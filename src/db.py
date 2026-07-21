"""The interface to all db operations."""

import json
import os
import sqlite3

from .config import Config
from .utils import Status, path_from_app
from .utils import StatusType as ST

_db_path = ""  # set by init_db
_fixed_db_con = None


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    """Create a new connection object to db.

    Note: Run init_db once before calling this function.
    """
    global _fixed_db_con

    if _fixed_db_con:
        try:
            cur = _fixed_db_con.cursor()
            return _fixed_db_con
        except sqlite3.ProgrammingError as _:
            print(
                f"Fixed database connection has been closed incorrectly! Assuming it was intentional and unsetting the fixed con."
            )
            _fixed_db_con = None

    con = sqlite3.Connection(db_path or _db_path)
    con.row_factory = sqlite3.Row

    return con


def fix_connection(con: sqlite3.Connection | None) -> None:
    """Set a fixed connection object to be used by all database functions.

    Args:
        con: The database connection, None to unset and close the connection.
    """
    global _fixed_db_con

    if con is None and _fixed_db_con is not None:
        try:
            _fixed_db_con.close()
        except sqlite3.ProgrammingError as _:
            pass  # already closed
        _fixed_db_con = None
    else:
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


def create_group(guild_id: int, name: str) -> Status:
    """Create a new group entity with given name.

    Args:
        guild_id: The guild that owns this group.
        name: The name of the group.

    Returns: A Status object.
    """
    con = get_db()

    cur = con.cursor()

    group_exists = cur.execute(
        "SELECT * FROM courseGroup WHERE guildId = ? AND name = ?", (guild_id, name)
    ).fetchone()
    if group_exists:
        return Status(
            type=ST.WARNING,
            msg="Group already exists.",
            rowid=group_exists["id"],
        )

    cur.execute(
        "INSERT INTO courseGroup (guildId, name) VALUES (?, ?)", (guild_id, name)
    )
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
            ST.ERROR, msg="Such a group doesn't exist. Please create it first."
        )

    course_exists = cur.execute(
        "SELECT * FROM course WHERE courseGroupId = ? AND name = ?", (group_id, name)
    ).fetchone()
    if course_exists:
        return Status(
            type=ST.WARNING,
            msg="Course already exists in the group.",
            rowid=course_exists["id"],
        )

    if channel_id:
        channel_in_use = cur.execute(
            "SELECT name as courseName FROM course WHERE channelId = ?", (channel_id,)
        ).fetchone()
        if channel_in_use:
            return Status(
                ST.ERROR,
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
        course_id: The id of the course that will own the module.
        name: The name of the module.
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
            ST.ERROR, msg="Such a course doesn't exist. Please create it first."
        )

    module_exists = cur.execute(
        "SELECT * FROM module WHERE courseId = ? AND name = ?", (course_id, name)
    ).fetchone()
    if module_exists:
        return Status(
            type=ST.WARNING,
            msg="Module already exists in the course.",
            rowid=module_exists["id"],
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
            ST.ERROR, msg="Such a module doesn't exist. Please create it first."
        )

    entry_exists = cur.execute(
        "SELECT * FROM checkEntry WHERE userId = ? AND moduleId = ?",
        (user_id, module_id),
    ).fetchone()

    if entry_exists:
        return Status(ST.WARNING, msg="You have already checked this module.")

    cur.execute(
        "INSERT INTO checkEntry (userId, moduleId) VALUES (?, ?)",
        (user_id, module_id),
    )
    last_id = cur.lastrowid

    con.commit()

    return Status(msg=f"Checked **{module_exists['name']}**. Great job!", rowid=last_id)


def delete_entry(user_id: int, module_id: int) -> Status:
    """Delete a check entry.

    Args:
        user_id: The id of the user.
        module_id: The id of the module.

    Returns: A Status object.
    """
    con = get_db()

    cur = con.cursor()

    module = cur.execute(
        "SELECT name FROM module WHERE id = ?", (module_id,)
    ).fetchone()
    entry_exists = cur.execute(
        "SELECT id FROM checkEntry WHERE userId = ? AND moduleId = ?",
        (user_id, module_id),
    ).fetchone()

    if not entry_exists:
        return Status(ST.WARNING, msg="It's already not checked.")

    cur.execute(
        "DELETE FROM checkEntry WHERE userId = ? AND moduleId = ?",
        (user_id, module_id),
    )

    con.commit()

    return Status(msg=f"Unchecked module **{module['name']}**.")


