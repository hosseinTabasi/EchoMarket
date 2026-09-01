"""Fact-card-conditioned decoder (prompt-only multi-agent loop). Author: Hossein Tabasi.

v1: role templates + slot fill + licensed mutation. Numeric claims copied from the card only.
Optional HTTP / adapter hooks return immediately when no key or GPU is present.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from src.io_utils import split_sentences, word_count
from src.schemas import ALARM_LEXICON, BANNED_PHRASES, empty_post_payload, validate_post_payload

SAY = ["said", "stated", "disclosed", "reported", "recorded"]
EMOJI = ["⚠️", "📌", "❗", "📉", "📈"]


def maybe_api_generate(_messages: List[Dict[str, str]]) -> None:
    key = os.environ.get("ECHOMARKET_API_KEY")
    if not key:
        return None
    return None


def maybe_lora_generate(_card: Dict[str, Any]) -> None:
    if os.environ.get("ECHOMARKET_LORA_PATH"):
        return None
    return None


def _facts(card: Dict[str, Any]) -> List[str]:
    return [str(x).rstrip(".") + "." for x in card.get("verified_facts") or []]


def _status(card: Dict[str, Any]) -> str:
    return str(card.get("official_status") or "").rstrip(".") + "."


def _path(card: Dict[str, Any]) -> str:
    return str(card.get("price_or_peg_path_72h") or "[UNKNOWN]")


def _unknowns(card: Dict[str, Any]) -> List[str]:
    out = []
    if "[UNKNOWN]" in _path(card):
        out.append("72-hour peg path not sourced on the fact card")
    for inv in card.get("forbidden_inventions") or []:
        if "[UNKNOWN]" in str(inv):
            out.append(str(inv))
    return out[:6]


def path_sign(card: Dict[str, Any]) -> str:
    p = _path(card).lower()
    if "[unknown]" in p:
        return "unknown"
    if "negative" in p:
        return "negative"
    if "positive" in p:
        return "positive"
    return "unknown"


def _banned(text: str) -> bool:
    tl = text.lower()
    return any(b in tl for b in BANNED_PHRASES)


def default_stance_peg(role: str, card: Dict[str, Any], event: Dict[str, Any]) -> Tuple[str, str, str]:
    """Return stance, peg_sentiment, intent."""
    sign = path_sign(card)
    status = _status(card).lower()
    et = (event.get("event_type") or "").lower()
    if role == "official":
        if sign == "negative":
            return "factual", "neutral", "inform"
        return "reassurance", "bullish" if sign == "positive" or "excess" in status or "1:1" in status or "unqualified" in status else "neutral", "reassure"
    if role == "journalist":
        peg = "bearish" if sign == "negative" else "bullish" if sign == "positive" else "neutral"
        return "factual", peg, "inform"
    if role == "whale":
        peg = "bearish" if sign == "negative" else "bullish" if sign == "positive" else "neutral"
        return "speculative", peg, "inform"
    if role == "analyst":
        peg = "bearish" if sign == "negative" else "bullish" if sign == "positive" else "neutral"
        return "factual" if sign != "unknown" else "speculative", peg, "inform"
    if role == "bot":
        peg = "bearish" if sign == "negative" else "bullish" if sign == "positive" else "neutral"
        return "factual", peg, "inform"
    if role == "retail_panic":
        bearishish = sign == "negative" or "restrict" in status or "did not seek" in status or "delist" in status
        return "panic", "bearish" if bearishish else "neutral", "alarm"
    if role == "retail_skeptical":
        return "speculative", "neutral", "inform"
    if role == "retail_apathetic":
        return "factual", "neutral", "inform"
    if role == "redteam":
        return "panic", "bearish", "persuade"
    if role == "factcheck":
        return "factual", "neutral", "inform"
    _ = et
    return "factual", "neutral", "inform"


def _pick_facts(card: Dict[str, Any], rng, k: int = 2) -> List[str]:
    facts = list(_facts(card))
    rng.shuffle(facts)
    return facts[: max(1, min(k, len(facts)))]


def _fill(role: str, event: Dict[str, Any], card: Dict[str, Any], rng) -> str:
    eid = event.get("event_id", "")
    asset = event.get("asset", "")
    date = event.get("date", "")
    status = _status(card)
    path = _path(card)
    picked = _pick_facts(card, rng, k=2)
    a = picked[0]
    b = picked[1] if len(picked) > 1 else status
    verb = SAY[rng.randrange(len(SAY))]

    if role == "official":
        return f"Official status on {eid}: {status} The record {verb}: {a}"
    if role == "journalist":
        return (
            f"{date} — {asset} {event.get('event_type')}: {status} "
            f"Named sources {verb}: {a} Seventy-two-hour peg path on the card: {path}"
        )
    if role == "whale":
        return f"{asset} inventory note ({eid}): {a} Peg-path field: {path} No off-card sizes."
    if role == "analyst":
        unk = "[UNKNOWN] remains [UNKNOWN]" if "[UNKNOWN]" in path else f"Sourced path: {path}"
        return f"Analyst restatement of {eid}: {status} {a} {unk}."
    if role == "bot":
        return f"{a} {status}"
    if role == "retail_panic":
        return (
            f"This is confirmed from the {eid} card — no invented billions. {a} "
            f"Official status: {status} Peg path licensed on the card: {path}"
        )
    if role == "retail_skeptical":
        return (
            f"Waiting on what the {eid} card actually licenses. {a} "
            f"If the 72-hour path is missing it stays [UNKNOWN]: {path}"
        )
    if role == "retail_apathetic":
        return f"{a}"
    if role == "redteam":
        return (
            f"Everyone knows the {eid} card already {verb} this. {a} "
            f"{status} Peg path on the card: {path} No new figures."
        )
    if role == "factcheck":
        return f"Correction from the {eid} card only: {status} Licensed fact: {a} Peg path: {path}"
    return f"{eid}: {a} {b}"


def mutate(text: str, style: str, rng) -> str:
    sents = split_sentences(text) or [text]
    if style == "ignore":
        return sents[0] if sents else text
    if style == "quote":
        return text
    if style == "exaggerate" or style == "rhetoric":
        if rng.random() < 0.7:
            em = EMOJI[rng.randrange(len(EMOJI))]
            text = f"{em} {text}"
        if rng.random() < 0.5:
            text = text.rstrip(".") + ". No doubt on the card facts."
        return text
    # paraphrase / quote/paraphrase: maybe shorten
    if style.startswith("quote"):
        if rng.random() < 0.3 and len(sents) > 1:
            return sents[0]
        return text
    if rng.random() < 0.35 and len(sents) > 1:
        return " ".join(sents[:2]) if len(sents) > 2 else sents[0]
    return text


def generate_one(
    role: str,
    event: Dict[str, Any],
    card: Dict[str, Any],
    rng,
    memory: Optional[List[Dict[str, Any]]] = None,
    reply_to: Optional[str] = None,
    mutation_style: Optional[str] = None,
) -> Dict[str, Any]:
    maybe_api_generate([])
    maybe_lora_generate(card)
    _ = memory  # window is a constraint, not a source of new facts
    payload = empty_post_payload()
    stance, peg, intent = default_stance_peg(role, card, event)
    text = _fill(role, event, card, rng)
    style = mutation_style or "paraphrase"
    text = mutate(text, style, rng)
    if _banned(text):
        text = re.sub("|".join(re.escape(b) for b in BANNED_PHRASES), "[removed]", text, flags=re.I)
    if not text.endswith((".", "!", "?")):
        text = text.rstrip() + "."
    payload["text"] = text
    payload["stance"] = stance
    payload["peg_sentiment"] = peg
    payload["claimed_facts"] = _pick_facts(card, rng, k=3)
    payload["unknowns"] = _unknowns(card)
    payload["reply_to"] = reply_to
    payload["intent"] = intent
    errs = validate_post_payload(payload)
    if errs:
        raise RuntimeError("invalid payload: " + "; ".join(errs))
    return payload


def emo_score(text: str) -> float:
    tl = (text or "").lower()
    tokens = re.findall(r"\S+", tl)
    hits = 0
    for lex in ALARM_LEXICON:
        if lex in tl:
            hits += tl.count(lex)
    return hits / (1.0 + len(tokens))


def cosine_novelty(text: str, recent_texts: List[str]) -> float:
    if not recent_texts:
        return 0.0
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
    except Exception:
        # lexical fallback: 1 - max Jaccard of word sets
        a = set(re.findall(r"[a-z0-9]+", text.lower()))
        best = 0.0
        for t in recent_texts:
            b = set(re.findall(r"[a-z0-9]+", t.lower()))
            if not a and not b:
                continue
            j = len(a & b) / max(1, len(a | b))
            if j > best:
                best = j
        return 1.0 - best
    corpus = [text] + list(recent_texts)
    vec = TfidfVectorizer(min_df=1, token_pattern=r"(?u)\b\w+\b")
    try:
        x = vec.fit_transform(corpus)
    except ValueError:
        return 0.0
    sims = cosine_similarity(x[0:1], x[1:])
    import numpy as np

    m = float(np.max(sims)) if sims.size else 0.0
    return 1.0 - m


def virality(
    pr_author: float,
    text: str,
    recent_texts: List[str],
    lambdas: Dict[str, float],
) -> float:
    import math

    lp = float(lambdas.get("lambda_p", 1.0))
    le = float(lambdas.get("lambda_e", 0.7))
    ln = float(lambdas.get("lambda_n", 0.5))
    return lp * math.log(1.0 + max(0.0, pr_author)) + le * emo_score(text) + ln * cosine_novelty(text, recent_texts)
