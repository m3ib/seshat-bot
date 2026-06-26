"""The interface to all db operations."""

import os
import sqlite3

from .config import Config
from .utils import APP_DIR, ROOT_DIR

_db_path = ""  # set by init_db


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    """Create a new connection object to db.

    Note: Run init_db once before calling this function.
    """
    conn = sqlite3.Connection(db_path or _db_path)
    conn.row_factory = sqlite3.Row

    return conn


def init_db(config: Config) -> sqlite3.Connection:
    """Execute the database schema and set the required pragmas."""
    global _db_path

    is_dir = "/" in config.db or "\\" in config.db
    dirname = os.path.dirname(config.db)
    if not os.path.exists(dirname) and is_dir:
        os.mkdir(dirname)
    _db_path = config.db

    con = get_db()
    cur = con.cursor()
    cur.execute("PRAGMA FOREIGN_KEYS = ON")

    with open(os.path.join(APP_DIR, "schema.sql"), "r") as f:
        cur.executescript(f.read())

    cur.close()
    con.commit()

    return con


def create_group(name: str, connection: sqlite3.Connection | None = None) -> int:
    """Create a new group entity with given name.

    Args:
        name: The name of the group.
        connection: A connection object to use instead of creating a new one. Used for testing

    Returns: id of the created group.
    """
    con = connection or get_db()

    cur = con.cursor()
    cur.execute("INSERT INTO courseGroup (name) VALUES (?)", (name,))
    last_id = cur.lastrowid
    con.commit()

    return last_id


def create_course(
    group_id: int,
    name: str,
    channel_id: int | None = None,
    order: int | None = None,
    connection: sqlite3.Connection | None = None,
) -> int:
    """Create a new course entity under the given group.

    Args:
        group_id: The id of the group that will own the course.
        name: The name of the course.
        channel_id: Channel to associate the course with.
        order: Sort key, creation date will be used otherwise.
        connection: A connection object to use instead of creating a new one. Used for testing

    Returns: id of the created course.
    """
    con = connection or get_db()

    cur = con.cursor()
    cur.execute(
        "INSERT INTO course (courseGroupId, name, channelId, ord) VALUES (?, ?, ?, ?)",
        (group_id, name, channel_id, order),
    )
    last_id = cur.lastrowid
    con.commit()

    return last_id


def create_module(
    course_id: int,
    name: str,
    order: int | None = None,
    connection: sqlite3.Connection | None = None,
) -> int:
    """Create a new module entity under the given course.

    Args:
        group_id: The id of the group that will own the course.
        name: The name of the course.
        channel_id: Channel to associate the course with.
        order: Sort key, creation date will be used otherwise.
        connection: A connection object to use instead of creating a new one. Used for testing

    Returns: id of the created module.
    """
    con = connection or get_db()

    cur = con.cursor()

    group_id = cur.execute(
        "SELECT courseGroupId FROM course WHERE id = ?", (course_id,)
    ).fetchone()["courseGroupId"]

    cur.execute(
        "INSERT INTO module (courseGroupId, courseId, name, ord) VALUES (?, ?, ?, ?)",
        (group_id, course_id, name, order),
    )
    last_id = cur.lastrowid
    con.commit()

    return last_id


def create_entry(
    user_id: int, module_id: int, connection: sqlite3.Connection | None = None
) -> int:
    """Create a new check entry entity.

    Args:
        user_id: The id of the user.
        module_id: The id of the module to check.
        connection: A connection object to use instead of creating a new one. Used for testing

    Returns: id of the created entry.
    """
    con = connection or get_db()

    cur = con.cursor()

    cur.execute(
        "INSERT INTO checkEntry (userId, moduleId) VALUES (?, ?)",
        (user_id, module_id),
    )
    last_id = cur.lastrowid
    con.commit()

    return last_id


def get_all(
    table: str, connection: sqlite3.Connection | None = None
) -> list[sqlite3.Row]:
    """Fetch all rows in the given table.

    Args:
        table: The table to query.
        connection: A connection object to use instead of creating a new one. Used for testing
    """
    con = connection or get_db()

    return con.execute(f"SELECT * FROM {table}").fetchall()
