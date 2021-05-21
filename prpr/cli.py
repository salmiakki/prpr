import argparse

from prpr.filters import Mode


def configure_arg_parser():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    filters = arg_parser.add_argument_group(
        "filters",
        "these allow to specify the subset of homeworks to be displayed, can be composed",
    )
    filters.add_argument(
        "-m",
        "--mode",
        type=Mode.from_string,
        choices=list(Mode),
        default=Mode.DEFAULT,
        help="""filter by status mode
        default: in review, open or on the side of user
        open: in review or open
        closed: resolved or closed
        all: all, duh""",
    )
    filters.add_argument(
        "-p",
        "--projects",
        type=int,
        nargs="+",
        help="the numbers of projects to be shown; multiple space-separated values are accepted",
    )
    filters.add_argument(
        "-n",
        "--no",
        type=int,
        help="the no of the homework to be shown, all other filters are ignored",
    )
    filters.add_argument(
        "-s",
        "--student",
        help="the substring to be found in the student column, mail works best",
    )
    arg_parser.add_argument(
        "-o",
        "--open",
        action="store_true",
        default=False,
        help="Open the first homework in the list "
             "in two tabs of default browser: tracker and reviewer")
    arg_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
    )
    return arg_parser
