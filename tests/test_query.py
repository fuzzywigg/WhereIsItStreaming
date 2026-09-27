import os
import sqlite3

import db
import query


def test_return_one_film(temp_db):
    films = query.returnOneFilm(1)
    assert len(films) == 1
    assert films[0]["title"] == "The Arrival"
    assert films[0]["IMDBid"] == "tt0000001"
    assert films[0]["poster_path"] == "/poster1.jpg"


def test_return_one_film_maps_all_fields(temp_db):
    film = query.returnOneFilm(3)[0]
    assert film == {
        "id": 3,
        "IMDBid": "tt0000003",
        "overview": "Another drama",
        "genres": " - Drama - Action - ",
        "title": "Arrival Part Two",
        "release_date": "2020-06-01",
        "homepage": "https://example.com",
        "poster_path": "/poster3.jpg",
        "tagline": "Again",
    }


def test_return_one_film_missing(temp_db):
    assert query.returnOneFilm(999) == []


def test_return_film_prefix_match(temp_db):
    films = query.returnFilm("Arrival")
    titles = {f["title"] for f in films}
    assert "The Arrival" not in titles  # LIKE 'Arrival%' — title starts with Arrival
    assert "Arrival Part Two" in titles


def test_return_film_the_prefix(temp_db):
    films = query.returnFilm("The")
    assert any(f["title"] == "The Arrival" for f in films)


def test_return_film_no_match(temp_db):
    assert query.returnFilm("ZzzNoSuchTitle") == []


def test_return_film_empty_prefix_matches_all(temp_db):
    # Historical LIKE '{}%' with empty title matches every row.
    films = query.returnFilm("")
    assert {f["id"] for f in films} == {1, 2, 3}


def test_return_cast(temp_db):
    cast = query.returnCast(1)
    names = {c["name"] for c in cast}
    assert names == {"Ada Lovelace", "Grace Hopper"}
    assert cast[0]["character"]


def test_return_cast_missing_movie(temp_db):
    assert query.returnCast(999) == []


def test_return_cast_movie_without_cast(temp_db):
    assert query.returnCast(2) == []


def test_return_crew(temp_db):
    crew = query.returnCrew(1)
    by_role = {c["role"]: c["name"] for c in crew}
    assert by_role["Directing"] == "Alice Director"
    assert by_role["Writing"] == "Bob Writer"


def test_return_crew_missing_movie(temp_db):
    assert query.returnCrew(999) == []


def test_return_ratings_average(temp_db):
    ratings = query.returnRatings(1)
    assert len(ratings) == 1
    assert ratings[0]["rating"] == 4.5


def test_return_ratings_rounds_to_three_decimals(temp_db):
    conn = sqlite3.connect(temp_db)
    conn.execute("INSERT INTO ratings(id, rating) VALUES(?,?)", (3, 1.0))
    conn.execute("INSERT INTO ratings(id, rating) VALUES(?,?)", (3, 2.0))
    conn.execute("INSERT INTO ratings(id, rating) VALUES(?,?)", (3, 2.0))
    conn.commit()
    conn.close()
    ratings = query.returnRatings(3)
    assert len(ratings) == 1
    assert ratings[0]["rating"] == 1.667


def test_return_ratings_none(temp_db):
    assert query.returnRatings(2) == []


def test_random_movies_skips_empty_poster_and_caps(temp_db):
    films = query.randomMovies()
    assert all(f["poster_path"] for f in films)
    assert len(films) <= 20
    # seed has two movies with posters
    assert len(films) == 2


def test_random_movies_empty_when_all_posters_blank(tmp_path):
    path = str(tmp_path / "blank_posters.db")
    conn = sqlite3.connect(path)
    db.init_schema(conn)
    conn.execute(
        """INSERT INTO movies(id, imdb_id, overview, genres, title, release_date,
           homepage, poster_path, tagline)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (1, "tt1", "x", " - ", "No Art", "2000-01-01", "", "", ""),
    )
    conn.commit()
    conn.close()

    previous = query.get_db_path()
    query.set_db_path(path)
    try:
        assert query.randomMovies() == []
    finally:
        query.set_db_path(previous)


def test_insert_liked(temp_db):
    query.insert(10, 1, "liked")
    conn = sqlite3.connect(temp_db)
    row = conn.execute(
        "SELECT movieid, userid FROM liked WHERE userid = 10"
    ).fetchone()
    conn.close()
    assert row == (1, 10)


def test_insert_viewed_and_searched(temp_db):
    query.insert(10, 2, "viewed")
    query.insert(10, 3, "searched")
    conn = sqlite3.connect(temp_db)
    viewed = conn.execute(
        "SELECT movieid, userid FROM viewed"
    ).fetchall()
    searched = conn.execute(
        "SELECT movieid, userid FROM searched"
    ).fetchall()
    conn.close()
    assert viewed == [(2, 10)]
    assert searched == [(3, 10)]


def test_set_db_path_roundtrip(temp_db):
    assert query.get_db_path() == temp_db


def test_set_db_path_switches_queries(tmp_path):
    path_a = str(tmp_path / "a.db")
    path_b = str(tmp_path / "b.db")
    for path, title in ((path_a, "Alpha"), (path_b, "Beta")):
        conn = sqlite3.connect(path)
        db.init_schema(conn)
        conn.execute(
            """INSERT INTO movies(id, imdb_id, overview, genres, title, release_date,
               homepage, poster_path, tagline)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (1, "tt1", "o", " - ", title, "2000-01-01", "", "/p.jpg", ""),
        )
        conn.commit()
        conn.close()

    previous = query.get_db_path()
    try:
        query.set_db_path(path_a)
        assert query.returnOneFilm(1)[0]["title"] == "Alpha"
        query.set_db_path(path_b)
        assert query.returnOneFilm(1)[0]["title"] == "Beta"
        assert query.get_db_path() == path_b
    finally:
        query.set_db_path(previous)
        os.environ.pop("MOVIES_DB_PATH", None)
