"""The interface to all db operations."""

import os
import sqlite3

from .config import Config
from .utils import Status, StatusType, path_from_app

_db_path = ""  # set by init_db
_fixed_db_con = None


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    """Create a new connection object to db.

    Note: Run init_db once before calling this function.
    """
    if _fixed_db_con:
        return _fixed_db_con

    con = sqlite3.Connection(db_path or _db_path)
    con.row_factory = sqlite3.Row

    return con


def fix_connection(con: sqlite3.Connection | None) -> None:
    """Set a fixed connection object to be used by all database functions.

    Args:
        con: The database connection, None to unset.
    """
    global _fixed_db_con

    _fixed_db_con = con


def init_db(config: Config) -> sqlite3.Connection:
    """Execute the database schema and set the required pragmas."""
    global _db_path

    dirname = os.path.dirname(config.db)
    if dirname and not os.path.exists(dirname):
        os.mkdir(dirname)
    _db_path = config.db

    con = get_db()
    cur = con.cursor()
    cur.execute("PRAGMA FOREIGN_KEYS = ON")

    with open(path_from_app("schema.sql"), "r") as f:
        cur.executescript(f.read())

    con.commit()

    return con


def create_group(name: str) -> Status:
    """Create a new group entity with given name.

    Args:
        name: The name of the group.

    Returns: A Status object.
    """
    con = get_db()

    cur = con.cursor()
    cur.execute("INSERT INTO courseGroup (name) VALUES (?)", (name,))
    last_id = cur.lastrowid

    con.commit()

    return Status(msg=f"Group: **{name}** created.", rowid=last_id)


def create_course(
    group_id: int,
    name: str,
    channel_id: int | None = None,
    order: int | None = None,
) -> Status:
    """Create a new course entity under the given group.

    Args:
        group_id: The id of the group that will own the course.
        name: The name of the course.
        channel_id: Channel to associate the course with.
        order: Sort key, creation date will be used otherwise.

    Returns: A Status object.
    """
    con = get_db()

    cur = con.cursor()

    group_exists = cur.execute(
        "SELECT name as groupName FROM courseGroup WHERE id = ?", (group_id,)
    ).fetchone()
    if not group_exists:
        return Status(
            StatusType.ERROR, msg="Such a group doesn't exist. Please create it first."
        )

    if channel_id:
        channel_in_use = cur.execute(
            "SELECT name as courseName FROM course WHERE channelId = ?", (channel_id,)
        ).fetchone()
        if channel_in_use:
            return Status(
                StatusType.ERROR,
                msg=f"This channel is already in use by **{channel_in_use['courseName']}**.",
            )

    cur.execute(
        "INSERT INTO course (courseGroupId, name, channelId, ord) VALUES (?, ?, ?, ?)",
        (group_id, name, channel_id, order),
    )
    last_id = cur.lastrowid

    con.commit()

    return Status(
        msg=f"Created course **{name}** under {group_exists['groupName']}.",
        rowid=last_id,
    )


def create_module(
    course_id: int,
    name: str,
    order: int | None = None,
) -> Status:
    """Create a new module entity under the given course.

    Args:
        group_id: The id of the group that will own the course.
        name: The name of the course.
        channel_id: Channel to associate the course with.
        order: Sort key, creation date will be used otherwise.

    Returns: A Status object.
    """
    con = get_db()

    cur = con.cursor()

    course_exists = cur.execute(
        "SELECT courseGroupId as groupId, name FROM course WHERE id = ?", (course_id,)
    ).fetchone()

    if not course_exists:
        return Status(
            StatusType.ERROR, msg="Such a course doesn't exist. Please create it first."
        )

    cur.execute(
        "INSERT INTO module (courseGroupId, courseId, name, ord) VALUES (?, ?, ?, ?)",
        (course_exists["groupId"], course_id, name, order),
    )
    last_id = cur.lastrowid

    con.commit()

    return Status(
        msg=f"Module {name} created under {course_exists['name']}", rowid=last_id
    )


def create_entry(user_id: int, module_id: int) -> Status:
    """Create a new check entry entity.

    Args:
        user_id: The id of the user.
        module_id: The id of the module to check.

    Returns: A Status object.
    """
    con = get_db()

    cur = con.cursor()

    module_exists = cur.execute(
        "SELECT name FROM module WHERE id = ?", (module_id,)
    ).fetchone()

    if not module_exists:
        return Status(
            StatusType.ERROR, msg="Such a module doesn't exist. Please create it first."
        )

    entry_exists = cur.execute(
        "SELECT * FROM checkEntry WHERE userId = ? AND moduleId = ?",
        (user_id, module_id),
    ).fetchone()

    if entry_exists:
        return Status(
            StatusType.ERROR, msg="You have already checked this module before."
        )

    cur.execute(
        "INSERT INTO checkEntry (userId, moduleId) VALUES (?, ?)",
        (user_id, module_id),
    )
    last_id = cur.lastrowid

    con.commit()

    return Status(msg=f"Checked **{module_exists['name']}**. Great job!", rowid=last_id)


def get_all(table: str) -> list[sqlite3.Row]:
    """Fetch all rows in the given table.

    Args:
        table: The table to query.
    """
    con = get_db()

    return con.execute(f"SELECT * FROM {table}").fetchall()


def get_modules(user_id, channel_id: int | None = None) -> list[sqlite3.Row]:
    """Fetch unchecked modules from the context of the current channel if possible.

    Args:
        channel_id: Channel to derive the course from. If no course is linked to it, all modules (in all courses) are returned instead.
    """
    con = get_db()
    cur = con.cursor()
    course_linked = con.execute(
        "SELECT id FROM course WHERE channelId = ?", (channel_id,)
    ).fetchone()

    if course_linked:
        modules = cur.execute(
            "SELECT id, name FROM module WHERE courseId = ? AND id not in (SELECT id FROM checkEntry)",
            (course_linked["id"],),
        ).fetchall()
    else:
        modules = cur.execute(
            "SELECT module.id as id, module.name as name, course.name as courseName FROM module JOIN course ON module.courseId = course.id"
        ).fetchall()

    con.close()

    return modules


def course_progress(user_id: int, course_id: int) -> str:
    """List all modules in a course and show which are done"""
    con = get_db()
    course_modules = con.execute(
        "SELECT * FROM module WHERE courseId = ?", (course_id,)
    ).fetchall()

    output = ""

    for module in course_modules:
        is_checked = con.execute(
            "SELECT * FROM checkEntry WHERE userId = ? AND moduleId = ?",
            (user_id, module["id"]),
        ).fetchone()

        output += "✅" if is_checked else "◆"
        output += f" {module['name']}\n"

    return output


def deduce_course(channel_id: int) -> sqlite3.Row:
    """Try to deduce the course from the context of a channel

    Args:
        channel_id: The current channel the user is in.
    """
    con = get_db()

    course_exists = con.execute(
        "SELECT * FROM course WHERE channelId = ?", (channel_id,)
    ).fetchone()

    return course_exists
