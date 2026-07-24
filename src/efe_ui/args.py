import argparse

ARGS = None


def get_args() -> argparse.Namespace:
    global ARGS
    if ARGS is None:
        ARGS = parse_args()
    return ARGS


def parse_args() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser(description="EFE-UI")
    arg_parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    arg_parser.add_argument(
        "-l",
        "--log",
        action="store_true",
        help="Enable device logs",
    )
    args = arg_parser.parse_known_args()
    return args[0]
