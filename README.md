# protoactor-python
Proto Actor - Ultra fast distributed actors

# Getting Started

Ensure you have Python 2.7 with pip installed.

```
$ pip install virtualenv
$ virtualenv dev.venv
$ source dev.venv/bin/activate # on POSIX systems
$ .\dev.venv\Scripts\activate.ps1 # on Windows
$ pip install -r requirements.dev.txt
```

## Run mypy
mypy --python-version 3.6 --fast-parser -p protoactor

## Run tests

```
$ tox
```
