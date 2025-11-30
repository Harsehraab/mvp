"""A minimal MCP-like HTTP server to expose orchestration capabilities.

This server implements a tiny JSON API at POST /mcp expecting a body like:
  {"action": "add_transaction", "payload": {...}}

It is purposely minimal and synchronous. For production you'd want an async
framework and authentication.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from typing import Any, Dict, Optional

from . import transactions


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class MCPHandler(BaseHTTPRequestHandler):
    server_version = "CrewMCP/0.1"

    def _send_json(self, status: int, payload: Dict[str, Any]):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_POST(self):
        if self.path != "/mcp":
            self._send_json(404, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "invalid_json"})
            return

        action = payload.get("action")
        data = payload.get("payload", {})

        if action == "add_transaction":
            db_path = data.get("db_path")
            account_id = data.get("account_id")
            amount = float(data.get("amount", 0))
            ttype = data.get("type", "credit")
            desc = data.get("description")
            if not db_path or not account_id:
                self._send_json(400, {"error": "missing_parameters"})
                return
            try:
                transactions.init_db(db_path)
                rowid = transactions.add_transaction(db_path, account_id, amount, ttype, desc)
                self._send_json(200, {"ok": True, "id": rowid})
            except Exception as e:
                self._send_json(500, {"error": "server_error", "message": str(e)})

        elif action == "list_transactions":
            db_path = data.get("db_path")
            account_id = data.get("account_id")
            limit = int(data.get("limit", 100))
            since = data.get("since")
            if not db_path:
                self._send_json(400, {"error": "missing_db_path"})
                return
            try:
                txs = transactions.get_transactions(db_path, account_id=account_id, limit=limit, since=since)
                self._send_json(200, {"ok": True, "transactions": txs})
            except Exception as e:
                self._send_json(500, {"error": "server_error", "message": str(e)})

        elif action == "get_balance":
            db_path = data.get("db_path")
            account_id = data.get("account_id")
            if not db_path or not account_id:
                self._send_json(400, {"error": "missing_parameters"})
                return
            try:
                bal = transactions.get_balance(db_path, account_id)
                self._send_json(200, {"ok": True, "balance": bal})
            except Exception as e:
                self._send_json(500, {"error": "server_error", "message": str(e)})

        else:
            self._send_json(400, {"error": "unknown_action"})


def start_mcp_server(host: str = "127.0.0.1", port: int = 8008) -> Any:
    """Start the MCP server in a background thread and return the server object.

    The server runs in a daemon thread and will stop when the main process exits.
    """
    server = ThreadingHTTPServer((host, port), MCPHandler)

    def _serve():
        try:
            server.serve_forever()
        except Exception:
            pass

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    return server


def stop_mcp_server(server: Any) -> None:
    try:
        server.shutdown()
    except Exception:
        pass


__all__ = ["start_mcp_server", "stop_mcp_server"]
