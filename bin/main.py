#!/usr/bin/env python3

"""
Command line utility tool for reading lidar data from an Ouster sensor or a pcap file and pushing to keelson
"""
import sys
import time
import json
import atexit
import logging
import argparse
import warnings
from contextlib import closing
from typing import cast, Iterator, Tuple, Optional, Dict

import zenoh
import numpy as np
from ouster.sdk import client
from ouster.sdk.client import _client
from ouster.sdk.client import ClientTimeout, Sensor, LidarPacket, ImuPacket, LidarScan

import keelson
from keelson.payloads.ImuReading_pb2 import ImuReading
from keelson.payloads.PointCloud_pb2 import PointCloud
from keelson.payloads.PackedElementField_pb2 import PackedElementField
from keelson.payloads.ConfigurationSensorPerception_pb2 import ConfigurationSensorPerception

from ouster.sdk import pcap

import terminal_inputs 

KEELSON_SUBJECT_POINT_CLOUD = "point_cloud"
KEELSON_SUBJECT_IMU_READING = "imu_reading"
KEELSON_SUBJECT_CONFIG = "configuration_perception_sensor"

# We subclass client.Scans and provide our own iterator interface
# This is necessary to extract both the LidarScans and the IMU packets from the same packet source
class LidarPacketAndIMUPacketScans(client.Scans):
    def __iter__(
        self,
    ) -> Iterator[Tuple[Optional[Dict[str, np.ndarray]], Optional[LidarScan]]]:
        """Get an iterator, returning a tuple where either the LidarScan or ImuData is None, indicating which type of
        packets is being returned."""

        w = self._source.metadata.format.columns_per_frame
        h = self._source.metadata.format.pixels_per_column
        columns_per_packet = self._source.metadata.format.columns_per_packet
        packets_per_frame = w // columns_per_packet
        column_window = self._source.metadata.format.column_window

        # If source is a sensor, make a type-specialized reference available
        sensor = (
            cast(Sensor, self._source) if isinstance(self._source, Sensor) else None
        )

        ls_write = None
        pf = _client.PacketFormat.from_info(self._source.metadata)
        batch = _client.ScanBatcher(w, pf)

        # Time from which to measure timeout
        start_ts = time.monotonic()

        it = iter(self._source)
        self._packets_consumed = 0
        self._scans_produced = 0
        while True:
            try:
                packet = next(it)
                self._packets_consumed += 1
            except StopIteration:
                if ls_write is not None:
                    if not self._complete or ls_write.complete(column_window):
                        yield None, ls_write
                return
            except ClientTimeout:
                self._timed_out = True
                return

            if self._timeout is not None and (
                time.monotonic() >= start_ts + self._timeout
            ):
                self._timed_out = True
                return

            if isinstance(packet, LidarPacket):
                ls_write = ls_write or LidarScan(h, w, self._fields, columns_per_packet)

                if batch(packet, ls_write):
                    # Got a new frame, return it and start another
                    if not self._complete or ls_write.complete(column_window):
                        yield None, ls_write
                        self._scans_produced += 1
                        start_ts = time.monotonic()
                    ls_write = None

                    # Drop data along frame boundaries to maintain _max_latency and
                    # clear out already-batched first packet of next frame
                    if self._max_latency and sensor is not None:
                        buf_frames = sensor.buf_use // packets_per_frame
                        drop_frames = buf_frames - self._max_latency + 1

                        if drop_frames > 0:
                            sensor.flush(drop_frames)
                            batch = _client.ScanBatcher(w, pf)

            elif isinstance(packet, ImuPacket):
                yield {
                    "acceleration": packet.accel,
                    "angular_velocity": packet.angular_vel,
                    "capture_timestamp": packet.capture_timestamp,
                }, None


def imu_data_to_imu_proto_payload(imu_data: dict):

    payload = ImuReading()

    payload.timestamp.FromNanoseconds(int(imu_data["capture_timestamp"] * 1e9))

    payload.linear_acceleration.x = imu_data["acceleration"][0]
    payload.linear_acceleration.y = imu_data["acceleration"][1]
    payload.linear_acceleration.z = imu_data["acceleration"][2]

    payload.angular_velocity.x = imu_data["angular_velocity"][0]
    payload.angular_velocity.y = imu_data["angular_velocity"][1]
    payload.angular_velocity.z = imu_data["angular_velocity"][2]

    return payload


