import os
import sqlite3
import hashlib
import hmac
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configuração da Base de Dados Local (SQLite)
DB_FILE = "infinito_ledger.db"
SECRET_KEY = hashlib.sha3_256(b"INFINITO_CORE_V36_MASTER_SECRET").digest()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            sender TEXT,
            receiver TEXT,
            amount REAL,
            signature TEXT,
            prev_hash TEXT,
            hash TEXT
        )
    """)
    conn.commit()
    
    # Criar bloco genesis se estiver vazio
    cursor.execute("SELECT COUNT(*) FROM ledger")
    if cursor.fetchone()[0] == 0:
        ts = time.time()
        genesis_prev = "0" * 64
        raw_data = f"{ts}:GENESIS:CORE:0.0:{genesis_prev}".encode()
        genesis_hash = hmac.new(SECRET_KEY, raw_data, hashlib.sha3_256).hexdigest()
        cursor.execute("""
            INSERT INTO ledger (timestamp, sender, receiver, amount, signature, prev_hash, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ts, "GENESIS", "CORE", 0.0, "MASTER_INIT", genesis_prev, genesis_hash))
        conn.commit()
    conn.close()

def add_transaction(sender, receiver, amount):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT hash FROM ledger ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    prev_hash = row[0] if row else "0" * 64
    
    ts = time.time()
    payload = f"{ts}:{sender}:{receiver}:{amount}:{prev_hash}".encode()
    signature = hmac.new(SECRET_KEY, payload, hashlib.sha3_256).hexdigest()
    current_hash = hashlib.sha3_256(signature + prev_hash.encode()).hexdigest()
    
    cursor.execute("""
        INSERT INTO ledger (timestamp, sender, receiver, amount, signature, prev_hash, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ts, sender, receiver, amount, signature, prev_hash, current_hash))
    conn.commit()
    conn.close()

def get_ledger():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, sender, receiver, amount, hash FROM ledger ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Painel HTML Completo Embutido
HTML_PANEL = """<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Infinito Core V36 - Sovereign Ledger</title>
    <style>
        :root { --bg: #050505; --card: #111; --accent: #00ffcc; --text: #e0e0e0; --border: #222; }
        body { background: var(--bg); color: var(--text); font-family: monospace; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; }
        header { border-bottom: 1px solid var(--accent); padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        h1 { margin: 0; color: var(--accent); font-size: 1.5rem; }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 15px; margin-bottom: 20px; }
        input, button { background: #000; border: 1px solid var(--accent); color: var(--accent); padding: 10px; margin: 5px 0; width: 100%; box-sizing: border-box; font-family: monospace; }
        button { background: var(--accent); color: #000; font-weight: bold; cursor: pointer; }
        button:hover { opacity: 0.8; }
        table { width: 100%%; border-collapse: collapse; margin-top: 10px; font-size: 0.85rem; }
        th, td { border: 1px solid var(--border); padding: 8px; text-align: left; word-break: break-all; }
        th { background: #1a1a1a; color: var(--accent); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>INFINITO CORE V36</h1>
            <span>STATUS: ONLINE</span>
        </header>
        
        <div class="card">
            <h3>Nova Transação Ledger</h3>
            <form method="POST" action="/transactor">
                <label>Origem (Sender):</label>
                <input type="text" name="sender" value="Node-Alpha" required>
                <label>Destino (Receiver):</label>
                <input type="text" name="receiver" value="Node-Beta" required>
                <label>Montante:</label>
                <input type="number" step="any" name="amount" value="100.0" required>
                <button type="submit">Registar no Ledger Soberano</button>
            </form>
        </div>

        <div class="card">
            <h3>Blocos Registados</h3>
            <table>
                <thead>
                    <tr><th>ID</th><th>Timestamp</th><th>De -> Para</th><th>Montante</th><th>Hash</th></tr>
                </thead>
                <tbody>
                    {{ROWS}}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

class SovereignHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            rows = get_ledger()
            rows_html =
