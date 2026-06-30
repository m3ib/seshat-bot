import pytest

from src import db as db
from src.config import Config
from src.utils import StatusType

TEST_CONFIG = Config(db=":memory:")


def test_new_group():
    con = db.init_db(config=TEST_CONFIG)
    db.fix_connection(con)
    db.create_group("Math")

    result = con.execute("SELECT * FROM courseGroup WHERE name = 'Math'").fetchone()
    assert result


def test_new_course():
    con = db.init_db(config=TEST_CONFIG)

    db.fix_connection(con)
    group_id = db.create_group("Math").rowid

    status = db.create_course(group_id, "Algebra 1")

    result = con.execute(
        "SELECT * FROM course WHERE name = 'Algebra 1' AND courseGroupId = ?",
        (group_id,),
    ).fetchone()
    assert status.type == StatusType.INFO
    assert result


def test_new_course_invalid():
    con = db.init_db(config=TEST_CONFIG)

    db.fix_connection(con)
    group_id = db.create_group("Math").rowid

    status = db.create_course(group_id + 1, "Algebra 1")

    result = con.execute(
        "SELECT * FROM course WHERE name = 'Algebra 1' AND courseGroupId = ?",
        (group_id,),
    ).fetchone()
    assert status.type == StatusType.ERROR
    assert not result


def test_new_module():
    con = db.init_db(config=TEST_CONFIG)

    db.fix_connection(con)
    group_id = db.create_group("Math").rowid
    course_id = db.create_course(group_id, "Algebra 1").rowid

    status = db.create_module(course_id, "Lesson 1")

    result = con.execute(
        "SELECT * FROM module WHERE name = 'Lesson 1' AND courseGroupId = ? AND courseId = ?",
        (group_id, course_id),
    ).fetchone()
    assert status.type == StatusType.INFO
    assert result


def test_new_module_invalid():
    con = db.init_db(config=TEST_CONFIG)

    db.fix_connection(con)
    group_id = db.create_group("Math").rowid
    course_id = db.create_course(group_id, "Algebra 1").rowid

    status = db.create_module(course_id + 1, "Lesson 1")

    result = con.execute(
        "SELECT * FROM module WHERE name = 'Lesson 1' AND courseGroupId = ? AND courseId = ?",
        (group_id, course_id),
    ).fetchone()
    assert status.type == StatusType.ERROR
    assert not result


def test_new_entry():
    con = db.init_db(config=TEST_CONFIG)

    db.fix_connection(con)
    group_id = db.create_group("Math").rowid
    course_id = db.create_course(group_id, "Algebra 1").rowid
    module_id = db.create_module(course_id, "Lesson 1").rowid

    status = db.create_entry(1, module_id)

    result = con.execute(
        "SELECT * FROM checkEntry WHERE userId = 1 AND moduleId = ?",
        (module_id,),
    ).fetchone()
    assert status.type == StatusType.INFO
    assert result


def test_new_entry_invalid():
    con = db.init_db(config=TEST_CONFIG)

    db.fix_connection(con)
    group_id = db.create_group("Math").rowid
    course_id = db.create_course(group_id, "Algebra 1").rowid
    module_id = db.create_module(course_id, "Lesson 1").rowid

    status = db.create_entry(1, module_id + 1)

    result = con.execute(
        "SELECT * FROM checkEntry WHERE userId = 1 AND moduleId = ?",
        (module_id,),
    ).fetchone()
    assert status.type == StatusType.ERROR
    assert not result


def test_new_entry_duplicate():
    con = db.init_db(config=TEST_CONFIG)

    db.fix_connection(con)
    group_id = db.create_group("Math").rowid
    course_id = db.create_course(group_id, "Algebra 1").rowid
    module_id = db.create_module(course_id, "Lesson 1").rowid

    first_status = db.create_entry(1, module_id)
    second_status = db.create_entry(1, module_id)

    result = con.execute(
        "SELECT * FROM checkEntry WHERE userId = 1 AND moduleId = ?",
        (module_id,),
    ).fetchall()
    assert first_status.type == StatusType.INFO
    assert second_status.type == StatusType.ERROR
    assert len(result) == 1
