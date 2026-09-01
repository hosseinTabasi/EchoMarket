"""Protocol calibration checks and round-to-clock mapping. Author: Hossein Tabasi.

Does not invent peg prints. E01-E02 may align 12 rounds to the sourced day; others N/A.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

PROTOCOL_PRIORS = {
    "official": 80,
    "journalist": 65,
    "whale": 60,
    "analyst": 62,
    "bot": 55,
    "retail_panic": 50,
    "retail_skeptical": 70,
    "retail_apathetic": 65,
}
PROTOCOL_P_POST = {
    "official": 0.40,
    "journalist": 0.55,
    "whale": 0.25,
    "analyst": 0.35,
    "bot": 0.70,
    "retail_panic": 0.45,
    "retail_skeptical": 0.20,
    "retail_apathetic": 0.08,
}
PROTOCOL_ABG = {
    "official": (0.4, 0.2, 8.0),
    "journalist": (1.2, 0.8, 6.0),
    "whale": (1.5, 1.0, 5.0),
    "analyst": (1.0, 1.2, 7.0),
    "bot": (2.0, 0.3, 2.0),
    "retail_panic": (2.5, 0.6, 1.5),
    "retail_skeptical": (0.8, 1.0, 6.0),
    "retail_apathetic": (0.3, 0.2, 1.0),
}


def check_config(cfg: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    if not cfg.get("_smoke"):
        if int(cfg.get("n_agents", 0)) != 120:
            errs.append("study config n_agents must be 120 (use --smoke for N=12)")
        if int(cfg.get("rounds", 0)) != 12:
            errs.append("study config rounds must be 12")
        seeds = cfg.get("seeds") or []
        if list(seeds) != [20260311, 20260813, 20260101]:
            errs.append("seeds must be [20260311, 20260813, 20260101]")
    priors = cfg.get("priors") or {}
    for role, v in PROTOCOL_PRIORS.items():
        if float(priors.get(role, v)) != float(v):
            errs.append(f"prior mismatch {role}")
    for role, v in PROTOCOL_P_POST.items():
        if abs(float((cfg.get("p_post") or {}).get(role, v)) - v) > 1e-9:
            errs.append(f"p_post mismatch {role}")
    for role, trip in PROTOCOL_ABG.items():
        a = float((cfg.get("alpha") or {}).get(role, trip[0]))
        b = float((cfg.get("beta") or {}).get(role, trip[1]))
        g = float((cfg.get("gamma") or {}).get(role, trip[2]))
        if (a, b, g) != trip:
            errs.append(f"alpha/beta/gamma mismatch {role}")
    return errs


def round_clock(event_id: str, round_index: int, rounds: int = 12) -> Optional[str]:
    """Align rounds to sourced calendar language. No invented hourly prints."""
    if event_id == "E01":
        return f"2023-03-11 sourced depeg window, round {round_index + 1}/{rounds} (peg unrecovered that day)"
    if event_id == "E02":
        if round_index < max(1, rounds // 3):
            return f"2023-03-12 before/around 18:15 ET joint statement, round {round_index + 1}/{rounds}"
        return f"2023-03-12 announcement through Monday 13 Mar recovery window, round {round_index + 1}/{rounds}"
    return None  # [UNKNOWN] path: no clock


def fidelity_applicable(card: Dict[str, Any]) -> bool:
    path = str(card.get("price_or_peg_path_72h") or "")
    return "[UNKNOWN]" not in path and path.strip() != ""
