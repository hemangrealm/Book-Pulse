import numpy as np


def rank(m, dial=0.3, n=5, rescue=0.15):
    """Top-n TBR books. dial 0 = closest to your taste, 1 = most different."""
    dial = float(np.clip(dial, 0, 1))
    rel, nov, neg = m.relevance(), m.novelty(), m.neglect()
    score = (1 - dial) * rel + dial * nov + rescue * neg

    # MMR re-rank so the list isn't five near-identical books
    sub = m.sim[np.ix_(m.tbr, m.tbr)]
    cand, chosen = list(np.argsort(-score)), []
    while cand and len(chosen) < n:
        if not chosen:
            best = cand[0]
        else:
            div = sub[np.ix_(cand, chosen)].max(axis=1)
            best = cand[int(np.argmax((1 - dial * 0.5) * score[cand] - dial * 0.5 * div))]
        chosen.append(best)
        cand.remove(best)
    return [m.tbr[i] for i in chosen]


def dice(m, rescue=1.0):
    """Lucky pick from the TBR. Every book has a chance; books left unread
    the longest get extra weight (Forgotten Book Rescue)."""
    w = (0.2 + m.relevance()) if m.ready else np.ones(len(m.tbr))
    w = w + rescue * m.neglect()
    return m.tbr[int(np.random.choice(len(m.tbr), p=w / w.sum()))]