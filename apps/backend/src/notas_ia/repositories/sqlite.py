from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from ..domain.models import Conversation, Message, Summary
from ..errors import ConflictError, NotFoundError


SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    model_profile TEXT NOT NULL,
    assistant_profile TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    next_sequence INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(conversation_id, sequence)
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_sequence
    ON messages(conversation_id, sequence);
CREATE TABLE IF NOT EXISTS summaries (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    through_sequence INTEGER NOT NULL,
    model_profile TEXT NOT NULL,
    model TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(conversation_id, version)
);
CREATE INDEX IF NOT EXISTS idx_summaries_conversation_version
    ON summaries(conversation_id, version DESC);
CREATE TABLE IF NOT EXISTS generation_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    purpose TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    status TEXT NOT NULL,
    error_code TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency_keys (
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    client_message_id TEXT NOT NULL,
    content TEXT NOT NULL,
    user_message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    response_json TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(conversation_id, client_message_id)
);
"""

SCHEMA_V2 = """
ALTER TABLE conversations ADD COLUMN memory_profile TEXT NOT NULL DEFAULT 'recent-window-v1';
CREATE TABLE IF NOT EXISTS tool_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    assistant_message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    status TEXT NOT NULL,
    strategy TEXT,
    source_ids_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS message_sources (
    assistant_message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    reference TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    document TEXT NOT NULL,
    section TEXT NOT NULL,
    url TEXT NOT NULL,
    verified_at TEXT,
    PRIMARY KEY(assistant_message_id, reference)
);
CREATE TABLE IF NOT EXISTS handoff_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    assistant_message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    mode TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    human_available INTEGER NOT NULL,
    template_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _conversation(row: sqlite3.Row) -> Conversation:
    return Conversation(**dict(row))


def _message(row: sqlite3.Row) -> Message:
    return Message(**dict(row))


def _summary(row: sqlite3.Row) -> Summary:
    return Summary(**dict(row))


class SQLiteConversationRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            row = connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version=1"
            ).fetchone()
            if not row:
                connection.executescript(SCHEMA_V1)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) "
                    "VALUES(1, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"
                )
            row = connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version=2"
            ).fetchone()
            if not row:
                connection.executescript(SCHEMA_V2)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) "
                    "VALUES(2, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"
                )

    def check(self) -> bool:
        with self._connect() as connection:
            return connection.execute("SELECT 1").fetchone()[0] == 1

    def create_conversation(self, conversation: Conversation) -> Conversation:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO conversations "
                "(id,model_profile,assistant_profile,prompt_version,created_at,updated_at,"
                "next_sequence,memory_profile) VALUES(?,?,?,?,?,?,?,?)",
                (conversation.id, conversation.model_profile, conversation.assistant_profile,
                 conversation.prompt_version, conversation.created_at, conversation.updated_at,
                 conversation.next_sequence, conversation.memory_profile),
            )
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM conversations WHERE id=?", (conversation_id,)
            ).fetchone()
        return _conversation(row) if row else None

    def delete_conversation(self, conversation_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))
            return cursor.rowcount > 0

    def list_messages(self, conversation_id: str, after_sequence: int = 0,
                      limit: int = 1000) -> list[Message]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM messages WHERE conversation_id=? AND sequence>? "
                "ORDER BY sequence LIMIT ?",
                (conversation_id, after_sequence, limit),
            ).fetchall()
        return [_message(row) for row in rows]

    def get_latest_summary(self, conversation_id: str) -> Summary | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM summaries WHERE conversation_id=? "
                "ORDER BY version DESC LIMIT 1", (conversation_id,)
            ).fetchone()
        return _summary(row) if row else None

    def save_summary(self, summary: Summary) -> Summary:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO summaries VALUES(?,?,?,?,?,?,?,?)",
                (summary.id, summary.conversation_id, summary.version, summary.content,
                 summary.through_sequence, summary.model_profile, summary.model,
                 summary.created_at),
            )
        return summary

    def begin_turn(self, conversation_id: str, client_message_id: str,
                   content: str) -> tuple[str, Message, dict[str, Any] | None]:
        from datetime import datetime, timezone
        from uuid import uuid4

        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            conversation = connection.execute(
                "SELECT * FROM conversations WHERE id=?", (conversation_id,)
            ).fetchone()
            if not conversation:
                connection.rollback()
                raise NotFoundError("Conversa não encontrada")
            existing = connection.execute(
                "SELECT * FROM idempotency_keys WHERE conversation_id=? "
                "AND client_message_id=?", (conversation_id, client_message_id),
            ).fetchone()
            if existing:
                if existing["content"] != content:
                    connection.rollback()
                    raise ConflictError(
                        "client_message_id já foi usado com outro conteúdo"
                    )
                message_row = connection.execute(
                    "SELECT * FROM messages WHERE id=?", (existing["user_message_id"],)
                ).fetchone()
                cached = json.loads(existing["response_json"]) \
                    if existing["status"] == "completed" else None
                if not cached:
                    if message_row["sequence"] != conversation["next_sequence"] - 1:
                        connection.rollback()
                        raise ConflictError(
                            "Uma tentativa antiga não pode ser retomada após novos turnos"
                        )
                    connection.execute(
                        "UPDATE idempotency_keys SET status='processing', updated_at=? "
                        "WHERE conversation_id=? AND client_message_id=?",
                        (now, conversation_id, client_message_id),
                    )
                connection.commit()
                return ("completed" if cached else "retry", _message(message_row), cached)

            message = Message(str(uuid4()), conversation_id,
                              conversation["next_sequence"], "user", content,
                              "accepted", now)
            connection.execute(
                "INSERT INTO messages VALUES(?,?,?,?,?,?,?)",
                (message.id, message.conversation_id, message.sequence, message.role,
                 message.content, message.status, message.created_at),
            )
            connection.execute(
                "UPDATE conversations SET next_sequence=next_sequence+1, updated_at=? WHERE id=?",
                (now, conversation_id),
            )
            connection.execute(
                "INSERT INTO idempotency_keys VALUES(?,?,?,?,?,?,?)",
                (conversation_id, client_message_id, content, message.id, "processing", None, now),
            )
            connection.commit()
            return "started", message, None

    def complete_turn(self, conversation_id: str, client_message_id: str,
                      assistant: Message, response: dict[str, Any],
                      attempts: list[dict[str, Any]],
                      tool_executions: list[dict[str, Any]] | None = None,
                      sources: list[dict[str, Any]] | None = None,
                      handoff: dict[str, Any] | None = None) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            sequence = connection.execute(
                "SELECT next_sequence FROM conversations WHERE id=?", (conversation_id,)
            ).fetchone()[0]
            if sequence != assistant.sequence:
                connection.rollback()
                raise ConflictError("A sequência da conversa mudou durante a geração")
            connection.execute(
                "INSERT INTO messages VALUES(?,?,?,?,?,?,?)",
                (assistant.id, assistant.conversation_id, assistant.sequence, assistant.role,
                 assistant.content, assistant.status, assistant.created_at),
            )
            connection.execute(
                "UPDATE conversations SET next_sequence=next_sequence+1, updated_at=? WHERE id=?",
                (assistant.created_at, conversation_id),
            )
            connection.execute(
                "UPDATE idempotency_keys SET status='completed', response_json=?, updated_at=? "
                "WHERE conversation_id=? AND client_message_id=?",
                (json.dumps(response, ensure_ascii=False), assistant.created_at,
                 conversation_id, client_message_id),
            )
            for attempt in attempts:
                self._insert_attempt(connection, attempt)
            for execution in tool_executions or []:
                connection.execute(
                    "INSERT INTO tool_executions "
                    "(conversation_id,user_message_id,assistant_message_id,tool_name,status,"
                    "strategy,source_ids_json,created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (conversation_id, execution["user_message_id"], assistant.id,
                     execution["tool_name"], execution["status"], execution.get("strategy"),
                     json.dumps(execution.get("source_ids", []), ensure_ascii=False),
                     assistant.created_at),
                )
            for source in sources or []:
                connection.execute(
                    "INSERT INTO message_sources "
                    "(assistant_message_id,reference,chunk_id,document,section,url,verified_at) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (assistant.id, source["reference"], source["chunk_id"],
                     source["document"], source["section"], source["url"],
                     source.get("verified_at")),
                )
            if handoff:
                connection.execute(
                    "INSERT INTO handoff_events "
                    "(conversation_id,user_message_id,assistant_message_id,mode,reason,status,"
                    "human_available,template_id,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                    (conversation_id, handoff["user_message_id"], assistant.id,
                     handoff["mode"], handoff["reason"], handoff["status"],
                     int(handoff["human_available"]), handoff["template_id"],
                     assistant.created_at),
                )
            connection.commit()

    def fail_turn(self, conversation_id: str, client_message_id: str,
                  attempt: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE idempotency_keys SET status='failed', updated_at=? "
                "WHERE conversation_id=? AND client_message_id=?",
                (attempt["created_at"], conversation_id, client_message_id),
            )
            self._insert_attempt(connection, attempt)
            connection.commit()

    def record_attempt(self, attempt: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._insert_attempt(connection, attempt)
            connection.commit()

    @staticmethod
    def _insert_attempt(connection: sqlite3.Connection, attempt: dict[str, Any]) -> None:
        connection.execute(
            "INSERT INTO generation_attempts "
            "(conversation_id,user_message_id,purpose,provider,model,latency_ms," 
            "input_tokens,output_tokens,status,error_code,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            tuple(attempt.get(key) for key in (
                "conversation_id", "user_message_id", "purpose", "provider", "model",
                "latency_ms", "input_tokens", "output_tokens", "status", "error_code",
                "created_at",
            )),
        )

    def count_user_messages(self, conversation_id: str) -> int:
        with self._connect() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM messages WHERE conversation_id=? AND role='user'",
                (conversation_id,),
            ).fetchone()[0]

    def list_sources(self, conversation_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT s.* FROM message_sources s JOIN messages m "
                "ON m.id=s.assistant_message_id WHERE m.conversation_id=? "
                "ORDER BY m.sequence, s.reference",
                (conversation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_handoff_events(self, conversation_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT mode,reason,status,human_available,template_id,created_at "
                "FROM handoff_events WHERE conversation_id=? ORDER BY id",
                (conversation_id,),
            ).fetchall()
        return [
            {**dict(row), "human_available": bool(row["human_available"])}
            for row in rows
        ]
