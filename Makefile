.PHONY: install migrate seed test dev compose-config deploy-dev compose-down

VENV ?= .venv
PYTHON ?= python3
PIP := $(VENV)/bin/pip
ALEMBIC := $(VENV)/bin/alembic
PYTEST := $(VENV)/bin/pytest
UVICORN := $(VENV)/bin/uvicorn
DEPLOY_ENV ?= .env.deploy

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

$(DEPLOY_ENV):
	@cp .env.example $(DEPLOY_ENV)
	@sed -i "s#^SECRET_KEY=.*#SECRET_KEY=$$(openssl rand -hex 32)#" $(DEPLOY_ENV)
	@sed -i "s#^SEED_ADMIN_PASSWORD=.*#SEED_ADMIN_PASSWORD=dev-admin-$$(openssl rand -hex 12)#" $(DEPLOY_ENV)
	@echo "Created $(DEPLOY_ENV). Review it before exposing this service outside your LAN."

compose-config: $(DEPLOY_ENV)
	docker compose --env-file $(DEPLOY_ENV) config

deploy-dev: $(DEPLOY_ENV)
	docker compose --env-file $(DEPLOY_ENV) up --build -d

compose-down:
	docker compose --env-file $(DEPLOY_ENV) down
