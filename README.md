📖 Book-Pulse

**A small hunch about what to read next.**

BookPulse is an end-to-end book recommendation system that learns only from the books *you* enter. It needs no downloaded dataset and no external APIs. It ranks your to-be-read pile, explains each pick, and adds a dose of chance so you don't get stuck in a reading bubble. 


![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-database-336791)
![Redis](https://img.shields.io/badge/Redis-cache-DC382D)
![React](https://img.shields.io/badge/React-UI-61DAFB)
![License](https://img.shields.io/badge/License-MIT-green)

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
  

## Features

| Feature | Description |
|---|---|
| **Taste profile** | Learns from your ratings. Ratings are centred on your own average, so liked books pull recommendations closer and disliked ones push away. |
| **Serendipity Dial** | A slider from *safe* to *surprising* that blends relevance with novelty. |
| **Roll the Dice** | A weighted random pick from your pile. Books left unread the longest get extra weight. |
| **Explainable picks** | Every suggestion says why, for example: "Close to *Dune* (5★): shares politics, and adds philosophy." |
| **Taste DNA** | Shows the themes you rate highest. |
| **Blind Spots** | Lists themes on your TBR pile that you have never read. |
| **Bubble Meter** | Scores how broad or narrow your reading is. |
| **Mood and length filters** | Narrow your pile by mood or maximum page count. |
| **Smart tag cleaning** | `sci-fi`, `scifi` and `Sci Fi` become one tag, and typos are merged with tags you already use. |
| **Graceful degradation** | If Redis is down, the app keeps working without caching. |

## How It Works


flowchart LR
    A[Add books<br/>read + TBR] --> B[Tag cleaning<br/>and validation]
    B --> C[(PostgreSQL)]
    C --> D[TF-IDF<br/>book vectors]
    D --> E[Taste profile<br/>from ratings]
    E --> F[Score TBR books<br/>relevance, novelty, neglect]
    F --> G[MMR re-ranking<br/>for diversity]
    G --> H[Ranked picks<br/>with reasons]
    I[(Redis cache)] -.-> H


**Scoring**

```
score = (1 - dial) * relevance + dial * novelty + 0.15 * neglect
```

- **Relevance:** cosine similarity between a book and your taste profile.
- **Novelty:** how different a book is from everything you have read.
- **Neglect:** a boost for books that have sat on your shelf for up to six months.
- **MMR re-ranking:** removes near-duplicates so the top picks are varied.
- **Cold start:** personalised picks unlock after you rate 3 books. Roll the Dice works from the start.

## Tech Stack

| Layer | Technology |
|---|---|
| API | Python, FastAPI, Uvicorn |
| ML | pandas, NumPy, scikit-learn |
| Database | PostgreSQL |
| Cache | Redis (optional) |
| UI | React (loaded from a CDN, single `index.html`) |
| Infrastructure | Docker Compose (local), Render (deployment) |

## Project Structure


bookpulse/
├── main.py             # FastAPI app and routes
├── model.py            # TF-IDF vectors, taste profile, scoring
├── serendipity.py      # Serendipity Dial, MMR re-ranking, dice
├── insights.py         # Explanations, Taste DNA, blind spots, bubble meter
├── tags.py             # Tag normalisation and typo merging
├── db.py               # PostgreSQL schema and connections
├── cache.py            # Redis cache with safe fallback
├── config.py           # Environment settings
├── index.html          # React user interface
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Local PostgreSQL and Redis
└── .gitignore


## Getting Started

### Prerequisites

- Python 3.10 or newer
- Docker Desktop
- Git

### Run locally

```bash
# 1. Clone the repository
git clone https://github.com/hemangrealm/bookpulse.git
cd bookpulse

# 2. Start PostgreSQL and Redis
docker compose up -d

# 3. Create a virtual environment and install dependencies
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

# 4. Start the app
uvicorn main:app --reload
```

Open **http://localhost:8000**.

### First use

1. Add at least 3 books you have read, each with tags and a rating.
2. Add a few books to your TBR pile.
3. Move the dial or press **Roll the Dice**.

## Configuration

All settings are optional environment variables.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | local Postgres | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `CACHE_TTL` | `600` | Cache lifetime in seconds |
| `APP_USER` | `bookpulse` | Login username |
| `APP_PASSWORD` | empty | Login password. When empty, login is disabled (local use). |

## API Reference

Interactive docs are available at `/docs` when the server is running.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/books` | List all books |
| `POST` | `/books` | Add a book |
| `PATCH` | `/books/{id}/finish?rating=` | Move a TBR book to read with a rating |
| `DELETE` | `/books/{id}` | Remove a book |
| `GET` | `/recommend?dial=&mood=&max_pages=` | Ranked picks with reasons |
| `GET` | `/dice` | A lucky pick |
| `GET` | `/insights` | Taste DNA, blind spots, bubble meter |

