import csv
import sqlite3
from ast import literal_eval

# fetch the csv files from https://www.kaggle.com/rounakbanik/the-movies-dataset
# drop in a folder called data and run, it should take around a minute or two


def format_genres(genre_list):
    """Build the display string used when loading movies from CSV.

    Expects a list of dicts with a ``name`` key (as in the Kaggle metadata).
    """
    genres = " - "
    for item in genre_list:
        genres = genres + item["name"] + " - "
    return genres


def should_include_cast(order):
    """Match db load rule: keep cast members with order index under 9."""
    return order < 9


def should_include_crew(department):
    """Match db load rule: keep Directing and Writing crew only."""
    return department == "Directing" or department == "Writing"


def init_schema(connection):
    """Create the SQLite tables used by the app (idempotent)."""
    curs = connection.cursor()
    curs.execute(
        "CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username CHAR(15) UNIQUE, email CHAR(50) UNIQUE, password CHAR(80))")
    curs.execute(
        "CREATE TABLE IF NOT EXISTS liked(movieid INT, userid INT, FOREIGN KEY(userid) REFERENCES users(id), FOREIGN KEY(movieid) REFERENCES movies(id))")
    curs.execute(
        "CREATE TABLE IF NOT EXISTS viewed(movieid INT, userid INT, FOREIGN KEY(userid) REFERENCES users(id), FOREIGN KEY(movieid) REFERENCES movies(id))")
    curs.execute(
        "CREATE TABLE IF NOT EXISTS searched(movieid INT, userid INT, FOREIGN KEY(userid) REFERENCES users(id), FOREIGN KEY(movieid) REFERENCES movies(id))")
    curs.execute(
        "CREATE TABLE IF NOT EXISTS movies(id int UNIQUE, imdb_id char(12), overview TEXT, genres TEXT, title TEXT, release_date TEXT, homepage TEXT, poster_path TEXT, tagline TEXT, PRIMARY KEY (id))")
    curs.execute(
        "CREATE TABLE IF NOT EXISTS casts(id int, character TEXT, name TEXT, profile_path TEXT, FOREIGN KEY (id) REFERENCES movies(id))")
    curs.execute(
        "CREATE TABLE IF NOT EXISTS crews(id int, name TEXT, role TEXT, FOREIGN KEY(id) REFERENCES movies(id))")
    curs.execute(
        "CREATE TABLE IF NOT EXISTS ratings(id int, rating float, FOREIGN KEY(id) REFERENCES movies(id))")
    connection.commit()


def load_from_csv(db_path="movies.db", data_dir="data"):
    """Populate movies.db from Kaggle CSV files under data_dir."""
    db = sqlite3.connect(db_path)
    curs = db.cursor()

    csvfile = open("%s/movies_metadata.csv" % data_dir, "r")
    stars = open("%s/credits.csv" % data_dir, "r")
    ratings = open("%s/ratings.csv" % data_dir, "r")

    movieReader = csv.DictReader(csvfile)
    starReader = csv.DictReader(stars)
    ratingsReader = csv.DictReader(ratings)

    init_schema(db)

    print("Populating movies table")
    for row in movieReader:
        genreDict = literal_eval(row["genres"])
        genres = format_genres(genreDict)
        try:
            curs.execute('''INSERT OR REPLACE INTO movies(id, imdb_id, overview, genres, title, release_date, homepage, poster_path, tagline) VALUES(?,?,?,?,?,?,?,?,?)''',
                         (int(row["id"]), row["imdb_id"], row["overview"], genres, row["title"], row["release_date"], row["homepage"], row["poster_path"], row["tagline"]))
        except Exception:
            continue

    print("Movies table created successfully")

    print("Populating casts and crews tables")
    for row in starReader:
        cast = literal_eval(row["cast"])
        crew = literal_eval(row["crew"])
        for item in cast:
            if should_include_cast(item["order"]):
                curs.execute('''INSERT INTO casts(id, character, name, profile_path) VALUES(?,?,?,?)''',
                             (int(row["id"]), item["character"], item["name"], item["profile_path"]))
        for item in crew:
            if should_include_crew(item["department"]):
                curs.execute('''INSERT INTO crews(id, name, role) VALUES(?,?,?)''',
                             (int(row["id"]), item["name"], item["department"]))
    print("Casts and crews created successfully")

    print("Populating ratings tables")
    for row in ratingsReader:
        curs.execute('''INSERT INTO ratings(id, rating) VALUES(?,?)''',
                     (int(row["movieId"]), float(row["rating"])))
    print("Ratings table created successfully")

    csvfile.close()
    stars.close()
    ratings.close()

    db.commit()
    db.close()
    print("Closing up shop..")


if __name__ == "__main__":
    load_from_csv()
