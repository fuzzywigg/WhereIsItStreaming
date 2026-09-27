import sqlite3

import db


def test_format_genres_empty():
    assert db.format_genres([]) == " - "


def test_format_genres_joins_names():
    genres = [{"name": "Action"}, {"name": "Comedy"}]
    assert db.format_genres(genres) == " - Action - Comedy - "


def test_should_include_cast_boundary():
    assert db.should_include_cast(0) is True
    assert db.should_include_cast(8) is True
    assert db.should_include_cast(9) is False


def test_should_include_crew_directing_and_writing_only():
    assert db.should_include_crew("Directing") is True
    assert db.should_include_crew("Writing") is True
    assert db.should_include_crew("Camera") is False
    assert db.should_include_crew("Sound") is False


def test_init_schema_creates_expected_tables(tmp_path):
    path = str(tmp_path / "schema.db")
    conn = sqlite3.connect(path)
    db.init_schema(conn)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    conn.close()
    assert {
        "users",
        "liked",
        "viewed",
        "searched",
        "movies",
        "casts",
        "crews",
        "ratings",
    }.issubset(tables)


def test_init_schema_is_idempotent(tmp_path):
    path = str(tmp_path / "schema2.db")
    conn = sqlite3.connect(path)
    db.init_schema(conn)
    db.init_schema(conn)
    count = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0]
    conn.close()
    assert count >= 8
