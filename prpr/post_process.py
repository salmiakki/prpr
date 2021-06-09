import subprocess
from typing import Union

from loguru import logger

from prpr.download import DownloadedResult
from prpr.homework import Homework

DEFAULT = "default"
PROCESS = "process"
RUNNER = "runner"
COURSES = "courses"
PROBLEMS = "problems"


def post_process_homework(
    results: list[DownloadedResult], homework: Homework = None, config=None, print_step_output=True
):
    if not (process_config := config.get(PROCESS, {})):
        logger.error("Aaaaa")  # TODO
        return
    runner = process_config.get(RUNNER, ["bash", "-c"])
    if default_processing := process_config.get(DEFAULT, {}):
        run_steps(default_processing, runner, results, DEFAULT, print_step_output)
    if homework and (course_config := process_config.get(COURSES, {}).get(homework.course)):
        default_course_processing = course_config.get(DEFAULT, {})
        run_steps(default_course_processing, runner, results, f"{homework.course}.{DEFAULT}", print_step_output)
        if problem_processing := course_config.get(PROBLEMS, {}).get(pr := homework.problem):
            run_steps(problem_processing, runner, results, f"{homework.course}.{PROBLEMS}.{pr}", print_step_output)


def run_steps(steps_batch, runner, results, steps_batch_name, print_step_output):
    logger.info("Running steps from {}...", steps_batch_name)
    for step_name, command_template in steps_batch["steps"].items():
        result_last = results[-1]
        command = _interpolate(command_template, result_last)
        if diff := any(
            key in command_template for key in {"{it_prev}", "{it_prev_}", "{it_prev_zip}", "{it_prev_zip_}"}
        ):
            if len(results) >= 2:
                result_prev = results[-2]
                command = _interpolate_previous(command, result_prev)
            else:
                logger.info(f"Skipping {step_name} for first iteration.")
                continue
        else:
            result_prev = None
        logger.info(f"Running {step_name}...")
        logger.debug(f"{step_name}: {command}")
        step_process = subprocess.run(
            runner + [command],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            text=True,
        )
        if print_step_output:
            print(step_process.stdout)
        _save_step_output_to_file(diff, result_last, result_prev, step_name, step_process)


def _save_step_output_to_file(
    diff,
    last: DownloadedResult,
    prev: DownloadedResult,
    step_name: str,
    step_process: Union[subprocess.CompletedProcess, subprocess.CompletedProcess[str]],
) -> None:
    if diff:
        filename = f"{prev.iteration}_vs_{last.iteration}_{prev.id}_{last.id}_{step_name}.log"
    else:
        filename = f"{last.iteration}_{last.id}_{step_name}.log"
    output_path = last.homework_directory / filename
    logger.debug("Writing results of {} to {}...", step_name, output_path)
    with open(output_path, "w") as f:
        f.write(step_process.stdout)


def _interpolate(command_template: str, result_last: DownloadedResult) -> str:
    return _translate(
        command_template,
        {
            "{hw}": str(result_last.homework_directory),
            "{it_last}": str(result_last.iteration_directory),
            "{it_last_}": str(result_last.iteration_directory_relative_to_homework_directory),
            "{it_last_zip}": str(result_last.zipfile),
            "{it_last_zip_}": str(result_last.zipfile_relative_to_homework_directory),
        },
    )


def _interpolate_previous(command: str, result_prev: DownloadedResult) -> str:
    return _translate(
        command,
        {
            "{it_prev}": str(result_prev.iteration_directory),
            "{it_prev_}": str(result_prev.iteration_directory_relative_to_homework_directory),
            "{it_prev_zip}": str(result_prev.zipfile),
            "{it_prev_zip_}": str(result_prev.zipfile_relative_to_homework_directory),
        },
    )


def _translate(string, dictionary):
    for key, translation in dictionary.items():
        string = string.replace(key, translation)
    return string
