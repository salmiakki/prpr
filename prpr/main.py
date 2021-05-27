#!/usr/bin/env python3
from __future__ import annotations

import sys
import webbrowser

from loguru import logger

from prpr.cli import configure_arg_parser
from prpr.config import get_config
from prpr.filters import filter_homeworks
from prpr.homework import Homework
from prpr.startrack_client import get_startack_client
from prpr.table import DISPLAYED_TAIL_LENGTH, print_issue_table

COMPONENT_SUFFIXES = "component_suffixes"


def get_cohort(cohort, components, config):
    cohort = str(cohort)
    if not components:
        return cohort

    first_component = components[0]
    component_name = first_component.name
    suffix_mapper = config.get(COMPONENT_SUFFIXES, {})
    return cohort + suffix_mapper.get(component_name, component_name)


def sort_homeworks(homeworks: list[Homework]) -> list[Homework]:
    return sorted(homeworks, key=Homework.order_key)


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

    if args.open:
        open_pages(sorted_homeworks)


def open_pages(sorted_homeworks: list[Homework]) -> None:
    if sorted_homeworks:
        homework_to_open = sorted_homeworks[0]
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