def get_all(table: str) -> list[sqlite3.Row]:
    """Fetch all rows in the given table.

    Args:
        table: The table to query.
    """
    con = get_db()

    return con.execute(f"SELECT * FROM {table}").fetchall()


def get_modules_state(
    user_id, channel_id: int | None = None, checked_only=False
) -> list[sqlite3.Row]:
    """Fetch modules from the context of the current channel if possible.
    Note: if channel couldn't be deduced an extra `courseName` column is returned.

    Args:
        channel_id: Channel to derive the course from. If no course is linked to it, all modules (in all courses) are returned instead.
        checked_only: if True returns checked modules only otherwise return unchecked only.

    Returns: A sqlite3.Row object of the `module` table.
    """
    con = get_db()
    cur = con.cursor()
    course_linked = con.execute(
        "SELECT id FROM course WHERE channelId = ?", (channel_id,)
    ).fetchone()

    if course_linked:
        modules = cur.execute(
            f"SELECT id, name FROM module WHERE courseId = ? AND id {'' if checked_only else 'not '}in (SELECT id FROM checkEntry)",
            (course_linked["id"],),
        ).fetchall()
    else:
        # TODO: Actually filter based on checked_only
        modules = cur.execute(
            "SELECT module.id as id, module.name as name, course.name as courseName FROM module JOIN course ON module.courseId = course.id"
        ).fetchall()

    con.close()

    return modules


def deduce_course(channel_id: int) -> sqlite3.Row:
    """Try to deduce the course from the context of a channel

    Args:
        channel_id: The current channel the user is in.

    Returns: A sqlite3.Row object of the `course` table.
    """
    con = get_db()

    course_exists = con.execute(
        "SELECT * FROM course WHERE channelId = ?", (channel_id,)
    ).fetchone()

    return course_exists


def from_json(guild_id: int, data: str) -> Status:
    """Update the database to match or contain the given data.

    Args:
        guild_id: The guild that owns the group/s that might get created.
        data: The json data to load, e.g. `{"Group1": {"Course 1": {"channel_id": 12, "modules": {"Mod 5": {"order": 5}, "Mod 1": {}}}, "Course 2": {}}, "Group 2": {}}`
    """
    try:
        obj: dict[str, str] = json.loads(data)
    except json.decoder.JSONDecodeError as e:
        return Status(ST.ERROR, msg=f"Failed to parse JSON string. Error: {e}")

    for g in obj:
        status = create_group(guild_id, g)
        if status.type == ST.ERROR:
            return status

        g_id = status.rowid

        if not isinstance(obj, dict):
            continue

        g_data = obj[g]
        for course in g_data:
            course_data = None
            if isinstance(g_data, dict):
                course_data = g_data[course]

            status = create_course(
                g_id,
                course,
                course_data.get("channel_id") if course_data else None,
                course_data.get("order") if course_data else None,
            )
            if status.type == ST.ERROR:
                return status
            course_id = status.rowid

            if not course_data:
                continue

            modules = course_data.get("modules")
            if not modules:
                continue

            for m in modules:
                module_data = None
                if isinstance(modules, dict):
                    module_data = modules[m]

                create_module(
                    course_id, m, module_data.get("order") if module_data else None
                )
                if status.type == ST.ERROR:
                    return status

    status = Status(ST.INFO, msg="All done.")
    return status


def course_progress(user_id: int, course_id: int) -> Status:
    """List all modules in a course and their status for a user.

    Returns: a Status object"""
    con = get_db()
    course = con.execute(
        "SELECT name FROM course WHERE id = ?", (course_id,)
    ).fetchone()
    if not course:
        return Status(ST.ERROR, msg="Such a course doesn't exist.")

    course_modules = con.execute(
        "SELECT * FROM module WHERE courseId = ? ORDER BY ord, creationDate",
        (course_id,),
    ).fetchall()

    module_status = ""
    for module in course_modules:
        is_checked = con.execute(
            "SELECT * FROM checkEntry WHERE userId = ? AND moduleId = ?",
            (user_id, module["id"]),
        ).fetchone()

        module_status += f"### {'✅' if is_checked else '🟩'} {module['name']}\n"
    module_status = module_status.strip()

    return Status(ST.INFO, msg=module_status, title=course["name"])
