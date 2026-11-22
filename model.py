import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MIN_RATED = 3  # need this many rated books before personalizing
FILLER = "__book"  # keeps the vocabulary non-empty when books have no tags


class Shelf:
    """Everything the engine knows: only books the reader typed in."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.reset_index(drop=True)
        self.df["tags"] = self.df["tags"].apply(lambda t: list(t) if t is not None else [])
        self.df["author"] = self.df["author"].fillna("")
        self.df["note"] = self.df["note"].fillna("")
        self.df["added_at"] = pd.to_datetime(self.df["added_at"])

        tags = self.df.tags.apply(lambda t: " ".join(t))
        text = (tags + " ") * 3 + self.df.author + " " + self.df.note + " " + FILLER  # tags weigh 3x
        self.vec = TfidfVectorizer(token_pattern=r"[^\s]+", sublinear_tf=True)
        self.X = self.vec.fit_transform(text)
        self.sim = cosine_similarity(self.X)

        self.read = self.df.index[(self.df.status == "read") & self.df.rating.notna()].tolist()
        self.tbr = self.df.index[self.df.status == "tbr"].tolist()

    @property
    def ready(self) -> bool:
        return len(self.read) >= MIN_RATED

    def taste(self) -> np.ndarray:
        """Ratings are centered on YOUR average: liked books pull toward their tags,
        disliked books push away."""
        r = self.df.loc[self.read, "rating"].astype(float)
        w = (r - r.mean()).values
        if np.abs(w).sum() == 0:  # everything rated the same
            w = r.values
        return np.asarray(self.X[self.read].T @ w).ravel()

    def relevance(self) -> np.ndarray:
        s = cosine_similarity(self.X[self.tbr], self.taste().reshape(1, -1)).ravel()
        return (s - s.min()) / (s.max() - s.min() + 1e-9)

    def novelty(self) -> np.ndarray:
        """1 = nothing like anything you've read."""
        return 1 - self.sim[np.ix_(self.tbr, self.read)].max(axis=1)

    def neglect(self) -> np.ndarray:
        """0..1 boost for books sitting on the shelf; 6 months = max."""
        age = (pd.Timestamp.now() - self.df.loc[self.tbr, "added_at"]).dt.days.values
        return np.clip(age / 180, 0, 1)