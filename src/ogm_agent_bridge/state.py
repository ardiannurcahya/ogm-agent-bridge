"""Durable local bridge state."""

from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path
from typing import cast


class StateStore:
    """SQLite registry; one row per project identity."""

    def __init__(self, path: Path, project_id: str) -> None:
        self.path = path
        self.project_id = project_id
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        os.chmod(path, 0o600)
        self.db.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def close(self) -> None:
        self.db.close()

    def _migrate(self) -> None:
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
        )
        row = self.db.execute("SELECT version FROM schema_version").fetchone()
        if row is None:
            self.db.execute("INSERT INTO schema_version VALUES (1)")
            self.db.executescript("""
            CREATE TABLE users (project_id TEXT NOT NULL, external_id TEXT NOT NULL, core_id TEXT, status TEXT NOT NULL CHECK(status IN ('provisioning','active','uncertain')), PRIMARY KEY(project_id, external_id));
            CREATE TABLE agents (project_id TEXT NOT NULL, name TEXT NOT NULL, core_id TEXT, status TEXT NOT NULL CHECK(status IN ('provisioning','active','uncertain')), PRIMARY KEY(project_id, name));
            CREATE TABLE sessions (project_id TEXT NOT NULL, bridge_id TEXT NOT NULL, user_external_id TEXT NOT NULL, agent_name TEXT NOT NULL, core_id TEXT, status TEXT NOT NULL CHECK(status IN ('provisioning','active','uncertain')), PRIMARY KEY(project_id, bridge_id), UNIQUE(project_id, user_external_id, agent_name));
            """)
        self.db.commit()

    def identity(self, kind: str, key: str) -> tuple[str | None, str] | None:
        column = "external_id" if kind == "users" else "name"
        return cast(
            tuple[str | None, str] | None,
            self.db.execute(
                f"SELECT core_id, status FROM {kind} WHERE project_id=? AND {column}=?",
                (self.project_id, key),
            ).fetchone(),
        )

    def begin_identity(self, kind: str, key: str) -> None:
        column = "external_id" if kind == "users" else "name"
        self.db.execute(
            f"INSERT OR IGNORE INTO {kind}(project_id,{column},status) VALUES(?,?, 'provisioning')",
            (self.project_id, key),
        )
        self.db.commit()

    def finish_identity(self, kind: str, key: str, core_id: str) -> None:
        column = "external_id" if kind == "users" else "name"
        self.db.execute(
            f"UPDATE {kind} SET core_id=?, status='active' WHERE project_id=? AND {column}=?",
            (core_id, self.project_id, key),
        )
        self.db.commit()

    def uncertain_identity(self, kind: str, key: str) -> None:
        column = "external_id" if kind == "users" else "name"
        self.db.execute(
            f"UPDATE {kind} SET status='uncertain' WHERE project_id=? AND {column}=?",
            (self.project_id, key),
        )
        self.db.commit()

    def session(self, user: str, agent: str) -> tuple[str, str | None, str] | None:
        return cast(
            tuple[str, str | None, str] | None,
            self.db.execute(
                "SELECT bridge_id, core_id, status FROM sessions WHERE project_id=? AND user_external_id=? AND agent_name=?",
                (self.project_id, user, agent),
            ).fetchone(),
        )

    def begin_session(self, user: str, agent: str) -> str:
        row = self.session(user, agent)
        if row:
            return row[0]
        bridge_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO sessions VALUES(?,?,?,?,?,?)",
            (self.project_id, bridge_id, user, agent, None, "provisioning"),
        )
        self.db.commit()
        return bridge_id

    def finish_session(self, bridge_id: str, core_id: str) -> None:
        self.db.execute(
            "UPDATE sessions SET core_id=?, status='active' WHERE project_id=? AND bridge_id=?",
            (core_id, self.project_id, bridge_id),
        )
        self.db.commit()

    def uncertain_session(self, bridge_id: str) -> None:
        self.db.execute(
            "UPDATE sessions SET status='uncertain' WHERE project_id=? AND bridge_id=?",
            (self.project_id, bridge_id),
        )
        self.db.commit()

    def resolve_session(self, bridge_id: str) -> str | None:
        row = self.db.execute(
            "SELECT core_id,status FROM sessions WHERE project_id=? AND bridge_id=?",
            (self.project_id, bridge_id),
        ).fetchone()
        return row[0] if row and row[1] == "active" else None
