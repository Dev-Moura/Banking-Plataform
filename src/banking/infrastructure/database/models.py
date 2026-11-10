"""Agrega todos os modelos ORM para o metadata do Alembic."""

from __future__ import annotations

from banking.infrastructure.database.base import Base
from banking.modules.account.infrastructure.persistence import models as account_models
from banking.modules.audit.infrastructure.persistence import models as audit_models
from banking.modules.customer.infrastructure.persistence import (
    models as customer_models,
)
from banking.modules.identity.infrastructure.persistence import (
    models as identity_models,
)
from banking.modules.ledger.infrastructure.persistence import models as ledger_models
from banking.modules.transaction.infrastructure.persistence import (
    models as transaction_models,
)

__all__ = [
    "Base",
    "account_models",
    "audit_models",
    "customer_models",
    "identity_models",
    "ledger_models",
    "transaction_models",
]
