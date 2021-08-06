#!/usr/bin/env python3
from __future__ import annotations

import sys
import webbrowser

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


def get_cohort(cohort, components, config):
    cohort = str(cohort) if cohort else "?"
    if not components:
        return cohort

    first_component = components[0]
    component_name = first_component.name
    suffix_mapper = config.get(COMPONENT_SUFFIXES, {})
    return cohort + suffix_mapper.get(component_name, "")


def sort_homeworks(homeworks: list[Homework]) -> list[Homework]:
    return sorted(homeworks, key=Homework.order_key)


def choose_to_download(to_download: list[Homework]) -> list[Homework]:
    if not to_download:
        return []
    if len(to_download) == 1:
        logger.debug("Just one homework to be choose from, choosing it.")
        return to_download
    hw_strings = [str(hw) for hw in to_download]
    chosen_title = questionary.select(
        "Which homework do you want to download?",
        choices=hw_strings,
    ).ask()
    return [hw for hw in to_download if str(hw) == chosen_title]


def main():
    arg_parser = configure_arg_parser()
    args = arg_parser.parse_args()

    configure_logger(args.verbose)
    logger.debug(f"{args=}")

    config = get_config()
    client = get_startack_client(config)

    issues = client.get_issues()
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
            first=issue.previousStatus is None,
            course=extract_course(issue),
            transitions=client.get_status_history(issue.key, issue.status.key),
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
    print_issue_table(sorted_homeworks, last=DISPLAYED_TAIL_LENGTH)

    if not args.download and args.open:
        open_pages_for_first(sorted_homeworks)

    logger.debug("args.download = {}", args.download)

    if args.download:
        if to_download := [hw for hw in sorted_homeworks if hw.open_or_in_review]:
            if args.interactive:
                logger.warning("--interactive is deprecated and to be removed, use `--download interactive` instead.")
                to_download = choose_to_download(to_download)
            elif args.download == DownloadMode.ALL:
                pass
            elif args.download == DownloadMode.ONE:
                to_download = to_download[:1]
            elif args.download == DownloadMode.INTERACTIVE:
                # TODO: deprecate --interactive
                to_download = choose_to_download(to_download)
            else:
                raise ValueError(f"Unexpected download mode: {args.download} 😿")
            logger.info("Downloading {} homeworks...", len(to_download))
            with BatchDownloader(config, headless=not args.head) as downloader:
                for results, homework in zip(downloader.download_batch(to_download), to_download):
                    if args.post_process and results:
                        logger.info(f"Post-processing {homework}...")
                        post_process_homework(results, homework, config=config)
                    if args.open:
                        _open_pages_for_homework(homework)
        else:
            logger.warning("There's nothing to download. Consider relaxing the filters if that's not what you expect.")
    else:
        if args.post_process:
            logger.warning("{} is ignored without {} at the moment.", POST_PROCESS, DOWNLOAD)
        if args.interactive:
            logger.warning("{} is ignored without {} at the moment", INTERACTIVE, DOWNLOAD)


def extract_course(issue):
    if components := issue.components:
        return components[0].name
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
