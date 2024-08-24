#!/bin/sh

# this assumes Poetry is installed and in the Path, see https://python-poetry.org/docs/#installing-with-the-official-installer
# on macos run with `source ./setup_dev.sh`
poetry install
poetry run pre-commit install
poetry run pre-commit autoupdate
