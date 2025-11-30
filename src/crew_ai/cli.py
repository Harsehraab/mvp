"""CLI for Crew AI orchestration utilities (transactions + MCP server).

Provides commands to add/list transactions and to start a minimal MCP HTTP endpoint.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

import click

from .transactions import get_db_path, init_db, add_transaction, get_transactions, get_balance
from .mcp_server import start_mcp_server


def _project_storage(project: Optional[str]) -> str:
    env = os.environ.get("CREWAI_STORAGE_DIR")
    if env:
        base = env
    else:
        # default per-user location (simple fallback)
        base = os.path.expanduser("~/.local/share/CrewAI")
    if project:
        path = os.path.join(base, project)
    else:
        path = os.path.join(base, "default")
    os.makedirs(path, exist_ok=True)
    return path


@click.group()
def cli():
    """Crew AI utilities CLI."""
    pass


@cli.command("txn-add")
@click.option("--project", default="default", help="project name for storage dir")
@click.option("--account", required=True, help="account id")
@click.option("--amount", required=True, type=float, help="transaction amount (positive credit, negative debit)")
@click.option("--type", "ttype", default="credit", help="transaction type")
@click.option("--description", default=None, help="optional description")
def txn_add(project: str, account: str, amount: float, ttype: str, description: Optional[str]):
    """Add a transaction to the project's SQLite DB."""
    storage = _project_storage(project)
    db_path = get_db_path(storage)
    init_db(db_path)
    rowid = add_transaction(db_path, account, amount, ttype, description)
    click.echo(f"ok: inserted id={rowid} db={db_path}")


@cli.command("txn-list")
@click.option("--project", default="default")
@click.option("--account", default=None)
@click.option("--limit", default=100)
def txn_list(project: str, account: Optional[str], limit: int):
    storage = _project_storage(project)
    db_path = get_db_path(storage)
    txs = get_transactions(db_path, account_id=account, limit=limit)
    for t in txs:
        click.echo(str(t))


@cli.command("txn-balance")
@click.option("--project", default="default")
@click.option("--account", required=True)
def txn_balance(project: str, account: str):
    storage = _project_storage(project)
    db_path = get_db_path(storage)
    bal = get_balance(db_path, account)
    click.echo(f"balance: {bal}")


@cli.command("start-mcp")
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8008)
def start_mcp(host: str, port: int):
    """Start the minimal MCP HTTP server (blocks until Ctrl-C)."""
    click.echo(f"Starting MCP server on {host}:{port} (CTRL-C to stop)")
    server = start_mcp_server(host=host, port=port)
    try:
        # block until interrupted
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("Shutting down MCP server")
        try:
            server.shutdown()
        except Exception:
            pass


def main(argv=None):
    try:
        cli(args=argv)
    except SystemExit as e:
        # exit with click's status
        sys.exit(e.code)


if __name__ == "__main__":
    main()
