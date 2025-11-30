import os
import tempfile

from crew_ai.transactions import init_db, add_transaction, get_transactions, get_balance


def test_transactions_basic(tmp_path):
    db_file = tmp_path / "test_txn.db"
    db_path = str(db_file)
    init_db(db_path)
    add_transaction(db_path, "acct1", 100.0, "credit", "initial deposit")
    add_transaction(db_path, "acct1", -25.5, "debit", "purchase")
    txs = get_transactions(db_path, account_id="acct1", limit=10)
    assert len(txs) == 2
    bal = get_balance(db_path, "acct1")
    assert abs(bal - 74.5) < 1e-6
