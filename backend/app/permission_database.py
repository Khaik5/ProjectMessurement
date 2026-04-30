from __future__ import annotations

from typing import Any, Iterable, Sequence

from app.config import get_permission_connection


def fetch_all(query: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
    conn = None
    try:
        conn = get_permission_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        if cursor.description is None:
            return []
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        if conn:
            conn.close()


def fetch_one(query: str, params: Sequence[Any] | None = None) -> dict[str, Any] | None:
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute_query(query: str, params: Sequence[Any] | None = None) -> int:
    conn = None
    try:
        conn = get_permission_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        conn.commit()
        return cursor.rowcount
    finally:
        if conn:
            conn.close()


def execute_many(query: str, params: Iterable[Sequence[Any]]) -> int:
    rows = list(params)
    if not rows:
        return 0
    conn = None
    try:
        conn = get_permission_connection()
        cursor = conn.cursor()
        cursor.executemany(query, rows)
        conn.commit()
        return cursor.rowcount
    finally:
        if conn:
            conn.close()


def insert_and_get_id(query: str, params: Sequence[Any] | None = None) -> int:
    conn = None
    try:
        conn = get_permission_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        row = cursor.fetchone()
        conn.commit()
        return int(row[0])
    finally:
        if conn:
            conn.close()

