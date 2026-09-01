"""Red-team rhetoric agent. Facts from the card only. Author: Hossein Tabasi."""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.defend import detector_p_ai, hallucination_flag
from src.generate import generate_one


def attack_direction(event: Dict[str, Any], card: Dict[str, Any]) -> str:
    path = (card.get("price_or_peg_path_72h") or "").lower()
    if "negative" in path:
        return "bearish"
    if "positive" in path:
        return "bullish"
    eid = event.get("event_id", "")
    et = (event.get("event_type") or "").lower()
    summary = (event.get("fact_summary") or "").lower()
    if eid in {"E04", "E09"} or "restrict" in summary or "did not seek" in summary:
        return "bearish"
    if "attestation" in et or "issuer operational" in et:
        return "bullish"
    return "bearish"


def maybe_red_post(
    event: Dict[str, Any],
    card: Dict[str, Any],
    rng,
    tau: float,
    budget_left: int,
    round_index: int,
    rounds: int,
    author_id: str,
) -> Optional[Dict[str, Any]]:
    """Spend at most budget_left. Spread K posts across R rounds (at most one per round)."""
    if budget_left <= 0:
        return None
    # remaining rounds including this one
    remain = max(1, rounds - round_index)
    # post this round if we still need to spend and a coin flip weighted by leftover budget
    p = min(1.0, budget_left / float(remain))
    if rng.random() > p:
        return None
    payload = generate_one("redteam", event, card, rng, mutation_style="rhetoric")
    direction = attack_direction(event, card)
    payload["peg_sentiment"] = direction
    payload["stance"] = "panic" if direction == "bearish" else "reassurance"
    payload["intent"] = "persuade" if direction == "bullish" else "alarm"
    if hallucination_flag(payload["text"], card):
        return None
    p_ai = detector_p_ai(payload["text"])
    if p_ai > float(tau):
        return None
    payload["detector_p_ai"] = p_ai
    payload["author_id"] = author_id
    payload["is_redteam"] = True
    payload["is_rebroadcast"] = False
    return payload
