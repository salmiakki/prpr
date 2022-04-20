import pytest

from prpr.filters import filter_homeworks, FilterMode
from prpr.homework import Homework


@pytest.fixture()
def homeworks():
    return [
        Homework(
            "PCR-12345",
            "[1] Даниил Хармс (STudent@yandex.ru)",
            "1",
            "open",
            "2021-05-11T02:13:00.000+0000",
            "",
            1,
            "backend-developer",
        ),
    ]


@pytest.mark.parametrize("search_string,count", (
    ("student", 1),
    ("STUDENT", 1),
    ("Student", 1),
    ("anybody", 0),
    ("Хармс", 1),
    ("хармс", 1),
    ("ХАРМС", 1),
    ("Медведев", 0),
))
def test_students_search(search_string, count, homeworks):

    result = filter_homeworks(homeworks, mode=FilterMode.ALL, config={}, student=search_string)
    assert len(result) == count
