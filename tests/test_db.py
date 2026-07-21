import pytest

from src import db as db
from src.config import Config
from src.utils import StatusType

TEST_CONFIG = Config(db=":memory:")


class TestCreateGroup:
    def test_new(self):
        con = db.init_db(config=TEST_CONFIG)
        db.fix_connection(con)
        status = db.create_group(1, "Math")

        result = con.execute("SELECT * FROM courseGroup WHERE name = 'Math'").fetchone()
        db.fix_connection(None)

        assert status.type == StatusType.INFO
        assert result

    def test_duplicate(self):
        con = db.init_db(config=TEST_CONFIG)
        db.fix_connection(con)
        first_status = db.create_group(1, "Math")
        second_status = db.create_group(1, "Math")

        count = con.execute(
            "SELECT COUNT(*) as c FROM courseGroup WHERE name = 'Math'"
        ).fetchone()["c"]
        db.fix_connection(None)

        assert first_status.type == StatusType.INFO
        assert second_status.type == StatusType.WARNING
        assert count == 1


class TestCreateCourse:
    def test_new(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        group_id = db.create_group(1, "Math").rowid

        status = db.create_course(group_id, "Algebra 1")

        result = con.execute(
            "SELECT * FROM course WHERE name = 'Algebra 1' AND courseGroupId = ?",
            (group_id,),
        ).fetchone()
        db.fix_connection(None)

        assert status.type == StatusType.INFO
        assert result

    def test_duplicate(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        group_id = db.create_group(1, "Math").rowid

        first_status = db.create_course(group_id, "Algebra 1")
        second_status = db.create_course(group_id, "Algebra 1")

        count = con.execute(
            "SELECT COUNT(*) as c FROM course WHERE name = 'Algebra 1' AND courseGroupId = ?",
            (group_id,),
        ).fetchone()["c"]
        db.fix_connection(None)

        assert first_status.type == StatusType.INFO
        assert second_status.type == StatusType.WARNING
        assert count == 1

    def test_invalid(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        group_id = db.create_group(1, "Math").rowid

        status = db.create_course(group_id + 1, "Algebra 1")

        result = con.execute(
            "SELECT * FROM course WHERE name = 'Algebra 1' AND courseGroupId = ?",
            (group_id,),
        ).fetchone()
        db.fix_connection(None)

        assert status.type == StatusType.ERROR
        assert not result


class TestModule:
    def test_new(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        group_id = db.create_group(1, "Math").rowid
        course_id = db.create_course(group_id, "Algebra 1").rowid

        status = db.create_module(course_id, "Lesson 1")

        result = con.execute(
            "SELECT * FROM module WHERE name = 'Lesson 1' AND courseGroupId = ? AND courseId = ?",
            (group_id, course_id),
        ).fetchone()
        db.fix_connection(None)

        assert status.type == StatusType.INFO
        assert result

    def test_duplicate(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        group_id = db.create_group(1, "Math").rowid
        course_id = db.create_course(group_id, "Algebra 1").rowid

        first_status = db.create_module(course_id, "Lesson 1")
        second_status = db.create_module(course_id, "Lesson 1")

        count = con.execute(
            "SELECT COUNT(*) as c FROM module WHERE name = 'Lesson 1' AND courseGroupId = ? AND courseId = ?",
            (group_id, course_id),
        ).fetchone()["c"]
        db.fix_connection(None)

        assert first_status.type == StatusType.INFO
        assert second_status.type == StatusType.WARNING
        assert count == 1

    def test_invalid(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        group_id = db.create_group(1, "Math").rowid
        course_id = db.create_course(group_id, "Algebra 1").rowid

        status = db.create_module(course_id + 1, "Lesson 1")

        result = con.execute(
            "SELECT * FROM module WHERE name = 'Lesson 1' AND courseGroupId = ? AND courseId = ?",
            (group_id, course_id),
        ).fetchone()
        db.fix_connection(None)

        assert status.type == StatusType.ERROR
        assert not result


class TestCreateEntry:
    def test_new(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        group_id = db.create_group(1, "Math").rowid
        course_id = db.create_course(group_id, "Algebra 1").rowid
        module_id = db.create_module(course_id, "Lesson 1").rowid

        status = db.create_entry(1, module_id)

        result = con.execute(
            "SELECT * FROM checkEntry WHERE userId = 1 AND moduleId = ?",
            (module_id,),
        ).fetchone()
        db.fix_connection(None)

        assert status.type == StatusType.INFO
        assert result

    def test_invalid(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        group_id = db.create_group(1, "Math").rowid
        course_id = db.create_course(group_id, "Algebra 1").rowid
        module_id = db.create_module(course_id, "Lesson 1").rowid

        status = db.create_entry(1, module_id + 1)

        result = con.execute(
            "SELECT * FROM checkEntry WHERE userId = 1 AND moduleId = ?",
            (module_id,),
        ).fetchone()
        db.fix_connection(None)

        assert status.type == StatusType.ERROR
        assert not result

    def test_duplicate(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        group_id = db.create_group(1, "Math").rowid
        course_id = db.create_course(group_id, "Algebra 1").rowid
        module_id = db.create_module(course_id, "Lesson 1").rowid

        first_status = db.create_entry(1, module_id)
        second_status = db.create_entry(1, module_id)

        result = con.execute(
            "SELECT * FROM checkEntry WHERE userId = 1 AND moduleId = ?",
            (module_id,),
        ).fetchall()
        db.fix_connection(None)

        assert first_status.type == StatusType.INFO
        assert second_status.type == StatusType.WARNING
        assert len(result) == 1


class TestFromJson:
    def test_group_list(self):
        con = db.init_db(config=TEST_CONFIG)

        g_pre = con.execute("SELECT * FROM courseGroup").fetchall()
        g_count_pre = con.execute("SELECT COUNT(*) as c FROM courseGroup").fetchone()[
            "c"
        ]

        if g_count_pre > 0:
            raise RuntimeError(
                f"The database isn't clean! {g_count_pre} groups already exist! first group: {g_pre[0]['name']}[{g_pre[0]['id']}]"
            )

        db.fix_connection(con)
        status = db.from_json(1, '["Group 1", "Group 2", "Group 3"]')

        g_count = con.execute("SELECT COUNT(*) as c FROM courseGroup").fetchone()["c"]
        correct_group = con.execute(
            "SELECT * FROM courseGroup WHERE name = ?", ("Group 2",)
        ).fetchall()
        db.fix_connection(None)

        assert status.type == StatusType.INFO
        assert g_count == 3
        assert correct_group

    def test_course_list(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        status = db.from_json(
            1, '{"Group 1": ["Course 1", "Course 2", "Course 3"], "Group 2": []}'
        )

        g_count = con.execute("SELECT COUNT(*) as c FROM courseGroup").fetchone()["c"]
        c_count = con.execute("SELECT COUNT(*) as c FROM course").fetchone()["c"]
        correct_course = con.execute(
            "SELECT * FROM course WHERE name = ? AND courseGroupId = ?", ("Course 2", 1)
        ).fetchall()
        db.fix_connection(None)

        assert status.type == StatusType.INFO
        assert g_count == 2
        assert c_count == 3
        assert correct_course

    def test_course_attributes(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        status = db.from_json(
            1,
            '{"Group 1": {"Course 1": {"channel_id": 12, "order": 2}}, "Group 2": []}',
        )

        g_count = con.execute("SELECT COUNT(*) as c FROM courseGroup").fetchone()["c"]
        correct_course = con.execute(
            "SELECT * FROM course WHERE name = ? AND courseGroupId = ? AND channelId = ? AND ord = ?",
            ("Course 1", 1, 12, 2),
        ).fetchone()
        db.fix_connection(None)

        assert status.type == StatusType.INFO
        assert g_count == 2
        assert correct_course

    def test_module_list(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        status = db.from_json(
            1,
            '{"Group 1": {"Course 1": {"channel_id": 12, "modules": ["Mod1", "Mod2", "Mod3"]}}, "Group 2": []}',
        )

        m_count = con.execute("SELECT COUNT(*) as c FROM module").fetchone()["c"]
        correct_module = con.execute(
            "SELECT * FROM module WHERE name = ? AND courseId = ?",
            ("Mod2", 1),
        ).fetchall()
        db.fix_connection(None)

        assert status.type == StatusType.INFO
        assert m_count == 3
        assert correct_module

    def test_module_attributes(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)
        status = db.from_json(
            1,
            '{"Group 1": {"Course 1": {"channel_id": 12, "modules": {"Mod1": {}, "Mod2": {"order": 5}, "Mod3": {}}}}, "Group 2": []}',
        )

        m_count = con.execute("SELECT COUNT(*) as c FROM module").fetchone()["c"]
        correct_module = con.execute(
            "SELECT * FROM module WHERE name = ? AND courseId = ? AND ord = ?",
            ("Mod2", 1, 5),
        ).fetchone()
        db.fix_connection(None)

        assert status.type == StatusType.INFO
        assert m_count == 3
        assert correct_module

    def test_incremental(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)

        g_id = db.create_group(1, "Group 1").rowid
        c_id = db.create_course(g_id, "Course 1").rowid

        status = db.from_json(
            1,
            '{"Group 1": {"Course 1": {"modules": ["Mod1", "Mod2", "Mod3"]}}, "Group 2": []}',
        )

        m_count = con.execute("SELECT COUNT(*) as c FROM module").fetchone()["c"]
        correct_module = con.execute(
            "SELECT * FROM module WHERE name = ? AND courseId = ?",
            ("Mod2", 1),
        ).fetchall()
        db.fix_connection(None)

        assert status.type == StatusType.INFO
        assert m_count == 3
        assert correct_module

    def test_invalid_json(self):
        con = db.init_db(config=TEST_CONFIG)

        db.fix_connection(con)

        status = db.from_json(
            1,
            '{"Group 1: {"Course 1": {"modules": ["Mod1", "Mod2", "Mod3"]}}, "Group 2": []}',  # unpaired double-quote
        )

        g_count = con.execute("SELECT COUNT(*) as c FROM courseGroup").fetchone()["c"]
        db.fix_connection(None)

        assert status.type == StatusType.ERROR
        assert g_count == 0
