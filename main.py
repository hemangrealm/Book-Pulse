from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

import pandas as pd
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import cache
import db
import tags as T
from config import USER_ID
from insights import blind_spots, bubble_meter, explain, taste_dna
from model import MIN_RATED, Shelf
from serendipity import dice, rank

INDEX = Path(__file__).parent / "index.html"


@asynccontextmanager
async def lifespan(app):
    db.init()  # creates the table on first start
    yield


app = FastAPI(title="BookPulse", lifespan=lifespan)


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(default="", max_length=120)
    tags: list[str] = []
    note: str = Field(default="", max_length=500)
    pages: Optional[int] = Field(default=None, ge=1, le=5000)
    mood: Optional[str] = None
    status: Literal["read", "tbr"]
    rating: Optional[int] = Field(default=None, ge=1, le=5)


def fetch_df():
    with db.cursor() as cur:
        cur.execute("SELECT * FROM books WHERE user_id=%s ORDER BY added_at", (USER_ID,))
        rows = cur.fetchall()
    return pd.DataFrame(rows)


def load(mood=None, max_pages=None):
    df = fetch_df()
    if df.empty:
        return None
    if mood or max_pages:  # filter the TBR pool only; reading history stays
        pool = df.status == "tbr"
        if mood:
            pool &= df.mood == mood
        if max_pages:
            pool &= df.pages.fillna(0) <= max_pages
        df = df[(df.status == "read") | pool]
    return Shelf(df)


@app.get("/")
def home():
    return FileResponse(INDEX)


@app.get("/books")
def list_books():
    df = fetch_df()
    if df.empty:
        return []
    df = df.astype(object).where(df.notna(), None)
    return [{**r, "added_at": str(r["added_at"]),
             "finished_at": str(r["finished_at"]) if r["finished_at"] else None}
            for r in df.to_dict("records")]


@app.post("/books")
def add_book(b: BookIn):
    if b.status == "read" and not b.rating:
        raise HTTPException(422, "Rate books you've read (1-5).")
    try:
        with db.cursor() as cur:
            cur.execute("SELECT DISTINCT unnest(tags) AS t FROM books WHERE user_id=%s", (USER_ID,))
            existing = [r["t"] for r in cur.fetchall()]
            cur.execute(
                """INSERT INTO books(user_id,title,author,tags,note,pages,mood,status,rating,finished_at)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s, CASE WHEN %s='read' THEN now() END) RETURNING id""",
                (USER_ID, b.title.strip(), b.author.strip(), T.clean(b.tags, existing), b.note.strip(),
                 b.pages, b.mood or None, b.status, b.rating if b.status == "read" else None, b.status))
            new_id = cur.fetchone()["id"]
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(409, "You already added this book.")
    cache.clear(USER_ID)
    return {"id": new_id}


@app.patch("/books/{book_id}/finish")
def finish_book(book_id: int, rating: int):
    if not 1 <= rating <= 5:
        raise HTTPException(422, "Rating must be 1-5.")
    with db.cursor() as cur:
        cur.execute("UPDATE books SET status='read', rating=%s, finished_at=now() WHERE id=%s AND user_id=%s",
                    (rating, book_id, USER_ID))
        if cur.rowcount == 0:
            raise HTTPException(404, "Book not found.")
    cache.clear(USER_ID)
    return {"ok": True}


@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    with db.cursor() as cur:
        cur.execute("DELETE FROM books WHERE id=%s AND user_id=%s", (book_id, USER_ID))
    cache.clear(USER_ID)
    return {"ok": True}


@app.get("/recommend")
def recommend(dial: float = 0.3, mood: Optional[str] = None, max_pages: Optional[int] = None):
    key = f"u{USER_ID}:rec:{dial}:{mood}:{max_pages}"
    if hit := cache.get(key):
        return hit
    m = load(mood, max_pages)
    if m is None or not m.tbr:
        return {"state": "empty", "picks": []}
    if not m.ready:
        return {"state": "locked", "need": MIN_RATED - len(m.read), "picks": []}
    picks = [{"id": int(m.df.id[i]), "title": m.df.title[i], "author": m.df.author[i],
              "pages": None if pd.isna(m.df.pages[i]) else int(m.df.pages[i]),
              "tags": m.df.tags[i], "why": explain(m, i)} for i in rank(m, dial)]
    out = {"state": "ok", "picks": picks}
    cache.put(key, out)
    return out


@app.get("/dice")
def roll():
    m = load()
    if m is None or not m.tbr:
        raise HTTPException(404, "Add some books to your TBR first.")
    i = dice(m)
    return {"id": int(m.df.id[i]), "title": m.df.title[i], "author": m.df.author[i],
            "why": explain(m, i) if m.ready else "A lucky pick from your shelf."}


@app.get("/insights")
def insights():
    m = load()
    if m is None or not m.ready:
        return {"ready": False}
    return {"ready": True, "dna": taste_dna(m), "blind_spots": blind_spots(m), "bubble": bubble_meter(m)}