.PHONY: install format lint test task up down migrate

install:
	poetry install

format:
	poetry run format

lint:
	poetry run lint

test:
	poetry run test

task:
	poetry run task

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	poetry run alembic upgrade head
