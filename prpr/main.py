#!/usr/bin/env python3
from __future__ import annotations

import sys
import webbrowser
from enum import Enum
from typing import Union

import questionary
from loguru import logger

from prpr.cli import DOWNLOAD, INTERACTIVE, POST_PROCESS, configure_arg_parser
from prpr.config import get_config
from prpr.download import BatchDownloader, DownloadMode
from prpr.filters import filter_homeworks
from prpr.homework import Homework
from prpr.post_process import post_process_homework
from prpr.startrack_client import get_startack_client
from prpr.table import DISPLAYED_TAIL_LENGTH, print_issue_table

COMPONENT_SUFFIXES = "component_suffixes"
_components_cache = {}


class InteractiveCommand(Enum):
    CHECK_AGAIN = "🔁 Check again"


def get_cohort(cohort, components, config):
    cohort = str(cohort) if cohort else "?"
    if not components:
        return cohort

    first_component = components[0]

    if first_component.id not in _components_cache:
        _components_cache[first_component.id] = first_component.name
    component_name = _components_cache[first_component.id]

    suffix_mapper = config.get(COMPONENT_SUFFIXES, {})
    return cohort + suffix_mapper.get(component_name, "")


def sort_homeworks(homeworks: list[Homework]) -> list[Homework]:
    return sorted(homeworks, key=Homework.order_key)


def choose_to_download(to_download: list[Homework]) -> Union[list[Homework], InteractiveCommand]:
    if not to_download:
        return []
    if len(to_download) == 1:
        logger.debug("Just one homework to be choose from, choosing it.")
        return to_download
    hw_strings = [str(hw) for hw in to_download]
    check_again_string = InteractiveCommand.CHECK_AGAIN.value
    chosen_title = questionary.select(
        "Which homework do you want to download?",
        choices=hw_strings + [check_again_string],
    ).ask()
    if chosen_title == check_again_string:
        return InteractiveCommand.CHECK_AGAIN
    return [hw for hw in to_download if str(hw) == chosen_title]


def main():
    arg_parser = configure_arg_parser()
    args = arg_parser.parse_args()

    configure_logger(args.verbose)
    logger.debug(f"{args=}")

    config = get_config()
    client = get_startack_client(config)

    user = args.user
    work_owner = f"{user}'s" if user else "My"
    if args.free:
        if user:
            logger.warning("Requested free tickets list, user parameter ignored")
        user = config["free_work_owner"]
        work_owner = "Free"
    table_title = f"{work_owner} Praktikum Review Tickets"

    should_run = True
    last_processed = None
    while should_run:
        issues = client.get_issues(user=user)
        logger.debug(f"Got {len(issues)} homeworks.")
        homeworks = [
            Homework(
                issue_key=issue.key,
                summary=issue.summary,
                cohort=get_cohort(issue.cohort, issue.components, config),
                status=issue.status.key,
                status_updated=issue.statusStartTime,
                description=issue.description,
                number=number,
                course=extract_course(issue),
                transitions=client.get_status_history(issue),
            )
            for number, issue in enumerate(issues, 1)
        ]
        filtered_homeworks = filter_homeworks(
            homeworks,
            mode=args.mode,
            config=config,
            problems=args.problems,
            no=args.no,
            student=args.student,
            cohorts=args.cohorts,
            from_date=args.from_date,
            to_date=args.to_date,
        )
        sorted_homeworks = sort_homeworks(filtered_homeworks)
        print_issue_table(
            sorted_homeworks, last=DISPLAYED_TAIL_LENGTH, last_processed=last_processed, title=table_title,
        )
        if not args.download and args.open:
            open_pages_for_first(sorted_homeworks)
        if not args.download:
            if args.post_process:
                logger.warning("{} is ignored without {} at the moment.", POST_PROCESS, DOWNLOAD)
            if args.interactive:
                logger.warning("{} is ignored without {} at the moment", INTERACTIVE, DOWNLOAD)
            should_run = False
        else:
            if open_or_in_review := [hw for hw in sorted_homeworks if hw.open_or_in_review]:
                if args.interactive:
                    logger.warning(
                        "--interactive is deprecated and to be removed, use `--download interactive` instead."
                    )
                    to_download = choose_to_download(open_or_in_review)
                    if to_download == InteractiveCommand.CHECK_AGAIN:
                        should_run = args.download
                        continue
                    if to_download:
                        assert len(to_download) == 1
                        last_processed = to_download[0]
                elif args.download == DownloadMode.ALL:
                    to_download = open_or_in_review
                elif args.download == DownloadMode.ONE:
                    to_download = open_or_in_review[:1]
                elif args.download == DownloadMode.INTERACTIVE or args.download == DownloadMode.INTERACTIVE_ALL:
                    # TODO: deprecate --interactive
                    to_download = choose_to_download(open_or_in_review)
                    if to_download == InteractiveCommand.CHECK_AGAIN:
                        should_run = True
                        continue
                    if to_download:
                        last_processed = to_download[0]
                else:
                    raise ValueError(f"Unexpected download mode: {args.download} 😿")
                if not to_download:
                    logger.warning("Nothing to download.")
                    should_run = False
                    continue
                hw_noun = "homeworks" if len(to_download) > 1 else "homework"
                logger.info("Downloading {} {}...", len(to_download), hw_noun)
                with BatchDownloader(config, headless=not args.head) as downloader:
                    print_banner = len(open_or_in_review) > 1 and args.download in {
                        DownloadMode.ALL,
                        DownloadMode.INTERACTIVE_ALL,
                    }
                    for results, homework in zip(
                        downloader.download_batch(to_download, print_banner=print_banner),
                        to_download,
                    ):
                        if args.post_process and results:
                            logger.info(f"Post-processing {homework}...")
                            post_process_homework(results, homework, config=config)
                        if args.open:
                            _open_pages_for_homework(homework)
                should_run = args.download == DownloadMode.INTERACTIVE_ALL and len(open_or_in_review) >= 2
            else:
                logger.warning(
                    "There's nothing to download. Consider relaxing the filters if that's not what you expect."
                )
                should_run = False
                continue


def extract_course(issue):
    if components := issue.components:
        component = components[0]
        if component.id not in _components_cache:
            _components_cache[component.id] = component.name
        return _components_cache[component.id]
    logger.warning(f"{issue.key} doesn't have components 😿")
    return "unknown_course"


def open_pages_for_first(sorted_homeworks: list[Homework]) -> None:
    if sorted_homeworks:
        homework_to_open = sorted_homeworks[0]
        _open_pages_for_homework(homework_to_open)


def _open_pages_for_homework(homework_to_open):
    startrek_url = homework_to_open.issue_url
    logger.info(f"Opening {startrek_url} ...")
    webbrowser.open(startrek_url)
    if revisor_url := homework_to_open.revisor_url:
        logger.info(f"Opening {revisor_url} ...")
        webbrowser.open(revisor_url)
        if homework_to_open.iteration and homework_to_open.iteration > 1:
            webbrowser.open(revisor_url)


def configure_logger(verbose):
    if verbose == 2:  # -vv
        return
    logger.remove()
    if verbose == 1:  # -v
        logger.add(sys.stderr, level="INFO")
    elif not verbose:
        logger.add(sys.stderr, level="WARNING")


if __name__ == "__main__":
    main()
