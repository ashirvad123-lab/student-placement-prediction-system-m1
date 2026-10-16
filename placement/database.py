"""Database helpers that work with MySQL when available and SQLite locally."""

import sqlite3
from pathlib import Path

import mysql.connector
from mysql.connector import Error

from config import Config

DATABASE_DIR = Path(__file__).resolve().parents[1] / "database"
SQLITE_DB_PATH = DATABASE_DIR / "placement_app.db"


def _ensure_sqlite_schema(connection):
    """Create the local SQLite schema used for local demos and tests."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            cgpa REAL NOT NULL,
            tenth_percentage REAL NOT NULL,
            twelfth_percentage REAL NOT NULL,
            branch TEXT NOT NULL,
            backlogs INTEGER NOT NULL DEFAULT 0,
            internship_experience TEXT NOT NULL,
            technical_skill_level TEXT NOT NULL,
            aptitude_score REAL NOT NULL,
            communication_skills REAL NOT NULL,
            projects_completed INTEGER NOT NULL DEFAULT 0,
            placement_status TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            cgpa REAL NOT NULL,
            tenth_percentage REAL NOT NULL,
            twelfth_percentage REAL NOT NULL,
            branch TEXT NOT NULL,
            backlogs INTEGER NOT NULL,
            internship_experience TEXT NOT NULL,
            technical_skill_level TEXT NOT NULL,
            aptitude_score REAL NOT NULL,
            communication_skills REAL NOT NULL,
            projects_completed INTEGER NOT NULL,
            predicted_status TEXT NOT NULL,
            placement_probability REAL,
            model_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL
        )
        """
    )

    connection.commit()


def _row_to_dict(row):
    """Normalize sqlite3 Row objects to plain dictionaries."""
    if row is None:
        return None
    if hasattr(row, "keys"):
        return {key: row[key] for key in row.keys()}
    return row


def get_connection():
    """Open a MySQL connection when configured; otherwise use a local SQLite DB."""
    try:
        return mysql.connector.connect(**Config.MYSQL_CONFIG)
    except Exception:
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(SQLITE_DB_PATH)
        connection.row_factory = sqlite3.Row
        _ensure_sqlite_schema(connection)
        return connection


def _adapt_query(query, connection):
    """Change SQLite-style placeholders to MySQL style when needed."""
    if isinstance(connection, sqlite3.Connection):
        return query
    return query.replace("?", "%s")


def execute(query, params=None):
    """Execute a statement and return the last inserted id when available."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True) if hasattr(connection, "cursor") and connection.__class__.__module__.startswith("mysql") else connection.cursor()
        cursor.execute(_adapt_query(query, connection), params or ())
        connection.commit()
        return cursor.lastrowid
    finally:
        if cursor is not None:
            cursor.close()
        if hasattr(connection, "close"):
            connection.close()


def fetch_all(query, params=None):
    """Execute a parameterized read query and return rows as dictionaries."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True) if hasattr(connection, "cursor") and connection.__class__.__module__.startswith("mysql") else connection.cursor()
        cursor.execute(_adapt_query(query, connection), params or ())
        rows = cursor.fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        if cursor is not None:
            cursor.close()
        if hasattr(connection, "close"):
            connection.close()


def fetch_one(query, params=None):
    """Return the first row or None for a query."""
    rows = fetch_all(query, params)
    return rows[0] if rows else None