def lidarscan_to_pointcloud_proto_payload(lidar_scan: LidarScan, xyz_lut: client.XYZLut, info, frame_id):

    logging.debug("Processing lidar scan with timestamp: %s", lidar_scan)

    payload = PointCloud()

    payload.timestamp.FromNanoseconds(int(lidar_scan.timestamp[0]))
    if frame_id is not None:
        payload.frame_id = frame_id

    # Destagger data
    xyz_destaggered = client.destagger(info, xyz_lut(lidar_scan))

    signal = client.destagger(info, lidar_scan.field(client.ChanField.SIGNAL))
    reflectivity = client.destagger(
        info, lidar_scan.field(client.ChanField.REFLECTIVITY)
    )
    near_ir = client.destagger(info, lidar_scan.field(client.ChanField.NEAR_IR))

    # Points as [[x, y, z, signal, reflectivity, near_ir], ...]
    points = np.concatenate(
        [
            xyz_destaggered,
            signal.reshape(list(signal.shape) + [1]),
            reflectivity.reshape(list(reflectivity.shape) + [1]),
            near_ir.reshape(list(near_ir.shape) + [1]),
        ],
        axis=-1,
    )

    points = xyz_destaggered.reshape(-1, points.shape[-1])

    # Zero relative position
    payload.pose.position.x = 0
    payload.pose.position.y = 0
    payload.pose.position.z = 0

    # Identity quaternion
    payload.pose.orientation.x = 0
    payload.pose.orientation.y = 0
    payload.pose.orientation.z = 0
    payload.pose.orientation.w = 1

    # Fields
    payload.fields.add(name="x", offset=0, type=PackedElementField.NumericType.FLOAT64)
    payload.fields.add(name="y", offset=8, type=PackedElementField.NumericType.FLOAT64)
    payload.fields.add(name="z", offset=16, type=PackedElementField.NumericType.FLOAT64)

    payload.fields.add(
        name="signal", offset=24, type=PackedElementField.NumericType.UINT16
    )
    payload.fields.add(
        name="reflectivity", offset=26, type=PackedElementField.NumericType.UINT16
    )
    payload.fields.add(
        name="near_ir", offset=28, type=PackedElementField.NumericType.UINT16
    )

    data = points.tobytes()
    payload.point_stride = len(data) // len(points)
    payload.data = data

    return payload


def from_sensor(session: zenoh.Session, args: argparse.Namespace):
    point_cloud_key = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject=KEELSON_SUBJECT_POINT_CLOUD,
        source_id=args.source_id,
    )

    imu_key = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject=KEELSON_SUBJECT_IMU_READING,
        source_id=args.source_id,
    )

    config_key = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject=KEELSON_SUBJECT_CONFIG,
        source_id=args.source_id,
    )

    logging.info("IMU key: %s", imu_key)
    logging.info("PointCloud key: %s", point_cloud_key)
    logging.info("Config key: %s", config_key)

    imu_publisher = session.declare_publisher(
        imu_key,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )

    point_cloud_publisher = session.declare_publisher(
        point_cloud_key,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )

    publisher_config = session.declare_publisher(
        config_key,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )
    
    
    logging.info("Connecting to Ouster sensor...")

    # Connect with the Ouster sensor and start processing lidar scans
    config = client.get_config(args.ouster_hostname)
    
    # TODO: send config data to keelson 
    logging.info("Sensor configuration: \n %s", type(config))
    logging.info("Sensor configuration: \n %s", json.dumps(str(config)))
    logging.info("Sensor configuration: \n %s", config)

    ingress_timestamp = time.time_ns()
    payload = ConfigurationSensorPerception()
    ConfigurationSensorPerception.SensorType.Value("LIDAR")
    ConfigurationSensorPerception.mode_operating.Value(config.operating_mode.name)
    payload.mode = config.lidar_mode
    payload.timestamp.FromNanoseconds(ingress_timestamp)
    payload.other_json = json.dumps(config)

    horizontal = (config.beam_azimuth_angles[0] - config.beam_azimuth_angles[1])/1000
    payload.view_horizontal_angel_deg = horizontal
    payload.view_vertical_angel_deg = config.beam_azimuth_angles

    logging.info("Sensor configuration: \n %s", payload)
    serialized_payload = payload.SerializeToString()
    envelope = keelson.enclose(serialized_payload)
    publisher_config.put()

    logging.info("Processing packages!")

    # Connecting to Ouster sensor
    with closing(
        LidarPacketAndIMUPacketScans.stream(
            args.ouster_hostname, config.udp_port_lidar, complete=True
        )
    ) as stream:
        # Create a look-up table to cartesian projection
        xyz_lut = client.XYZLut(stream.metadata)

        for imu_data, lidar_scan in stream:
            if imu_data is not None:
                payload = imu_data_to_imu_proto_payload(imu_data)

                serialized_payload = payload.SerializeToString()
                logging.debug("...serialized.")

                envelope = keelson.enclose(serialized_payload)
                imu_publisher.put(envelope)
                logging.info("...published IMU to zenoh!")

            if lidar_scan is not None:
                payload = lidarscan_to_pointcloud_proto_payload(
                    lidar_scan, xyz_lut, stream.metadata, args.frame_id
                )

                serialized_payload = payload.SerializeToString()
                envelope = keelson.enclose(serialized_payload)
                point_cloud_publisher.put(envelope)
                logging.info("...published to zenoh!")


