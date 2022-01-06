#!/usr/bin/env bash

python3 -m venv python-env
source python-env/bin/activate

# Install python pip modules
pip3 install pip --upgrade
pip3 install setuptools --upgrade
pip3 install poetry
poetry install
