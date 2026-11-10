"""Reconciliação entre saldo materializado e lançamentos do ledger."""

from __future__ import annotations

import asyncio

from sqlalchemy import text

from banking.infrastructure.database.session import get_engine


async def _reconcile() -> int:
    query = text(
        """
        SELECT a.id,
               a.balance,
               COALESCE(SUM(CASE le.entry_type
                                WHEN 'CREDIT' THEN le.amount
                                WHEN 'DEBIT' THEN -le.amount
                            END), 0) AS ledger_balance
        FROM accounts a
        LEFT JOIN ledger_entries le ON le.account_id = a.id
        GROUP BY a.id, a.balance
        HAVING a.balance <> COALESCE(SUM(CASE le.entry_type
                                WHEN 'CREDIT' THEN le.amount
                                WHEN 'DEBIT' THEN -le.amount
                            END), 0)
        """
    )
    async with get_engine().connect() as connection:
        result = await connection.execute(query)
        rows = result.fetchall()

    if not rows:
        print("Reconciliação OK: todos os saldos conferem com o ledger.")
        return 0

    print(f"Reconciliação FALHOU: {len(rows)} conta(s) divergente(s).")
    for row in rows:
        print(f"  conta={row.id} saldo={row.balance} ledger={row.ledger_balance}")
    return 1


def main() -> int:
    """Executa a reconciliação e retorna código de saída."""
    return asyncio.run(_reconcile())


if __name__ == "__main__":
    raise SystemExit(main())
