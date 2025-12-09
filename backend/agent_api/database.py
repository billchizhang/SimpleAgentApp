"""
Database manager for Agent API user authentication.

Provides SQLite operations for user management with secure practices.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime

from .auth import hash_password, generate_uid


class DatabaseManager:
    """
    Manages SQLite database operations for user authentication.

    Provides CRUD operations for users with proper error handling,
    transaction management, and SQL injection prevention.
    """

    def __init__(self, db_path: Path):
        """
        Initialize database manager and create schema if needed.

        Args:
            db_path: Path to SQLite database file

        Raises:
            sqlite3.Error: If database initialization fails
        """
        self.db_path = Path(db_path)
        self._ensure_database_exists()

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with automatic commit/rollback.

        Yields:
            sqlite3.Connection: Database connection with row_factory enabled

        Example:
            >>> with db.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT * FROM users")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_database_exists(self):
        """
        Create database file and schema if they don't exist.

        Creates:
            - users table with proper constraints
            - Indexes on username, email, and role

        Raises:
            sqlite3.Error: If schema creation fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    uid TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'admin')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_username ON users(username)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_email ON users(email)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_role ON users(role)
            """)

    def initialize_default_users(self):
        """
        Create default admin and user accounts if they don't exist.

        Default accounts:
            - admin / AdminPass123!
            - demo_user / UserPass123!

        Returns:
            None

        Note:
            Silently skips if users already exist
        """
        default_users = [
            {
                "username": "admin",
                "email": "admin@simpleagent.local",
                "password": "AdminPass123!",
                "role": "admin"
            },
            {
                "username": "demo_user",
                "email": "user@simpleagent.local",
                "password": "UserPass123!",
                "role": "user"
            }
        ]

        for user_data in default_users:
            if not self.user_exists(user_data["username"]):
                try:
                    self.create_user(
                        username=user_data["username"],
                        email=user_data["email"],
                        password_hash=hash_password(user_data["password"]),
                        role=user_data["role"]
                    )
                    print(f"   ✓ Created default {user_data['role']}: {user_data['username']}")
                except Exception as e:
                    print(f"   ✗ Failed to create {user_data['username']}: {e}")

    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: str
    ) -> Dict[str, Any]:
        """
        Create a new user in the database.

        Args:
            username: Unique username
            email: Unique email address
            password_hash: Bcrypt hashed password
            role: User role ('user' or 'admin')

        Returns:
            Dict containing user data (excluding password_hash)

        Raises:
            sqlite3.IntegrityError: If username or email already exists
            sqlite3.Error: If database operation fails

        Example:
            >>> from auth import hash_password
            >>> user = db.create_user(
            ...     username="johndoe",
            ...     email="john@example.com",
            ...     password_hash=hash_password("SecurePass123!"),
            ...     role="user"
            ... )
            >>> user['username']
            'johndoe'
        """
        uid = generate_uid()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (uid, username, email, password_hash, role)
                VALUES (?, ?, ?, ?, ?)
                """,
                (uid, username, email, password_hash, role)
            )

        # Return user data (without password_hash)
        return self.get_user_by_username(username)

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by username.

        Args:
            username: Username to look up

        Returns:
            Dict containing user data, or None if not found

        Example:
            >>> user = db.get_user_by_username("johndoe")
            >>> if user:
            ...     print(user['email'])
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by email address.

        Args:
            email: Email address to look up

        Returns:
            Dict containing user data, or None if not found

        Example:
            >>> user = db.get_user_by_email("john@example.com")
            >>> if user:
            ...     print(user['username'])
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def remove_user(self, username: str) -> bool:
        """
        Delete user by username.

        Args:
            username: Username of user to delete

        Returns:
            True if user was deleted, False if user not found

        Raises:
            sqlite3.Error: If database operation fails

        Example:
            >>> success = db.remove_user("johndoe")
            >>> print(f"User removed: {success}")
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM users WHERE username = ?",
                (username,)
            )
            return cursor.rowcount > 0

    def user_exists(self, username: str) -> bool:
        """
        Check if username exists in database.

        Args:
            username: Username to check

        Returns:
            True if user exists, False otherwise

        Example:
            >>> if db.user_exists("johndoe"):
            ...     print("User already exists")
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM users WHERE username = ? LIMIT 1",
                (username,)
            )
            return cursor.fetchone() is not None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Retrieve all users from database (excluding password hashes).

        Returns:
            List of user dicts (without password_hash field)

        Example:
            >>> users = db.get_all_users()
            >>> for user in users:
            ...     print(f"{user['username']} - {user['role']}")
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT uid, username, email, role, created_at, updated_at FROM users"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_user_count(self) -> int:
        """
        Get total number of users in database.

        Returns:
            Count of users

        Example:
            >>> count = db.get_user_count()
            >>> print(f"Total users: {count}")
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]
