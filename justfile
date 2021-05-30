# What's a justfile? It's like makefile, but a joy to use. See https://github.com/casey/just

verbose:
    python3 -m prpr.main --verbose

run:
    python3 -m prpr.main

all:
    python3 -m prpr.main --mode all

open:
    python3 -m prpr.main --verbose --open

month:
    python3 -m prpr.main --mode closed-this-month --verbose

final:
    python3 -m prpr.main --mode all --pr 15

test:
    python3 -m pytest --verbose

help:
    python3 -m prpr.main --help

black:
    black --line-length 119 .

mypy:
    mypy .

precommit:
    pre-commit run --all-files

down:
    python3 -m prpr.main --down --verbose
    tree /Users/leshapak/Yandex.Disk.localized/_praktikum/prpr2/downloaded
