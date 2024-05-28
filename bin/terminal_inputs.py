import argparse


def terminal_inputs():
    """Parse the terminal inputs and return the arguments"""

    parser = argparse.ArgumentParser(
        prog="seaman",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-l",
        "--log-level",
        type=int,
        default=30,
        help="Log level 10=DEBUG, 20=INFO, 30=WARN, 40=ERROR, 50=CRITICAL 0=NOTSET",
    )
    parser.add_argument(
        "--connect",
        action="append",
        type=str,
        help="Endpoints to connect to, in case multicast is not working.",
    )
    parser.add_argument(
        "-r",
        "--realm",
        default="rise",
        type=str,
        help="Unique id for a domain/realm to connect ex. rise",
    )
    parser.add_argument(
        "-e",
        "--entity-id",
        type=str,
        help="Entity being a unique id representing an entity within the realm ex, landkrabba",
    )

    parser.add_argument(
        "-oi",
        "--output-id",
        default="0",
        type=str,
        help="Unique output key id (default 0)",
    )


    # Process starter 1
    parser.add_argument(
        "-ts",
        "--trigger-sub",
        type=str,
        help="Trigger Key subscribe to an camera that is triggers the panorama image generation",
    )

    # Process starter 2
    parser.add_argument(
        "-th",
        "--trigger-hz",
        type=int,
        help="Trigger panorama image generation with fixed hz",
    )


    parser.add_argument(
        "-cq",
        "--camera-query",
        type=str,
        help="Key expression to query cameras",
    )



    ## Parse arguments and start doing our thing
    args = parser.parse_args()

    return args
