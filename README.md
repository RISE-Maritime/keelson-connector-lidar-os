# Keelson Connector Lidar Ouster 

Keelson connector for ouster lidar´s

TODO: update doc

Supported types:
- Sick picoScan150 Pro-1 (1134610)
- Sick multiScan136 (1131164)

## [Sick picoScan150 Pro-1 (1134610)](https://www.sick.com/ag/en/catalog/products/lidar-and-radar-sensors/lidar-sensors/picoscan100/picoscan150-pro-1/p/p677850?tab=detail)

### Features

- Light source: Infrared (905 nm)
- Horizontal: 276°
- Scanning frequency: 15 Hz, 20 Hz, 25 Hz, 30 Hz, 40 Hz & 50 Hz
- Angular resolution: 0.05°, 0.1°, 0.125°, 0.25°, 0.33° & 0.5°
- Scan field flatness: ± 1°
- Working range: 0.05 m --> 120 m
- Weight: 0.394 Kilograms

### Technical

- Supply voltage: 9-30V DC
- Power consumption: Typ. 4.5W max 17W
- Output current:	≤ 200 mA

### Performance

- Data output per scan segment: Segment size 30° at ≤ 25 Hz, Segment size 60° at ≥ 30 Hz
- Scan/frame rate: 12,546 measurement point/s ... 264,963 measurement point/s, Depends on the Dynamic Sensing Profile and number of echoes


[Dimensional drawing](https://www.sick.com/ag/en/catalog/products/lidar-and-radar-sensors/lidar-sensors/picoscan100/picoscan150-pro-1/p/p677850?tab=detail)

[Working range diagram](https://www.sick.com/ag/en/catalog/products/lidar-and-radar-sensors/lidar-sensors/picoscan100/picoscan150-pro-1/p/p677850?tab=detail)

[Operating Manual](https://cdn.sick.com/media/docs/1/91/691/operating_instructions_picoscan150_2d_lidar_sensors_en_im0106691.pdf)

### Device Configuration

Default Account: Service
Default Password: servicelevel

- IP: 10.10.30.2 (Open in web browser for Sick UI and config)
- Measurement output: 
  - Format: **Compact** | MSGPACK | MSGPACK
  - IP: 10.10.30.3
  - Port: 2115
- IMU output:
  - IP: 10.10.30.4
  - Port: 7503

### Scan Configuration

- 20Hz % 0.1°
- Range: 45m
- Sensitivity: Medium

Keelson processor for creating an realtime panorama image based on multiple camera sensors



# GIT REPOS

https://github.com/SICKAG/ScanSegmentDecoding

https://github.com/SICKAG/ScanSegmentAPI


https://github.com/SICKAG/sick_scan_rest_client 

## Quick start

```bash
python3 bin/main.py --log-level 10 -e boatswain --trigger-sub rise/v0/boatswain/pubsub/compressed_image/axis-1 --camera-query rise/v0/boatswain/pubsub/compressed_image/*
```



Setup for development environment on your own computer: 

1) Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - Docker desktop will provide you with an UI for monitoring and controlling docker containers and images along debugging 
   - If you want to learn more about docker and its building blocks of images and containers checkout [Docker quick hands-on in guide](https://docs.docker.com/guides/get-started/)
2) Start up of **Zenoh router** either in your computer or any other computer within your local network 

   ```bash
    # Navigate to folder containing docker-compose.zenoh-router.yml
  
    # Start router with log output 
    docker-compose -f containing docker-compose.zenoh-router.yml up 

    # If no obvious errors, stop container "ctrl-c"

    # Start container and let it run in the background/detached (append -d) 
    docker-compose -f containing docker-compose.zenoh-router.yml up -d
   ```

    [Link to --> docker-compose.zenoh-router.yml](docker-compose.zenoh-router.yml)

1) Now the Zenoh router is hopefully running in the background and should be available on localhost:8000. This can be example tested with [Zenoh Rest API ](https://zenoh.io/docs/apis/rest/) or continue to next step running Python API
2) Set up python virtual environment  `python >= 3.11`
   1) Install package `pip install -r requirements.txt`
3)  Now you are ready to explore some example scripts in the [exploration folder](./exploration/) 
    1)  Sample are coming from:
         -   [Zenoh Python API ](https://zenoh-python.readthedocs.io/en/0.10.1-rc/#quick-start-examples)


[Zenoh CLI for debugging and problem solving](https://github.com/RISE-Maritime/zenoh-cli)

