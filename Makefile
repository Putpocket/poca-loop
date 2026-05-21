.PHONY: install migrate seed test dev

VENV ?= .venv
PYTHON ?= python3
PIP := $(VENV)/bin/pip
ALEMBIC := $(VENV)/bin/alembic
PYTEST := $(VENV)/bin/pytest
UVICORN := $(VENV)/bin/uvicorn

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

migrate:
	$(ALEMBIC) upgrade head

seed:
	$(VENV)/bin/python -m app.db.seed

test:
	$(PYTEST)

dev:
	$(UVICORN) app.main:app --reload
