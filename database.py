"""
Database client for storing and retrieving meeting preparation calls.
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json


class DatabaseClient:
    """Client for interacting with the SQLite database."""

    def __init__(self, db_path: str = 'meeting_prep.db'):
        """
        Initialize database client and create tables if needed.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id TEXT UNIQUE,
                    attendee_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    meeting_description TEXT NOT NULL,
                    call_timestamp DATETIME NOT NULL,
                    call_status TEXT,
                    transcript TEXT,
                    summary TEXT,
                    report_file_path TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def save_call(
        self,
        call_id: str,
        attendee_name: str,
        phone_number: str,
        meeting_description: str,
        call_timestamp: datetime,
        call_status: str,
        transcript: str,
        summary: str,
        report_file_path: str
    ) -> int:
        """
        Save a completed call to the database.

        Args:
            call_id: Vapi call ID
            attendee_name: Name of person called
            phone_number: Phone number called
            meeting_description: Description of the meeting
            call_timestamp: When the call occurred
            call_status: Status of the call (completed, failed, etc.)
            transcript: Full call transcript
            summary: AI-generated summary
            report_file_path: Path to saved markdown file

        Returns:
            Database row ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO calls (
                    call_id, attendee_name, phone_number, meeting_description,
                    call_timestamp, call_status, transcript, summary, report_file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                call_id, attendee_name, phone_number, meeting_description,
                call_timestamp.isoformat(), call_status, transcript, summary, report_file_path
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_calls(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get all calls, ordered by most recent first.

        Args:
            limit: Maximum number of calls to return
            offset: Number of calls to skip

        Returns:
            List of call dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM calls
                ORDER BY call_timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_call_by_id(self, call_id: int) -> Optional[Dict]:
        """
        Get a specific call by database ID.

        Args:
            call_id: Database row ID

        Returns:
            Call dictionary or None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM calls WHERE id = ?', (call_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_call_by_vapi_id(self, vapi_call_id: str) -> Optional[Dict]:
        """
        Get a specific call by Vapi call ID.

        Args:
            vapi_call_id: Vapi call ID

        Returns:
            Call dictionary or None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM calls WHERE call_id = ?', (vapi_call_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def search_calls(self, query: str) -> List[Dict]:
        """
        Search calls by attendee name or meeting description.

        Args:
            query: Search query

        Returns:
            List of matching call dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM calls
                WHERE attendee_name LIKE ? OR meeting_description LIKE ?
                ORDER BY call_timestamp DESC
            ''', (f'%{query}%', f'%{query}%'))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_call(self, call_id: int) -> bool:
        """
        Delete a call from the database.

        Args:
            call_id: Database row ID

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM calls WHERE id = ?', (call_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Dict:
        """
        Get database statistics.

        Returns:
            Dictionary with stats
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total calls
            cursor.execute('SELECT COUNT(*) FROM calls')
            total_calls = cursor.fetchone()[0]

            # Successful calls (both 'ended' and 'completed' are considered successful)
            cursor.execute("SELECT COUNT(*) FROM calls WHERE call_status IN ('completed', 'ended')")
            successful_calls = cursor.fetchone()[0]

            # Recent calls (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM calls
                WHERE call_timestamp >= datetime('now', '-7 days')
            ''')
            recent_calls = cursor.fetchone()[0]

            return {
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'recent_calls': recent_calls
            }
