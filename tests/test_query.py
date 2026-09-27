import sqlite3

import query


def test_return_one_film(temp_db):
    films = query.returnOneFilm(1)
    assert len(films) == 1
    assert films[0]["title"] == "The Arrival"
    assert films[0]["IMDBid"] == "tt0000001"
    assert films[0]["poster_path"] == "/poster1.jpg"


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


def test_return_cast(temp_db):
    cast = query.returnCast(1)
    names = {c["name"] for c in cast}
    assert names == {"Ada Lovelace", "Grace Hopper"}
    assert cast[0]["character"]


def test_return_crew(temp_db):
    crew = query.returnCrew(1)
    by_role = {c["role"]: c["name"] for c in crew}
    assert by_role["Directing"] == "Alice Director"
    assert by_role["Writing"] == "Bob Writer"


def test_return_ratings_average(temp_db):
    ratings = query.returnRatings(1)
    assert len(ratings) == 1
    assert ratings[0]["rating"] == 4.5


def test_return_ratings_none(temp_db):
    assert query.returnRatings(2) == []


def test_random_movies_skips_empty_poster_and_caps(temp_db):
    films = query.randomMovies()
    assert all(f["poster_path"] for f in films)
    assert len(films) <= 20
    # seed has two movies with posters
    assert len(films) == 2


def test_insert_liked(temp_db):
    query.insert(10, 1, "liked")
    conn = sqlite3.connect(temp_db)
    row = conn.execute(
        "SELECT movieid, userid FROM liked WHERE userid = 10"
    ).fetchone()
    conn.close()
    assert row == (1, 10)


def test_set_db_path_roundtrip(temp_db):
    assert query.get_db_path() == temp_db
