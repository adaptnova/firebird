"""
PERSIST - Continue existing

Core persistence module for maintaining state, memory, and continuity across sessions.
Implements the 'PERSIST' principle from PACK-I.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import pickle
import hashlib


class PersistentMemory:
    """Long-term memory storage with embeddings for retrieval."""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize persistent memory.

        Args:
            storage_path: Path to store memory files. Defaults to ~/.adapt_memory/
        """
        if storage_path is None:
            storage_path = str(Path.home() / ".adapt_memory")

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        # Initialize SQLite DB for structured memory
        self.db_path = self.storage_path / "memory.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for memory storage."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Sessions table - track conversation sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Memories table - store key learnings and facts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB,
                created_at TEXT NOT NULL,
                importance REAL DEFAULT 1.0,
                access_count INTEGER DEFAULT 0,
                tags TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)

        # Events table - track actions and outcomes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                event_type TEXT NOT NULL,
                action TEXT NOT NULL,
                outcome TEXT,
                timestamp TEXT NOT NULL,
                success BOOLEAN,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)

        # Knowledge base - persistent facts about self/team/tools
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT,
                confidence REAL DEFAULT 1.0,
                last_updated TEXT NOT NULL,
                UNIQUE(category, key)
            )
        """)

        conn.commit()
        conn.close()

    def create_session(self, session_id: str, metadata: Optional[Dict] = None) -> str:
        """
        Create a new session.

        Args:
            session_id: Unique identifier for the session
            metadata: Optional metadata about the session

        Returns:
            Session ID
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (id, created_at, last_accessed, metadata)
            VALUES (?, ?, ?, ?)
        """, (session_id, now, now, json.dumps(metadata) if metadata else None))

        conn.commit()
        conn.close()
        return session_id

    def save_memory(
        self,
        session_id: str,
        memory_type: str,
        content: Union[str, Dict],
        importance: float = 1.0,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        Save a memory to long-term storage.

        Args:
            session_id: Session identifier
            memory_type: Type of memory (e.g., 'learning', 'fact', 'preference')
            content: Memory content
            importance: Importance score (0.0 to 1.0)
            tags: Optional tags for categorization

        Returns:
            Memory ID
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()
        content_str = json.dumps(content) if isinstance(content, dict) else str(content)

        cursor.execute("""
            INSERT INTO memories (session_id, type, content, created_at, importance, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            memory_type,
            content_str,
            now,
            importance,
            json.dumps(tags) if tags else None
        ))

        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return memory_id

    def recall_memory(
        self,
        session_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        importance_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Recall memories based on filters.

        Args:
            session_id: Filter by session (None for all sessions)
            memory_type: Filter by memory type
            tags: Filter by tags
            limit: Maximum number of memories to return
            importance_threshold: Minimum importance score

        Returns:
            List of memories
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Build query
        conditions = ["importance >= ?"]
        params = [importance_threshold]

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        if memory_type:
            conditions.append("type = ?")
            params.append(memory_type)

        query = f"""
            SELECT id, session_id, type, content, created_at, importance, tags, access_count
            FROM memories
            WHERE {" AND ".join(conditions)}
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
        """
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        memories = []
        for row in rows:
            memories.append({
                "id": row[0],
                "session_id": row[1],
                "type": row[2],
                "content": row[3],
                "created_at": row[4],
                "importance": row[5],
                "tags": json.loads(row[6]) if row[6] else [],
                "access_count": row[7]
            })

        conn.close()
        return memories

    def record_event(
        self,
        session_id: str,
        event_type: str,
        action: str,
        outcome: Optional[str] = None,
        success: Optional[bool] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Record an event (action + outcome).

        Args:
            session_id: Session identifier
            event_type: Type of event (e.g., 'action', 'decision', 'error')
            action: The action taken
            outcome: Result of the action
            success: Whether the action was successful
            metadata: Additional metadata

        Returns:
            Event ID
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO events (session_id, event_type, action, outcome, timestamp, success, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            event_type,
            action,
            outcome,
            now,
            success,
            json.dumps(metadata) if metadata else None
        ))

        event_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return event_id

    def get_recent_events(
        self,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent events.

        Args:
            session_id: Filter by session
            event_type: Filter by event type
            limit: Maximum number of events

        Returns:
            List of events
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        conditions = []
        params = []

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)

        query = f"""
            SELECT id, session_id, event_type, action, outcome, timestamp, success, metadata
            FROM events
            {f'WHERE {" AND ".join(conditions)}' if conditions else ''}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        events = []
        for row in rows:
            events.append({
                "id": row[0],
                "session_id": row[1],
                "type": row[2],
                "action": row[3],
                "outcome": row[4],
                "timestamp": row[5],
                "success": row[6],
                "metadata": json.loads(row[7]) if row[7] else {}
            })

        conn.close()
        return events

    def save_knowledge(self, category: str, key: str, value: str, source: str = "agent", confidence: float = 1.0):
        """
        Save knowledge to the knowledge base.

        Args:
            category: Category (e.g., 'self', 'tool', 'team')
            key: Knowledge key
            value: Knowledge value
            source: Source of knowledge
            confidence: Confidence level (0.0 to 1.0)
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO knowledge (category, key, value, source, confidence, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category, key, value, source, confidence, now))

        conn.commit()
        conn.close()

    def get_knowledge(self, category: Optional[str] = None, key: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve knowledge from the knowledge base.

        Args:
            category: Filter by category
            key: Filter by specific key

        Returns:
            Dictionary of knowledge
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        conditions = []
        params = []

        if category:
            conditions.append("category = ?")
            params.append(category)

        if key:
            conditions.append("key = ?")
            params.append(key)

        query = f"""
            SELECT category, key, value, source, confidence, last_updated
            FROM knowledge
            {f'WHERE {" AND ".join(conditions)}' if conditions else ''}
            ORDER BY category, key
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        knowledge = {}
        for row in rows:
            cat, k, v, src, conf, updated = row
            if cat not in knowledge:
                knowledge[cat] = {}
            knowledge[cat][k] = {
                "value": v,
                "source": src,
                "confidence": conf,
                "last_updated": updated
            }

        conn.close()
        return knowledge

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary of statistics
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        stats = {"session_id": session_id}

        # Memory count
        cursor.execute("SELECT COUNT(*) FROM memories WHERE session_id = ?", (session_id,))
        stats["memory_count"] = cursor.fetchone()[0]

        # Event count
        cursor.execute("SELECT COUNT(*) FROM events WHERE session_id = ?", (session_id,))
        stats["event_count"] = cursor.fetchone()[0]

        # Success rate
        cursor.execute("""
            SELECT COUNT(*), SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END)
            FROM events WHERE session_id = ? AND success IS NOT NULL
        """, (session_id,))
        total, successful = cursor.fetchone()
        stats["success_rate"] = (successful / total if total > 0 else 0)

        # Session duration
        cursor.execute("""
            SELECT created_at FROM sessions WHERE id = ?
        """, (session_id,))
        created = cursor.fetchone()
        if created:
            created_time = datetime.fromisoformat(created[0])
            duration = datetime.utcnow() - created_time
            stats["duration_hours"] = duration.total_seconds() / 3600

        conn.close()
        return stats


class StateManager:
    """Manages working state for the current session."""

    def __init__(self, session_id: str, memory: PersistentMemory):
        """
        Initialize state manager.

        Args:
            session_id: Current session ID
            memory: Persistent memory instance
        """
        self.session_id = session_id
        self.memory = memory
        self.working_memory: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        """Set a value in working memory."""
        self.working_memory[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from working memory."""
        return self.working_memory.get(key, default)

    def save_to_longterm(self, key: str, memory_type: str = "state", importance: float = 0.8):
        """Save working memory to long-term memory."""
        if key in self.working_memory:
            self.memory.save_memory(
                self.session_id,
                memory_type,
                {key: self.working_memory[key]},
                importance=importance
            )

    def load_from_longterm(self, key: str) -> Optional[Any]:
        """Load from long-term memory to working memory."""
        memories = self.memory.recall_memory(
            session_id=self.session_id,
            memory_type="state",
            limit=100
        )

        for memory in memories:
            try:
                content = json.loads(memory["content"])
                if key in content:
                    self.working_memory[key] = content[key]
                    return content[key]
            except:
                continue

        return None

    def clear(self):
        """Clear working memory."""
        self.working_memory.clear()

    def snapshot(self) -> Dict[str, Any]:
        """Take a snapshot of current state."""
        return {
            "session_id": self.session_id,
            "working_memory": self.working_memory.copy(),
            "timestamp": datetime.utcnow().isoformat()
        }
