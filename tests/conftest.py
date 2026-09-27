import os
import sqlite3

import pytest

import db
import query


@pytest.fixture
def temp_db(tmp_path):
    """Fresh SQLite DB with schema + a few rows; points query helpers at it."""
    path = str(tmp_path / "test_movies.db")
    conn = sqlite3.connect(path)
    db.init_schema(conn)

    conn.execute(
        """INSERT INTO movies(id, imdb_id, overview, genres, title, release_date,
           homepage, poster_path, tagline)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (1, "tt0000001", "A silent film", " - Drama - ", "The Arrival",
         "1895-01-01", "", "/poster1.jpg", "First light"),
    )
    conn.execute(
        """INSERT INTO movies(id, imdb_id, overview, genres, title, release_date,
           homepage, poster_path, tagline)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (2, "tt0000002", "No art", " - Comedy - ", "Blank Slate",
         "2000-01-01", "", "", ""),
    )
    conn.execute(
        """INSERT INTO movies(id, imdb_id, overview, genres, title, release_date,
           homepage, poster_path, tagline)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (3, "tt0000003", "Another drama", " - Drama - Action - ", "Arrival Part Two",
         "2020-06-01", "https://example.com", "/poster3.jpg", "Again"),
    )
    conn.execute(
        "INSERT INTO casts(id, character, name, profile_path) VALUES(?,?,?,?)",
        (1, "Traveler", "Ada Lovelace", "/ada.jpg"),
    )
    conn.execute(
        "INSERT INTO casts(id, character, name, profile_path) VALUES(?,?,?,?)",
        (1, "Host", "Grace Hopper", "/grace.jpg"),
    )
    conn.execute(
        "INSERT INTO crews(id, name, role) VALUES(?,?,?)",
        (1, "Alice Director", "Directing"),
    )
    conn.execute(
        "INSERT INTO crews(id, name, role) VALUES(?,?,?)",
        (1, "Bob Writer", "Writing"),
    )
    conn.execute("INSERT INTO ratings(id, rating) VALUES(?,?)", (1, 4.0))
    conn.execute("INSERT INTO ratings(id, rating) VALUES(?,?)", (1, 5.0))
    conn.execute(
        "INSERT INTO users(id, username, email, password) VALUES(?,?,?,?)",
        (10, "tester", "t@example.com", "hashed"),
    )
    conn.commit()
    conn.close()

    previous = query.get_db_path()
    query.set_db_path(path)
    os.environ["MOVIES_DB_PATH"] = path
    yield path
    query.set_db_path(previous)
    os.environ.pop("MOVIES_DB_PATH", None)
