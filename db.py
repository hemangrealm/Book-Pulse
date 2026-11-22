from contextlib import contextmanager
import psycopg2
import psycopg2.extras
from config import DATABASE_URL

SCHEMA = """
CREATE TABLE IF NOT EXISTS books(
  id SERIAL PRIMARY KEY,
  user_id INT DEFAULT 1,
  title TEXT NOT NULL,
  author TEXT DEFAULT '',
  tags TEXT[] DEFAULT '{}',
  note TEXT DEFAULT '',
  pages INT,
  mood TEXT,
  status TEXT CHECK (status IN ('read','tbr')) NOT NULL,
  rating INT CHECK (rating BETWEEN 1 AND 5),
  added_at TIMESTAMP DEFAULT now(),
  finished_at TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_book
  ON books(user_id, lower(title), lower(author));
"""


@contextmanager
def cursor():
    """Commit on success, roll back on error, always close."""
    c = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        with c, c.cursor() as cur:
            yield cur
    finally:
        c.close()


def init():
    with cursor() as cur:
        cur.execute(SCHEMA)