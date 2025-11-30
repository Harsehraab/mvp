"""Simple SQLite-backed banking transactions helper.

Provides minimal functions to initialize a DB, add transactions, query transactions
and compute balances. Designed for use by the Crew orchestration and the MCP
server.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Tuple


DEFAULT_DB_FILENAME = "long_term_memory_storage.db"


def get_db_path(storage_dir: Optional[str] = None) -> str:
    if storage_dir:
        os.makedirs(storage_dir, exist_ok=True)
        return os.path.join(storage_dir, DEFAULT_DB_FILENAME)
    # fallback to current directory
    return os.path.abspath(DEFAULT_DB_FILENAME)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    """Create the transactions table if it doesn't exist."""
    conn = _connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            timestamp TEXT NOT NULL
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_account ON transactions(account_id)")
    conn.commit()
    conn.close()


def add_transaction(db_path: str, account_id: str, amount: float, type: str, description: Optional[str] = None, timestamp: Optional[str] = None) -> int:
    """Insert a transaction. Returns the inserted row id."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    conn = _connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (account_id, amount, type, description, timestamp) VALUES (?, ?, ?, ?, ?)",
        (account_id, float(amount), type, description, timestamp),
    )
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid


def get_transactions(db_path: str, account_id: Optional[str] = None, limit: int = 100, since: Optional[str] = None) -> List[dict]:
    conn = _connect(db_path)
    cur = conn.cursor()
    q = "SELECT * FROM transactions"
    params: Tuple = ()
    clauses: List[str] = []
    if account_id:
        clauses.append("account_id = ?")
        params = params + (account_id,)
    if since:
        clauses.append("timestamp >= ?")
        params = params + (since,)
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY timestamp DESC LIMIT ?"
    params = params + (limit,)
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_balance(db_path: str, account_id: str) -> float:
    conn = _connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) as balance FROM transactions WHERE account_id = ?", (account_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return 0.0
    return float(row["balance"] or 0.0)


__all__ = ["get_db_path", "init_db", "add_transaction", "get_transactions", "get_balance"]
