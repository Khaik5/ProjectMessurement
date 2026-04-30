from __future__ import annotations

from typing import Any, Iterable, Sequence

from app.config import get_sqlserver_connection


def _row_to_dict(cursor, row) -> dict[str, Any]:
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def get_connection():
    return get_sqlserver_connection()


def execute_query(query: str, params: Sequence[Any] | None = None) -> int:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        affected = cursor.rowcount
        conn.commit()
        return affected
    finally:
        if conn:
            conn.close()


def fetch_all(query: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        if cursor.description is None:
            return []
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        if conn:
            conn.close()


def fetch_one(query: str, params: Sequence[Any] | None = None) -> dict[str, Any] | None:
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute_many(query: str, params: Iterable[Sequence[Any]]) -> int:
    params = list(params)
    if not params:
        return 0
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.fast_executemany = True
        cursor.executemany(query, params)
        conn.commit()
        return cursor.rowcount


def insert_and_get_id(query: str, params: Sequence[Any] | None = None) -> int:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        row = cursor.fetchone()
        conn.commit()
        return int(row[0])
    finally:
        if conn:
            conn.close()


def execute_insert_return_id(query: str, params: Sequence[Any] | None = None) -> int:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query + "; SELECT SCOPE_IDENTITY();", params or [])
        row = cursor.fetchone()
        conn.commit()
        return int(row[0])
    finally:
        if conn:
            conn.close()


def test_connection() -> dict[str, Any]:
    try:
        row = fetch_one("SELECT DB_NAME() AS database_name, @@SERVERNAME AS server_name")
        return {"connected": True, **(row or {})}
    except Exception as exc:
        return {"connected": False, "error": str(exc)}
