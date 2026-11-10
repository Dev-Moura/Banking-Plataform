# Moura Banking Platform

Plataforma bancária educacional construída com **FastAPI**, **DDD**, **Clean Architecture** e **TDD**.

> Projeto exclusivamente educacional. Não processa dinheiro real, não se integra a instituições
> financeiras e não deve armazenar dados reais de clientes ou cartões.

## Stack

- Python 3.13+ · FastAPI · Pydantic v2
- SQLAlchemy 2 async · asyncpg · PostgreSQL · Alembic
- Redis · JWT (HS256) · Argon2id
- Pytest · HTTPX · Ruff · Poetry
- Docker · Docker Compose

## Arquitetura

Monólito modular com fronteiras por domínio. Cada módulo segue as camadas
`domain → application → infrastructure/presentation`, com dependências apontando para dentro.

```text
src/banking/
├── api/                  # agregação de roteadores, health checks e versionamento
├── core/                 # configuração, logging, middlewares e Problem Details
├── infrastructure/       # base SQLAlchemy, sessão assíncrona e Unit of Work
├── shared/               # contratos de segurança, paginação e value objects
└── modules/
    ├── identity/         # usuários, login, JWT, refresh rotation e RBAC
    ├── customer/         # cadastro de clientes
    ├── account/          # contas, saldo, status e extrato
    ├── transaction/      # transferências idempotentes
    ├── ledger/           # lançamentos contábeis imutáveis
    └── audit/            # modelo de auditoria (endpoints adiados)
```

## Funcionalidades implementadas

### Identidade e acesso

- Registro e login com e-mail normalizado e senha forte.
- Hash de senha com **Argon2id**.
- Access token **JWT HS256** com validação de `iss`, `aud` e `exp`.
- Refresh token opaco armazenado como hash SHA-256, com rotação e revogação da família em caso de reuso.
- Bloqueio temporário após tentativas de login inválidas.
- RBAC com os papéis `CUSTOMER`, `BANK_OPERATOR`, `BANK_ADMIN`, `AUDITOR` e `SYSTEM`.
- Rate limiting por Redis (desabilitado nos testes).

### Clientes e contas

- Cadastro de cliente vinculado ao usuário autenticado.
- Consulta e atualização cadastral com verificação de propriedade/RBAC.
- Abertura de contas com número gerado pela sequência `account_number_seq`.
- Consulta de contas, saldo e extrato.
- Bloqueio e encerramento de contas por operadores/administradores.

### Transferências e ledger

- Transferência atômica entre contas com validação de saldo, status, moeda e titularidade.
- Bloqueio de linhas em ordem determinística para evitar condições de corrida e deadlocks.
- **Idempotency-Key** obrigatória, com hash do payload para detectar reuso indevido.
- Registro de transação `COMPLETED` e de dois lançamentos contábeis (`DEBIT`/`CREDIT`).
- Saldo materializado nas contas e conciliação via `poetry run reconcile`.
- Lançamentos contábeis imutáveis garantidos por trigger no PostgreSQL.

## Segurança financeira

- Valores monetários usam `Decimal` e `NUMERIC(19,2)`; nunca `float`.
- Operações financeiras em transação ACID.
- Idempotência no endpoint de transferência.
- Controle de concorrência com `SELECT ... FOR UPDATE` em ordem determinística.
- Saldo negativo bloqueado para contas não sistêmicas.
- Erros padronizados em **Problem Details (RFC 9457)** com `correlation_id`.
- Respostas de autenticação sem vazamento de hash ou existência de usuário.

## Endpoints

Prefixo versionado: `/api/v1`.

| Método | Rota | Descrição |
| --- | --- | --- |
| POST | `/identity/register` | Registro de usuário |
| POST | `/identity/login` | Login e emissão de tokens |
| POST | `/identity/refresh` | Rotação de refresh token |
| POST | `/identity/logout` | Revogação de sessão |
| GET | `/identity/me` | Usuário autenticado |
| POST | `/customers` | Cadastro de cliente |
| GET | `/customers/me` | Meu cadastro |
| GET | `/customers/{customer_id}` | Consulta de cliente |
| PATCH | `/customers/{customer_id}` | Atualização cadastral |
| POST | `/accounts` | Abertura de conta |
| GET | `/accounts` | Listagem de contas |
| GET | `/accounts/{account_id}` | Consulta de conta |
| GET | `/accounts/{account_id}/balance` | Saldo |
| GET | `/accounts/{account_id}/statement` | Extrato contábil |
| PATCH | `/accounts/{account_id}/status` | Ativação/bloqueio/encerramento |
| POST | `/transactions/transfers` | Transferência idempotente |
| GET | `/transactions` | Histórico de transações |
| GET | `/transactions/{transaction_id}` | Consulta de transação |
| GET | `/ledger/accounts/{account_id}` | Lançamentos da conta |
| GET | `/ledger/transactions/{transaction_id}` | Lançamentos da transação |

Health checks: `GET /health/live` e `GET /health/ready`.

A transferência exige o cabeçalho `Idempotency-Key` (1 a 128 caracteres).
Replays com o mesmo payload retornam `200` com a transação original; reuso com payload
diferente retorna `409`.

## Execução local

Pré-requisitos: Python 3.13+, Poetry 2.x, Docker e Docker Compose.

```bash
cp .env.example .env
docker compose up -d postgres redis
poetry install
poetry run alembic upgrade head
poetry run uvicorn banking.main:app --reload
```

Documentação interativa: <http://localhost:8000/docs>

### Docker

```bash
docker compose up -d postgres redis
docker compose run --rm api alembic upgrade head
docker compose up -d api
```

## Testes

A suíte usa um banco isolado `banking_test`, criado automaticamente pelas fixtures,
com migrations aplicadas antes dos testes. O banco de desenvolvimento não é tocado.

```bash
poetry run format          # formatação
poetry run lint            # lint
poetry run test            # testes + cobertura
poetry run task            # pipeline completa (format check + lint + testes)
```

Marcadores disponíveis: `unit`, `integration`, `security`, `contract` e `e2e`.

Cenários cobertos incluem autenticação, rotação de refresh token, autorização por
propriedade, transferências concorrentes, replay de idempotência, equilíbrio do ledger
e imutabilidade dos lançamentos.

## Decisões de projeto

- **Monólito modular** em vez de microserviços: menor custo operacional e fronteiras claras,
  preservando a possibilidade de extração futura.
- **Saldo materializado + ledger**: leitura rápida de saldo com rastreabilidade contábil e
  reconciliação explícita.
- **Idempotência com hash do payload**: evita duplicidade por retry sem aceitar reuso indevido.
- **Bloqueio determinístico de contas**: reduz risco de deadlock em transferências concorrentes.
- **Ledger imutável**: correções devem ocorrer por lançamentos compensatórios.
- **Problem Details**: contrato de erro uniforme para clientes e observabilidade.

## Escopo adiado

As fases de evolução abaixo estão previstas na especificação, mas não foram implementadas:

- Kafka, Transactional Outbox, consumers, retries e DLQ (fase 5).
- Endpoints do módulo de auditoria (modelo e migration já existem) (fase 6).
- Métricas, tracing e dashboards de observabilidade (fase 6).
- Seed de demonstração financiado por conta sistêmica.
- Separação em microserviços (fase 8).

A documentação interna de estudo (`docs/`) é mantida localmente e não é versionada,
conforme a especificação do projeto.

## Aviso

Desenvolvido com **opencode** e revisado por **Michael Moura**.
Criado com amor com **FastAPI** &lt;3.
