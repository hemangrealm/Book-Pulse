from collections import Counter
import numpy as np
from model import FILLER


def explain(m, i):
    liked = [j for j in m.read if m.df.rating[j] >= 4] or m.read
    src = max(liked, key=lambda j: m.sim[j, i])
    a, b = set(m.df.tags[src]), set(m.df.tags[i])
    shared, fresh = sorted(a & b)[:2], sorted(b - a)[:2]
    s = f"Close to “{m.df.title[src]}” ({int(m.df.rating[src])}★)"
    if shared:
        s += f": shares {', '.join(t.replace('_', ' ') for t in shared)}"
    if fresh:
        s += f", and adds {', '.join(t.replace('_', ' ') for t in fresh)}"
    return s


def taste_dna(m, k=6):
    names = m.vec.get_feature_names_out()
    t = m.taste()
    out = []
    for j in np.argsort(-t):
        if names[j] == FILLER or t[j] <= 0:
            continue
        out.append({"tag": names[j].replace("_", " "), "weight": round(float(t[j]), 3)})
        if len(out) == k:
            break
    return out


def blind_spots(m, k=5):
    """Themes on your TBR you have never actually read."""
    read_tags = {t for i in m.read for t in m.df.tags[i]}
    tbr_tags = Counter(t for i in m.tbr for t in m.df.tags[i])
    return [t.replace("_", " ") for t, _ in tbr_tags.most_common() if t not in read_tags][:k]


def bubble_meter(m):
    """0 = very narrow reading, 1 = very broad."""
    c = Counter(t for i in m.read for t in m.df.tags[i])
    if len(c) < 2:
        return 0.0
    p = np.array(list(c.values()), float)
    p /= p.sum()
    return round(float(-(p * np.log(p)).sum() / np.log(len(p))), 2)