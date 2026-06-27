import pytest

from src import db as db
from src.config import Config

TEST_CONFIG = Config(db=":memory:")


def test_new_group():
    con = db.init_db(config=TEST_CONFIG)
    db.create_group("Math", connection=con)

    result = con.execute("SELECT * FROM courseGroup WHERE name = 'Math'").fetchone()
    assert result


def test_new_course():
    con = db.init_db(config=TEST_CONFIG)

    group_id = db.create_group("Math", connection=con).rowid
    db.create_course(group_id, "Algebra 1", connection=con)

    result = con.execute(
        "SELECT * FROM course WHERE name = 'Algebra 1' AND courseGroupId = ?",
        (group_id,),
    ).fetchone()
    assert result


def test_new_module():
    con = db.init_db(config=TEST_CONFIG)

    group_id = db.create_group("Math", connection=con).rowid
    course_id = db.create_course(group_id, "Algebra 1", connection=con).rowid
    db.create_module(course_id, "Lesson 1", connection=con)

    result = con.execute(
        "SELECT * FROM module WHERE name = 'Lesson 1' AND courseGroupId = ? AND courseId = ?",
        (group_id, course_id),
    ).fetchone()
    assert result


def test_new_entry():
    con = db.init_db(config=TEST_CONFIG)

    group_id = db.create_group("Math", connection=con).rowid
    course_id = db.create_course(group_id, "Algebra 1", connection=con).rowid
    module_id = db.create_module(course_id, "Lesson 1", connection=con).rowid
    db.create_entry(1, module_id, connection=con)

    result = con.execute(
        "SELECT * FROM checkEntry WHERE userId = 1 AND moduleId = ?",
        (module_id,),
    ).fetchone()
    assert result
