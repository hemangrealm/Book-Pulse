import re
import difflib

SYN = {
    "sci-fi": "science_fiction", "scifi": "science_fiction", "sf": "science_fiction",
    "sci fi": "science_fiction", "self help": "self_help", "non fiction": "nonfiction",
    "bio": "biography", "rom com": "romcom", "ya": "young_adult",
}


def norm(tag: str) -> str:
    t = re.sub(r"\s+", " ", tag.strip().lower().replace("-", " "))
    t = SYN.get(t, t)
    return t.replace(" ", "_")


def clean(tags, existing):
    """Normalize, merge typos with tags you already use ("fantsy" -> "fantasy"), dedupe."""
    out = []
    for t in map(norm, tags):
        if not t:
            continue
        m = difflib.get_close_matches(t, existing, n=1, cutoff=0.85)
        out.append(m[0] if m else t)
    return sorted(set(out))