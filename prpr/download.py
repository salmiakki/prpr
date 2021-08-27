from __future__ import annotations

import os
import re
import sys
import zipfile
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Iterable, Optional, Tuple

import requests
from loguru import logger
from pyfiglet import Figlet
from rich import print as rprint
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from prpr.homework import Homework

PAGE_LOAD_TIMEOUT = 60
DRIVER_TIMEOUT = 110
YOUR_DESCRIPTION_HERE = "your_description_here"

HISTORY_TAB_XPATH = "//article[text()='История']"
REVIEW_TAB_XPATH = "//article[text()='Код-ревью']"


class DownloadMode(Enum):
    ONE = auto()
    ALL = auto()
    # TODAY = auto() TODO: add customizable day end
    INTERACTIVE = auto()
    INTERACTIVE_ALL = auto()

    def __str__(self):
        return self.name.lower().replace("_", "-")

    def __repr__(self):
        return str(self)

    @staticmethod
    def from_string(mode: str) -> DownloadMode:
        try:
            return DownloadMode[mode.upper().replace("-", "_")]
        except KeyError:
            logger.error(f"Unexpected PostProcessMode mode: '{mode}' 😿")
            return mode


def download(homework: Homework, config, headless=False):
    logger.debug(homework)
    download_config = config.get("download", {})
    logger.debug(f"{download_config=}")

    homework_directory = _get_homework_directory(homework, download_config)

    driver = configure_driver(download_config, headless=headless)
    urls = get_zip_urls(driver, homework.revisor_url)

    logger.debug(f"Got {len(urls)} urls:")
    results = []
    for iteration, url in enumerate(urls, 1):
        logger.debug(f"{iteration}: {url}")
        results.append(_download_zip(url, homework_directory, iteration, homework))
    return results


class BatchDownloader:
    def __init__(self, config, headless=True):
        self.download_config = config.get("download", {})
        self.driver = configure_driver(self.download_config, headless=headless)
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def download_batch(self, homeworks: Iterable[Homework], print_banner=True):
        with self.driver as driver:
            for homework in homeworks:
                if print_banner:
                    _print_banner(homework)
                logger.info(f"Downloading {homework}...")
                homework_directory = _get_homework_directory(homework, self.download_config)
                urls = _get_zip_urls(driver, homework.revisor_url)
                logger.debug(f"Got {len(urls)} urls:")
                results = []
                for iteration, url in enumerate(urls, 1):
                    logger.debug(f"{iteration}: {url}")

                    results.append(_download_zip(url, homework_directory, iteration, homework))
                yield results


def _get_homework_directory(homework: Homework, download_config) -> Path:
    if not (root_directory := download_config.get("directory")):
        logger.error("Download directory not set in .prpr 😿")
        sys.exit(1)
    download_root = Path(root_directory).expanduser()
    course_directory = download_root / homework.course
    logger.debug(f"course = {homework.course}, course_directory = {course_directory}")
    if not course_directory.exists():
        logger.warning(f"{course_directory} doesn't exist, creating now...")
        course_directory.mkdir(parents=True)
    problem_directory = _get_problem_directory(homework, course_directory)
    homework_directory = problem_directory / _build_directory_name(homework)
    if not homework_directory.exists():
        logger.warning(f"{homework_directory} doesn't exist, creating now...")
        homework_directory.mkdir(parents=True)
    return homework_directory


def _get_problem_directory(homework: Homework, course_directory: Path) -> Path:
    problem_directory_name_prefix = f"hw_{homework.problem:02d}_"
    for p in course_directory.iterdir():
        if p.is_dir() and p.name.startswith(problem_directory_name_prefix):
            logger.debug(f"Found {p} for problem {homework.problem:02d} of {homework.course}.")
            problem_directory = p
            break
    else:
        course_directory / problem_directory_name_prefix
        problem_directory_name = f"{problem_directory_name_prefix}{YOUR_DESCRIPTION_HERE}"
        problem_directory = course_directory / problem_directory_name
        logger.warning(
            f"Directory for {homework.problem:02d} of {homework.course} is not found, "
            f"creating now ({problem_directory}; '{YOUR_DESCRIPTION_HERE}' can be replaced)..."
        )
        problem_directory.mkdir()
    return problem_directory


def _build_directory_name(hw: Homework) -> str:
    return f"{hw.issue_key_number}_{hw.second_name_slug}"


def _extract_filename(url: str) -> str:
    return url.rsplit("/")[-1]


