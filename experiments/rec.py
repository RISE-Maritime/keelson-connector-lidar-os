from more_itertools import time_limited
from ouster.sdk import client
from contextlib import closing
from datetime import datetime
from ouster.sdk import pcap



# connect to sensor and record lidar/imu packets
config = client.SensorConfig()
config.udp_port_lidar = 7502
config.udp_port_imu = 7503
with closing(client.SensorPacketSource([("10.10.42.2", config)],
                            timeout=10).single_source(0)) as source:

    # make a descriptive filename for metadata/pcap files
    time_part = datetime.now().strftime("%Y%m%d_%H%M%S")
    meta = source.metadata
    fname_base = f"{meta.prod_line}_{meta.sn}_{meta.config.lidar_mode}_{time_part}"

    print(f"Saving sensor metadata to: {fname_base}.json")
    with open(f"{fname_base}.json", "w") as f:
        f.write(source.metadata.to_json_string())

    print(f"Writing to: {fname_base}.pcap (Ctrl-C to stop early)")
    source_it = time_limited(60, source)
    n_packets = pcap.record(source_it, f"{fname_base}.pcap")

    print(f"Captured {n_packets} packets")