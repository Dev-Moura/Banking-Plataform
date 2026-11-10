# Moura Banking Platform

Plataforma bancária educacional construída com **FastAPI**, **DDD**, **Clean Architecture** e **TDD**.

> Projeto exclusivamente educacional. Não processa dinheiro real, não se integra a instituições
> financeiras e não deve armazenar dados reais de clientes ou cartões.

## Stack

- Python 3.13+ · FastAPI · Pydantic v2
- SQLAlchemy 2 async · asyncpg · PostgreSQL · Alembic
- Redis · JWT · Argon2id
- Pytest · HTTPX · Ruff · Poetry
- Docker · Docker Compose

## Execução rápida

```bash
cp .env.example .env
docker compose up -d postgres redis
poetry install
poetry run alembic upgrade head
poetry run uvicorn banking.main:app --reload
```

Documentação interativa (desenvolvimento): <http://localhost:8000/docs>

## Comandos

```bash
poetry run format   # ruff format
poetry run lint     # ruff check
poetry run test     # pytest + cobertura
poetry run task     # pipeline completa
```

A documentação interna de estudo (`docs/`) é mantida localmente e não é versionada,
conforme a especificação do projeto.

## Aviso

Desenvolvido com **opencode** e revisado por **Michael Moura**.
Criado com amor com **FastAPI** &lt;3.