def _download_zip(url: str, homework_directory: Path, iteration: int, homework: Homework) -> DownloadedResult:
    filename = _extract_filename(url)
    logger.debug(f"{url=} -> {filename=}")

    zip_full_path = homework_directory / filename
    if zip_full_path.exists():  # TODO: add force download
        logger.info(f"{str(zip_full_path)} exists, skipping.")
    else:
        r = requests.get(url, allow_redirects=True)  # TODO: add retries
        with open(zip_full_path, "wb") as f:
            f.write(r.content)
        logger.info(f"Written to {zip_full_path}.")
    iteration_directory, version_id = _unzip_homework_file(zip_full_path, iteration, homework)
    return DownloadedResult(
        zipfile=zip_full_path,
        iteration_directory=iteration_directory,
        iteration=iteration,
        homework_directory=homework_directory,
        id=version_id,
    )


def configure_driver(download_config, headless=False):
    logger.debug("Configuring Selenium driver...")
    browser_settings = download_config["browser"]
    browser_type = browser_settings["type"]
    logger.debug(f"Browser = {browser_type}, headless = {headless}.")
    mapping = {
        "firefox": _configure_firefox_driver,
    }
    if browser_type not in mapping:
        supported_browsers = sorted(mapping.keys())
        logger.error(f"download > browser > type is {browser_type}, only {supported_browsers} is supported 😿")
    return mapping[browser_type](browser_settings, headless=headless)


def _configure_firefox_driver(browser_settings, headless=False):
    profile_path = browser_settings["profile_path"]
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.headless = headless
    fp = webdriver.FirefoxProfile(profile_path)
    return webdriver.Firefox(fp, service_log_path=os.path.devnull, options=firefox_options)


def get_zip_urls(driver, revisor_url: str) -> list[str]:
    logger.debug(f"Fetching from {revisor_url}...")
    with driver:
        return _get_zip_urls(driver, revisor_url)


def _get_zip_urls(driver, revisor_url: str) -> list[str]:
    page_load_timeout = PAGE_LOAD_TIMEOUT
    driver.maximize_window()
    driver.set_page_load_timeout(page_load_timeout)
    driver.get(revisor_url)
    try:
        element = driver.find_element_by_xpath(HISTORY_TAB_XPATH)
    except NoSuchElementException:
        logger.debug(f"Element with XPath='{HISTORY_TAB_XPATH}' not found, trying XPath='{REVIEW_TAB_XPATH}'...")
        try:
            element = driver.find_element_by_xpath(REVIEW_TAB_XPATH)
        except NoSuchElementException:
            logger.error(
                f"Failed to find element with XPath='{REVIEW_TAB_XPATH}'. Are you logged in? Is the VPN connected?"
            )
            sys.exit(1)
    element.click()
    driver.implicitly_wait(DRIVER_TIMEOUT)
    return _extract_zip_urls(driver.page_source, revisor_url)


def _extract_zip_urls(page_source: str, revisor_url: str) -> Optional[str]:
    if ms := re.findall(r"\"homework_url\":\s?\"(?P<url>[\w\\\-\_:\u002F\.]+\.zip)\"", page_source):
        urls = {m.replace(r"\u002F", "/") for m in ms}
        return sorted(urls, key=_extract_version_id)
    logger.error("Failed to extract zip urls from {} 😿", revisor_url)
    return []


def _unzip_homework_file(homework_zip: Path, iteration: int, homework: Homework) -> Tuple[Path, str]:
    assert homework_zip.suffix == ".zip", f"Unexpected extension {homework_zip.suffix} for {homework_zip} 😿"
    homework_directory = homework_zip.parent
    version_id = _extract_version_id(homework_zip.name)
    iteration_directory = homework_directory / f"it_{iteration:02d}_{version_id}"
    if iteration_directory.exists():
        logger.info(f"Target {iteration_directory} exists")
    else:
        zipfile.ZipFile(homework_zip).extractall(path=iteration_directory)
        rprint(f"Fetched [bold]{iteration_directory.absolute()}[/bold] for [bold]{homework}[/bold].")
    return iteration_directory, version_id


def _extract_version_id(homework_zip_filename: str) -> str:
    if m := re.search(r".*?_(?P<id>\d+).zip", homework_zip_filename):
        group_dict = m.groupdict()
        logger.debug("{} {} {}", homework_zip_filename, group_dict, group_dict["id"])
        return group_dict["id"]


def _print_banner(homework):
    f = Figlet(font="slant")
    print(f.renderText(f"{homework.second_name_slug} {homework.problem}.{homework.iteration}"))
    print(homework.issue_url)


# TODO: add warnings for multiple versions for an iteration


@dataclass
class DownloadedResult:
    zipfile: Path
    iteration_directory: Path
    homework_directory: Path
    iteration: int
    id: str

    @property
    def zipfile_relative_to_homework_directory(self):
        return self.zipfile.relative_to(self.homework_directory)

    @property
    def iteration_directory_relative_to_homework_directory(self):
        return self.iteration_directory.relative_to(self.homework_directory)
