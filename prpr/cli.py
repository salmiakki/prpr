import argparse
import datetime as dt

from prpr.filters import Mode


def configure_arg_parser():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    filters = arg_parser.add_argument_group(
        "filters",
        "these allow to specify the subset of homeworks to be displayed, can be composed",
    )
    configure_filter_arguments(filters)

    arg_parser.add_argument("-o", "--open", action="store_true", default=False, help="open homework pages in browser")

    download_options = arg_parser.add_argument_group(
        "download",
    )
    configure_download_arguments(download_options)

    arg_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
    )
    return arg_parser


def configure_filter_arguments(filters):
    filters.add_argument(
        "-m",
        "--mode",
        type=Mode.from_string,
        choices=list(Mode),
        default=Mode.STANDARD,
        help="""filter mode
            standard: in review, open or on the side of user
            open: in review or open
            closed: resolved or closed
            closed-this-month: resolved or closed this "month" aka 💰.
            closed-previous-month: resolved or closed previous "month" aka 💰.
            all: all, duh""",
    )
    filters.add_argument(
        "-p",
        "--problems",
        type=int,
        nargs="+",
        help="the numbers of problems to be shown; multiple space-separated values are accepted",
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
    filters.add_argument(
        "-c",
        "--cohorts",
        nargs="+",
        help="cohorts to be shown; multiple space-separated values are accepted",
    )
    filters.add_argument(
        "-f",
        "--from-date",
        help="the start date (YYYY-MM-DD)",
        type=dt.date.fromisoformat,
    )
    filters.add_argument(
        "-t",
        "--to-date",
        help="the end date (YYYY-MM-DD)",
        type=dt.date.fromisoformat,
    )


def configure_download_arguments(download_options):
    download_options.add_argument(
        "-d",
        "--download",  # TODO: Add help messages when we have all the options we want
        action="store_true",
        default=False,
    )
    download_options.add_argument(
        "--head",
        help="download with visible browser window (default is headless, i.e. the window is hidden)",
        action="store_true",
        default=False,
    )