def from_pcap(session: zenoh.Session, args: argparse.Namespace):
    point_cloud_key = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject=KEELSON_SUBJECT_POINT_CLOUD,
        source_id=args.source_id,
    )

    imu_key = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject=KEELSON_SUBJECT_IMU_READING,
        source_id=args.source_id,
    )

    logging.info("IMU key: %s", imu_key)
    logging.info("PointCloud key: %s", point_cloud_key)

    imu_publisher = session.declare_publisher(
        imu_key,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )

    point_cloud_publisher = session.declare_publisher(
        point_cloud_key,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )

    logging.info("Reading files...")

    with open(args.metadata_file, "r") as f:
        metadata = client.SensorInfo(f.read())
        logging.info("Read metadata from %s", args.metadata_file)

    pcap_source = pcap.Pcap(args.pcap_file, metadata)
    logging.info("Loaded pcap file: %s", args.pcap_file)

    scans = LidarPacketAndIMUPacketScans(source=pcap_source)
    logging.info("Created scans generator for %s", args.pcap_file)

    try:
        for imu_data, lidar_scan in scans:
            # TODO: We need to account for the timestamps and send the messages back in "real-time" not fast-time

            if imu_data is not None:
                payload = imu_data_to_imu_proto_payload(imu_data)

                serialized_payload = payload.SerializeToString()
                logging.debug("...serialized.")

                envelope = keelson.enclose(serialized_payload)
                logging.debug("...enclosed into envelope, serialized as: %s", envelope)

                imu_publisher.put(envelope)
                logging.info("...published to zenoh!")

            elif lidar_scan is not None:
                payload = lidarscan_to_pointcloud_proto_payload(lidar_scan, metadata)

                serialized_payload = payload.SerializeToString()
                logging.debug("...serialized.")
                envelope = keelson.enclose(serialized_payload)
                point_cloud_publisher.put(envelope)
                logging.info("...published to zenoh!")
                

    except ClientTimeout:
        logging.info("Timeout occurred while waiting for packets.")


if __name__ == "__main__":

    args = terminal_inputs.terminal_inputs()

    # Setup logger
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s", level=args.log_level
    )
    logging.captureWarnings(True)
    warnings.filterwarnings("once")

    ## Construct session
    logging.info("Opening Zenoh session...")
    conf = zenoh.Config()

    if args.connect is not None:
        conf.insert_json5(zenoh.config.CONNECT_KEY, json.dumps(args.connect))
    session = zenoh.open(conf)

    def _on_exit():
        session.close()

    atexit.register(_on_exit)

    # Dispatch to correct function
    try:
        args.func(session, args)
    except KeyboardInterrupt:
        logging.info("Program ended due to user request (Ctrl-C)")
        sys.exit(0)
