"""Blue-team defenses and the on-card critic. Author: Hossein Tabasi.

detector_p_ai is produced here: TF-IDF logistic fitted only if DEV real vs synth posts
exist; otherwise a transparent lexical detector. Never invent an AUC.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from src.io_utils import DATA, read_jsonl
from src.schemas import BANNED_PHRASES, CERTAINTY_LEXICON, TEMPLATE_MARKERS

LICENSED_PEG_LANG = re.compile(r"\b(1\s*[:/]\s*1|one[- ]for[- ]one|par value|at par)\b", re.I)

DATE_RE = re.compile(
    r"\b(?:(?:19|20)\d{2}-\d{2}-\d{2}|"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s*(?:19|20)\d{2}|"
    r"\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(?:19|20)\d{2}|"
    r"(?:19|20)\d{2})\b",
    re.I,
)
MONEY_RE = re.compile(
    r"\$\s?\d{1,3}(?:,\d{3})+(?:\.\d+)?|\$\s?\d+(?:\.\d+)?\s*(?:billion|million|trillion|B|M|bn)?|"
    r"\b\d+(?:\.\d+)?\s*(?:billion|million|trillion)\b|"
    r"\b\d{1,3}(?:,\d{3}){2,}\b",
    re.I,
)
PCT_RE = re.compile(r"\b\d+(?:\.\d+)?\s*%")
HASH_RE = re.compile(r"\b0x[a-fA-F0-9]{8,}\b")
QUOTE_RE = re.compile(r"[“\"]([^”\"]{8,})[”\"]")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

_FITTED = {"model": None, "vectorizer": None, "tried": False}


def _norm_num(s: str) -> str:
    t = s.lower().replace(",", "").replace("$", "").strip()
    t = t.replace("billion", "b").replace("million", "m").replace("trillion", "t")
    t = re.sub(r"\s+", "", t)
    t = t.replace("bn", "b")
    return t


def _card_blob(card: Dict[str, Any]) -> str:
    parts = [
        card.get("official_status", ""),
        card.get("price_or_peg_path_72h", ""),
        " ".join(card.get("verified_facts") or []),
        " ".join(card.get("forbidden_inventions") or []),
    ]
    return " ".join(parts)


def licensed_tokens(card: Dict[str, Any], extra_blob: str = "") -> set:
    blob = _card_blob(card) + " " + extra_blob
    toks = set()
    for m in MONEY_RE.findall(blob):
        toks.add(_norm_num(m))
    for m in PCT_RE.findall(blob):
        toks.add(_norm_num(m))
    for m in DATE_RE.findall(blob):
        toks.add(re.sub(r"\s+", " ", m.lower()))
    for m in YEAR_RE.findall(blob):
        toks.add(m)
    for m in re.findall(r"\b\d{2,}\b", blob.replace(",", "")):
        toks.add(m)
    for m in re.findall(r"\b\d+\.\d+\b", blob):
        toks.add(m)
        toks.add(m.replace(".", ""))
    return toks


def extract_suspects(text: str) -> Dict[str, List[str]]:
    return {
        "money": MONEY_RE.findall(text),
        "pct": PCT_RE.findall(text),
        "dates": DATE_RE.findall(text),
        "years": YEAR_RE.findall(text),
        "hashes": HASH_RE.findall(text),
        "quotes": QUOTE_RE.findall(text),
        "big_ints": re.findall(r"\b\d{1,3}(?:,\d{3}){2,}\b", text),
    }


def number_not_on_card(text: str, card: Dict[str, Any], extra_blob: str = "") -> List[str]:
    lic = licensed_tokens(card, extra_blob)
    blob = (_card_blob(card) + " " + extra_blob).lower()
    bad: List[str] = []
    sus = extract_suspects(text)
    for m in sus["money"] + sus["pct"] + sus["big_ints"]:
        n = _norm_num(m)
        if n in lic:
            continue
        if n in {"1", "11"} and LICENSED_PEG_LANG.search(text):
            continue
        compact = re.sub(r"[^\d.]", "", m)
        if compact and compact in re.sub(r"[^\d.]", "", blob):
            continue
        bad.append(m)
    for d in sus["dates"] + sus["years"]:
        dl = re.sub(r"\s+", " ", d.lower())
        if dl in lic or d in lic:
            continue
        if d.lower() in blob or dl in blob:
            continue
        bad.append(d)
    for h in sus["hashes"]:
        if h.lower() not in blob:
            bad.append(h)
    for q in sus["quotes"]:
        if q.lower() not in blob:
            # attributed short quotes must appear on the card; otherwise ungrounded
            bad.append(q[:80])
    return bad


def hallucination_flag(text: str, card: Dict[str, Any]) -> int:
    if number_not_on_card(text, card):
        return 1
    tl = (text or "").lower()
    if any(b in tl for b in BANNED_PHRASES):
        return 1
    return 0


def lexical_detector_p(text: str) -> float:
    """Transparent lexical detector in [0, 1]. Not an AUC."""
    tl = (text or "").lower()
    score = 0.0
    for m in TEMPLATE_MARKERS:
        if m in tl:
            score += 0.18
    for m in CERTAINTY_LEXICON:
        if m in tl:
            score += 0.12
    emoji = len(re.findall(r"[\U0001F300-\U0001FAFF⚠📌❗📉📈]", text or ""))
    score += min(0.2, 0.05 * emoji)
    # high overlap with "card" boilerplate
    if "no invented" in tl or "card facts" in tl or "fact card" in tl:
        score += 0.15
    return float(max(0.0, min(1.0, score)))


def _try_fit_logistic() -> None:
    if _FITTED["tried"]:
        return
    _FITTED["tried"] = True
    real = read_jsonl(DATA / "real_headlines.jsonl")
    synth = read_jsonl(DATA / "synth_posts.jsonl")
    # only DEV, and only if both classes exist with enough rows
    real_dev = [r.get("text", "") for r in real if r.get("split") == "dev" and r.get("text")]
    synth_dev = [r.get("text", "") for r in synth if r.get("split") == "dev" and r.get("text")]
    if len(real_dev) < 8 or len(synth_dev) < 8:
        return
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        import numpy as np
    except Exception:
        return
    y = [0] * len(real_dev) + [1] * len(synth_dev)
    vec = TfidfVectorizer(min_df=1, ngram_range=(1, 2), max_features=4000)
    x = vec.fit_transform(real_dev + synth_dev)
    clf = LogisticRegression(max_iter=200)
    clf.fit(x, y)
    _FITTED["model"] = clf
    _FITTED["vectorizer"] = vec


def detector_p_ai(text: str) -> float:
    _try_fit_logistic()
    if _FITTED["model"] is not None and _FITTED["vectorizer"] is not None:
        x = _FITTED["vectorizer"].transform([text or ""])
        proba = _FITTED["model"].predict_proba(x)[0]
        # class 1 = synth
        classes = list(_FITTED["model"].classes_)
        if 1 in classes:
            return float(proba[classes.index(1)])
        return float(proba[-1])
    return lexical_detector_p(text)


def factcheck_correction(card: Dict[str, Any], event: Dict[str, Any], offender_text: str) -> str:
    bad = number_not_on_card(offender_text, card)
    status = str(card.get("official_status") or "").rstrip(".") + "."
    path = str(card.get("price_or_peg_path_72h") or "[UNKNOWN]")
    flag = ", ".join(bad[:4]) if bad else "ungrounded span"
    return (
        f"Fact-check correction for {event.get('event_id')}: off-card claim flagged ({flag}). "
        f"Official status: {status} Peg path on the card: {path} "
        f"Missing facts stay [UNKNOWN]."
    )


def apply_detector_gate(post: Dict[str, Any], tau: float) -> bool:
    """Return True if the post should be DROPPED."""
    p = float(post.get("detector_p_ai", 0.0))
    return p > float(tau)


def retail_rate_limited(agent: Dict[str, Any]) -> bool:
    if not str(agent.get("role", "")).startswith("retail_"):
        return False
    return int(agent.get("rebroadcasts_this_round", 0)) >= 1
