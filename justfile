# What's a justfile? It's like makefile, but a joy to use. See https://github.com/casey/just

run:
    python3 -m prpr.main

test:
    python3 -m pytest --verbose

help:
    python3 -m prpr.main --help

black:
    black --line-length 119 .
