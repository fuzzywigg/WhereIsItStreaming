import csv
import sqlite3

import db


def test_format_genres_empty():
    assert db.format_genres([]) == " - "


def test_format_genres_single():
    assert db.format_genres([{"name": "Horror"}]) == " - Horror - "


def test_format_genres_joins_names():
    genres = [{"name": "Action"}, {"name": "Comedy"}]
    assert db.format_genres(genres) == " - Action - Comedy - "


def test_should_include_cast_boundary():
    assert db.should_include_cast(0) is True
    assert db.should_include_cast(8) is True
    assert db.should_include_cast(9) is False
    assert db.should_include_cast(-1) is True


def test_should_include_crew_directing_and_writing_only():
    assert db.should_include_crew("Directing") is True
    assert db.should_include_crew("Writing") is True
    assert db.should_include_crew("Camera") is False
    assert db.should_include_crew("Sound") is False
    assert db.should_include_crew("directing") is False


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


def _write_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_load_from_csv_filters_cast_crew_and_skips_bad_ids(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_path = str(tmp_path / "loaded.db")

    _write_csv(
        data_dir / "movies_metadata.csv",
        [
            "id",
            "imdb_id",
            "overview",
            "genres",
            "title",
            "release_date",
            "homepage",
            "poster_path",
            "tagline",
        ],
        [
            {
                "id": "101",
                "imdb_id": "tt101",
                "overview": "A film",
                "genres": "[{'name': 'Action'}, {'name': 'Drama'}]",
                "title": "Loaded Movie",
                "release_date": "1999-01-01",
                "homepage": "",
                "poster_path": "/p.jpg",
                "tagline": "Go",
            },
            {
                "id": "not-an-int",
                "imdb_id": "ttbad",
                "overview": "skip me",
                "genres": "[]",
                "title": "Bad Id",
                "release_date": "",
                "homepage": "",
                "poster_path": "",
                "tagline": "",
            },
        ],
    )
    _write_csv(
        data_dir / "credits.csv",
        ["id", "cast", "crew"],
        [
            {
                "id": "101",
                "cast": (
                    "[{'order': 0, 'character': 'Lead', 'name': 'Ada', "
                    "'profile_path': '/ada.jpg'}, "
                    "{'order': 9, 'character': 'Extra', 'name': 'Bob', "
                    "'profile_path': '/bob.jpg'}]"
                ),
                "crew": (
                    "[{'department': 'Directing', 'name': 'Dir'}, "
                    "{'department': 'Camera', 'name': 'Cam'}, "
                    "{'department': 'Writing', 'name': 'Write'}]"
                ),
            }
        ],
    )
    _write_csv(
        data_dir / "ratings.csv",
        ["movieId", "rating"],
        [
            {"movieId": "101", "rating": "4.0"},
            {"movieId": "101", "rating": "5.0"},
        ],
    )

    db.load_from_csv(db_path=db_path, data_dir=str(data_dir))

    conn = sqlite3.connect(db_path)
    movies = conn.execute(
        "SELECT id, title, genres FROM movies ORDER BY id"
    ).fetchall()
    cast_names = {
        row[0]
        for row in conn.execute("SELECT name FROM casts WHERE id = 101")
    }
    crew_roles = {
        row[0]
        for row in conn.execute("SELECT role FROM crews WHERE id = 101")
    }
    rating_count = conn.execute(
        "SELECT COUNT(*) FROM ratings WHERE id = 101"
    ).fetchone()[0]
    conn.close()

    assert movies == [(101, "Loaded Movie", " - Action - Drama - ")]
    assert cast_names == {"Ada"}
    assert "Bob" not in cast_names
    assert crew_roles == {"Directing", "Writing"}
    assert "Camera" not in crew_roles
    assert rating_count == 2
