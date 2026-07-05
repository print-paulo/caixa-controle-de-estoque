from pathlib import Path
import sqlite3

BANCO = Path(__file__).resolve().parent.parent / "database" / "banco.db"

def conectar_banco():
    conn = sqlite3.connect(BANCO)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn