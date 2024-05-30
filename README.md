# Keelson Connector Lidar Ouster

Keelson connector for Ouster lidar´s


## How it works

1) Connects to Ouster lidar with Python SDK
2) Applying configuration and setting lidar in mode NORMAL
3) Listens on the continuous UDP stream of LidarScanPackets and IMU readsing
4) Publishing IMU, Scans and Configuration setup to Keelson
5) Queryable available to send configuration changes to unit 

## Quick start

Check device web server on devise IP address ex. [10.10.42.2](https://10.10.42.2) 

```bash
# Unit IP 10.10.42.2 and log level debug=10
python3 bin/main.py  -r rise -e landkrabba -s lidar/os2/0 --log-level 10 from_sensor --ouster-hostname 10.10.42.2
```

Tested units:

- OS2 Rev D

## Information sources

[Ouster Downloads & Manuals](https://ouster.com/downloads)

## Setup for development

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

