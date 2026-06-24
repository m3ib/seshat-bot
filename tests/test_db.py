import pytest

from src import db as db


def test_new_group():
    con = db.init_db(testing=True)
    db.create_group("Math", 0, connection=con)

    result = con.execute("SELECT * FROM courseGroup WHERE name = 'Math'").fetchone()
    assert result


def test_new_course():
    con = db.init_db(testing=True)

    group_id = db.create_group("Math", 0, connection=con)
    db.create_course(group_id, "Algebra 1", connection=con)

    result = con.execute(
        "SELECT * FROM course WHERE name = 'Algebra 1' AND courseGroupId = ?",
        (group_id,),
    ).fetchone()
    assert result


def test_new_module():
    con = db.init_db(testing=True)

    group_id = db.create_group("Math", 0, connection=con)
    course_id = db.create_course(group_id, "Algebra 1", connection=con)
    db.create_module(course_id, "Lesson 1", connection=con)

    result = con.execute(
        "SELECT * FROM module WHERE name = 'Lesson 1' AND courseGroupId = ? AND courseId = ?",
        (group_id, course_id),
    ).fetchone()
    assert result


def test_new_entry():
    con = db.init_db(testing=True)

    group_id = db.create_group("Math", 0, connection=con)
    course_id = db.create_course(group_id, "Algebra 1", connection=con)
    module_id = db.create_module(course_id, "Lesson 1", connection=con)
    db.create_entry(1, module_id, connection=con)

    result = con.execute(
        "SELECT * FROM checkEntry WHERE userId = 1 AND moduleId = ?",
        (module_id,),
    ).fetchone()
    assert result
