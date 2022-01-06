#!/usr/bin/env bash

source python-env/bin/activate

export PYTHONPATH="${PYTHONPATH}:/workdir"

# application to run
# sleep 30
poetry run python3 "${SCRIPT}"