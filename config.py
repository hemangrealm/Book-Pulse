import os

DATABASE_URL = os.getenv("DATABASE_URL", "dbname=shelf user=sr password=sr host=localhost")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "600"))
USER_ID = 1  # single local reader