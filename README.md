# NLP Topic Builder Local Deployment Developer Guide

## Python Environment

- Install `python 3.12.0` and activate virtual environment by running `python -m venv venv` and `source venv/bin/activate`.

- Install python packages by running command: `pip install .`. It will install all dependencies from `pyproject.toml` file.

## Pull Docker Images

- First comment out `nlpui` service in `docker-compose.yml` file.

- 