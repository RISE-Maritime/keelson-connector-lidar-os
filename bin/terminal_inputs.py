import argparse
from main import from_sensor, from_pcap


def terminal_inputs():
    """Parse the terminal inputs and return the arguments"""

    parser = argparse.ArgumentParser(
        prog="ouster",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--log-level",
        type=int,
        default=30,
        help="Log level 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL 0=NOTSET",
    )

    parser.add_argument(
        "--connect",
        action="append",
        type=str,
        help="Endpoints to connect to, in case of struggeling to find router. ex. tcp/localhost:7447",
    )

    parser.add_argument(
        "-r",
        "--realm",
        default="rise",
        type=str,
        help="Unique id for a realm/domain to connect ex. rise",
    )

    parser.add_argument(
        "-e",
        "--entity-id",
        type=str,
        required=True,
        help="Entity being a unique id representing an entity within the realm ex, landkrabban",
    )

    parser.add_argument(
        "-s",
        "--source-id",
        type=str,
        required=True,
        help="Lidar source id ex. ouster/os1/0",
    )

    parser.add_argument(
        "-f", "--frame-id", type=str, default=None, help="Frame id for foxglow"
    )

    ## Subcommands
    subparsers = parser.add_subparsers(required=True)

    ## from_sensor subcommand
    from_sensor_parser = subparsers.add_parser("from_sensor")

    from_sensor_parser.add_argument("-o", "--ouster-hostname", type=str, required=True)

    from_sensor_parser.add_argument(
        "--view-angle-deg-start",
        type=int,
        required=True,
        default=0,
        help="Start angle in degrees from 0 to 360, needs to be smaller then end angle",
    )

    from_sensor_parser.add_argument(
        "--view-angle-deg-end",
        type=int,
        required=True,
        default=360,
        help="Start angle in degrees from 0 to 360, needs to be larger then start angle",
    )

    from_sensor_parser.add_argument(
        "--lidar-mode",
        type=str,
        default="1024x10",
        choices=["512x10", "512x20", "1024x10", "1024x20", "2048x10", "4096x5"],
        required=True,
        help="Lidar mode scan (columns(x)frequency)",
    )

    from_sensor_parser.set_defaults(func=from_sensor)

    ## from_pcap subcommand
    from_pcap_parser = subparsers.add_parser("from_pcap")
    from_pcap_parser.add_argument("-p", "--pcap-file", type=str, required=True)
    from_pcap_parser.add_argument("-m", "--metadata-file", type=str, required=True)
    from_pcap_parser.set_defaults(func=from_pcap)

    ## Parse arguments and start doing our thing
    args = parser.parse_args()

    return args
