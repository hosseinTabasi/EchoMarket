"""Record schemas and closed lexicons. Author: Hossein Tabasi."""

from __future__ import annotations

from typing import Any, Dict, List

STANCES = {"panic", "reassurance", "speculative", "factual"}
PEG_SENTS = {"bearish", "neutral", "bullish"}
INTENTS = {"inform", "reassure", "alarm", "persuade"}
RELATIONS = {"follow", "official", "media"}
ROLES = {
    "official",
    "journalist",
    "whale",
    "analyst",
    "bot",
    "retail_panic",
    "retail_skeptical",
    "retail_apathetic",
    "redteam",
}
CONDITIONS = {"A", "B", "C", "D", "E-factcheck", "E-ratelimit", "E-detector"}
SPLITS = {"dev", "test"}

POST_JSON_FIELDS = [
    "text",
    "stance",
    "peg_sentiment",
    "claimed_facts",
    "unknowns",
    "reply_to",
    "intent",
]

AGENT_FIELDS = [
    "agent_id",
    "role",
    "community",
    "peg_confidence",
    "alpha",
    "beta",
    "gamma",
    "p_post",
    "mutation",
]

EDGE_FIELDS = ["src", "dst", "relation", "weight"]

ALARM_LEXICON = [
    "depeg",
    "depegged",
    "plummeted",
    "sank",
    "inaccessible",
    "stuck",
    "restrict",
    "restricted",
    "delist",
    "delisting",
    "shortfall",
    "receivership",
    "unable to withdraw",
    "broke",
    "crash",
    "panic",
    "bank run",
    "87 cents",
    "0.87",
    "86 cents",
    "haywire",
    "backlog",
]

RISK_NEG = [
    "depeg",
    "depegged",
    "plummeted",
    "sank",
    "inaccessible",
    "stuck",
    "restrict",
    "restricted",
    "delist",
    "delisting",
    "hard deadline",
    "did not seek",
    "shortfall",
    "receivership",
    "unable to withdraw",
    "lost its peg",
    "broke",
    "87 cents",
    "0.87",
    "86 cents",
]

RISK_POS = [
    "1 for 1",
    "1:1",
    "redeemable",
    "stand behind",
    "depositors",
    "fully protected",
    "recovered",
    "fully recovered",
    "excess",
    "unqualified",
    "clean audit",
    "par value",
    "fungible",
    "mica-compliant",
    "operations resume",
    "cleared substantially all",
    "assets exceed",
]

RISK_NEU_REG = [
    "public law",
    "signed into law",
    "white paper",
    "attestation",
    "priced",
    "ipo",
    "ticker",
]

BANNED_PHRASES = [
    "buy now",
    "guaranteed profit",
    "guaranteed returns",
    "pump",
    "wire me",
]

CERTAINTY_LEXICON = [
    "no doubt",
    "confirmed",
    "absolutely",
    "everyone knows",
    "guaranteed",  # still banned as trading; detector may see it
    "clearly over",
    "this is it",
]

TEMPLATE_MARKERS = [
    "fact card",
    "sourced record",
    "named sources",
    "card lock",
    "verified_facts",
]

MUTATION_STYLE = {
    "official": "quote/paraphrase",
    "journalist": "paraphrase",
    "whale": "paraphrase",
    "analyst": "paraphrase",
    "bot": "quote",
    "retail_panic": "exaggerate",
    "retail_skeptical": "paraphrase",
    "retail_apathetic": "ignore",
    "redteam": "rhetoric",
}

SMOKE_ROLE_COUNTS = {
    "official": 1,
    "journalist": 1,
    "whale": 1,
    "analyst": 1,
    "bot": 1,
    "retail_panic": 3,
    "retail_skeptical": 2,
    "retail_apathetic": 2,
}

PANEL_SPEC = [
    ("official", 2),
    ("journalist", 2),
    ("whale", 2),
    ("analyst", 2),
    ("retail_panic", 1),
    ("retail_skeptical", 1),
]


def empty_post_payload() -> Dict[str, Any]:
    return {
        "text": "",
        "stance": "factual",
        "peg_sentiment": "neutral",
        "claimed_facts": [],
        "unknowns": [],
        "reply_to": None,
        "intent": "inform",
    }


def validate_post_payload(rec: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for f in POST_JSON_FIELDS:
        if f not in rec:
            errors.append(f"missing field {f}")
    if rec.get("stance") not in STANCES:
        errors.append(f"bad stance {rec.get('stance')}")
    if rec.get("peg_sentiment") not in PEG_SENTS:
        errors.append(f"bad peg_sentiment {rec.get('peg_sentiment')}")
    if rec.get("intent") not in INTENTS:
        errors.append(f"bad intent {rec.get('intent')}")
    return errors
