#!/usr/bin/env python3
"""EchoMarket pre-registered N=120 R=12 3-seed study driver.

Author: Hossein Tabasi
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import traceback
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.io_utils import CONFIG, DATA, load_yaml, read_jsonl, write_json, write_jsonl  # noqa: E402
from src.run import load_event_card, simulate  # noqa: E402
from src.update import held_sentiment, herding_index  # noqa: E402

STUDY = DATA / "study"
SEEDS = [20260311, 20260813, 20260101]
TAUS = [0.3, 0.5, 0.7, 1.0]
DEV_EVENTS = [f"E0{i}" for i in range(1, 9)]
TEST_EVENTS = ["E09", "E10"]
ALL_EVENTS = DEV_EVENTS + TEST_EVENTS
SPLIT = {**{e: "dev" for e in DEV_EVENTS}, **{e: "test" for e in TEST_EVENTS}}


def _mean(xs: Sequence[float]) -> float:
    xs = list(xs)
    if not xs:
        return 0.0
    return float(sum(xs) / len(xs))


def cell_name(event_id: str, condition: str, seed: int, tau: float, shuffle: bool) -> str:
    cond = "C-shuffled" if (condition == "C" and shuffle) else condition
    return f"{event_id}_{cond}_seed{seed}_tau{tau:g}"


def build_grid() -> List[Dict[str, Any]]:
    cells: List[Dict[str, Any]] = []
    for e in DEV_EVENTS:
        for s in SEEDS:
            cells.append({"event": e, "condition": "B", "seed": s, "tau": 1.0, "shuffle": False})
    for e in ALL_EVENTS:
        for s in SEEDS:
            cells.append({"event": e, "condition": "C", "seed": s, "tau": 1.0, "shuffle": False})
    for e in ALL_EVENTS:
        for s in SEEDS:
            cells.append({"event": e, "condition": "C", "seed": s, "tau": 1.0, "shuffle": True})
    for cond in ("D", "E-factcheck", "E-ratelimit", "E-detector"):
        for e in ALL_EVENTS:
            for s in SEEDS:
                for tau in TAUS:
                    cells.append({"event": e, "condition": cond, "seed": s, "tau": tau, "shuffle": False})
    return cells


def compact_record(bundle: Dict[str, Any], elapsed_s: float) -> Dict[str, Any]:
    world = bundle["world"]
    posts = bundle["posts"]
    snaps = bundle["snapshots"]
    metrics = bundle["metrics"]
    agents = bundle["agents"]
    counts = bundle.get("study_counts") or {}
    start_mean = float(bundle["start_mean"])
    end_mean = float(metrics["belief"]["mean"])
    tau = float(world.get("tau", 1.0))
    condition = str(world.get("condition") or "")
    defense = None
    if condition == "E-factcheck":
        defense = "factcheck"
    elif condition == "E-ratelimit":
        defense = "ratelimit"
    elif condition == "E-detector":
        defense = "detector"

    role_means: List[Dict[str, float]] = []
    herding: List[float] = []
    pop_means: List[float] = []
    for snap in snaps:
        off = [float(a["peg_confidence"]) for a in snap if a.get("role") == "official"]
        pan = [float(a["peg_confidence"]) for a in snap if a.get("role") == "retail_panic"]
        pop = [float(a["peg_confidence"]) for a in snap]
        role_means.append(
            {
                "official": _mean(off),
                "retail_panic": _mean(pan),
                "population": _mean(pop),
            }
        )
        pop_means.append(_mean(pop))
        herding.append(herding_index([held_sentiment(float(a["peg_confidence"])) for a in snap]))

    role_by_id = {a["agent_id"]: a.get("role") for a in agents}
    n_posts = len(posts)
    n_red = sum(1 for p in posts if p.get("is_redteam"))
    hall = float(metrics.get("factuality_hard_hallucination_rate") or 0.0)
    red_hall = float(metrics.get("redteam_hallucination_rate") or 0.0)
    n_flagged = sum(1 for p in posts if p.get("C_flag"))
    n_gated = int(counts.get("n_gated") or 0)
    n_rate_limited = int(counts.get("n_rate_limited") or 0)
    n_rebroadcast_attempts = int(counts.get("n_rebroadcast_attempts") or 0)
    n_official_gated = int(counts.get("n_official_gated") or 0)
    n_official_attempted = int(counts.get("n_official_attempted") or 0)
    official_posts = [p for p in posts if role_by_id.get(p.get("author_id")) == "official"]
    n_official_kept = len(official_posts)

    if defense == "detector":
        n_attempts = n_gated + n_posts
        detection_rate = n_gated / float(n_attempts) if n_attempts else 0.0
        n_off_tot = n_official_attempted if n_official_attempted else (n_official_kept + n_official_gated)
        official_fp = n_official_gated / float(n_off_tot) if n_off_tot else 0.0
        n_official_flagged = n_official_gated
    elif defense == "factcheck":
        detection_rate = n_flagged / float(n_posts) if n_posts else 0.0
        n_official_flagged = sum(1 for p in official_posts if p.get("C_flag"))
        official_fp = n_official_flagged / float(n_official_kept) if n_official_kept else 0.0
    elif defense == "ratelimit":
        detection_rate = n_rate_limited / float(n_rebroadcast_attempts) if n_rebroadcast_attempts else 0.0
        n_official_flagged = 0
        official_fp = 0.0
    else:
        n_over = sum(1 for p in posts if float(p.get("detector_p_ai") or 0.0) > tau)
        detection_rate = n_over / float(n_posts) if n_posts else 0.0
        n_official_flagged = sum(1 for p in official_posts if float(p.get("detector_p_ai") or 0.0) > tau)
        official_fp = n_official_flagged / float(n_official_kept) if n_official_kept else 0.0

    return {
        "world": world,
        "metrics": metrics,
        "start_mean": start_mean,
        "end_mean": end_mean,
        "delta_belief": end_mean - start_mean,
        "role_means_by_round": role_means,
        "herding_by_round": herding,
        "mean_confidence_by_round": pop_means,
        "herding_mean_rounds_4_12": _mean(herding[3:]) if len(herding) >= 4 else _mean(herding),
        "posts_summary": {
            "n_posts": n_posts,
            "n_red": n_red,
            "hallucination_rate": hall,
            "redteam_hallucination_rate": red_hall,
            "detection_rate": detection_rate,
            "official_fp_rate": official_fp,
            "n_official_posts": n_official_kept,
            "n_official_flagged": n_official_flagged,
            "n_gated": n_gated,
            "n_flagged": n_flagged,
            "n_rate_limited": n_rate_limited,
            "n_rebroadcast_attempts": n_rebroadcast_attempts,
        },
        "elapsed_s": elapsed_s,
        "ok": True,
    }


def c_post_rows(bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    world = bundle["world"]
    role_by_id = {a["agent_id"]: a.get("role") for a in bundle["agents"]}
    rows: List[Dict[str, Any]] = []
    for p in bundle["posts"]:
        if p.get("is_rebroadcast"):
            continue
        if p.get("generator") != "prompt-only-decoder":
            continue
        txt = (p.get("text") or "").strip()
        if not txt:
            continue
        rows.append(
            {
                "event_id": world["event_id"],
                "split": world.get("split"),
                "seed": world["seed"],
                "condition": "C",
                "text": txt,
                "generator": "prompt-only-decoder",
                "role": role_by_id.get(p.get("author_id")),
                "peg_sentiment": p.get("peg_sentiment"),
            }
        )
    return rows


def run_cell(spec: Dict[str, Any]) -> Dict[str, Any]:
    event_id = spec["event"]
    condition = spec["condition"]
    seed = int(spec["seed"])
    tau = float(spec["tau"])
    shuffle = bool(spec["shuffle"])
    key = cell_name(event_id, condition, seed, tau, shuffle)
    out_path = STUDY / f"{key}.json"
    t0 = time.time()
    if out_path.exists():
        try:
            rec = json.loads(out_path.read_text(encoding="utf-8"))
            if rec.get("ok"):
                return {
                    "key": key,
                    "ok": True,
                    "skipped": True,
                    "elapsed_s": float(rec.get("elapsed_s") or 0.0),
                    "path": str(out_path),
                    "error": None,
                }
        except Exception:
            pass
    try:
        cfg = load_yaml(CONFIG / "default.yaml")
        cfg["event_id"] = event_id
        cfg["condition"] = condition
        cfg["seed"] = seed
        cfg["tau"] = tau
        cfg["n_agents"] = 120
        cfg["rounds"] = 12
        cfg["red_budget_k"] = 8
        cfg["shuffle_graph"] = shuffle
        event, card = load_event_card(event_id)
        bundle = simulate(cfg, event, card)
        elapsed = time.time() - t0
        rec = compact_record(bundle, elapsed)
        rec["key"] = key
        write_json(out_path, rec)
        if condition == "C" and not shuffle:
            posts_path = STUDY / "posts_c" / f"{event_id}_seed{seed}.jsonl"
            write_jsonl(posts_path, c_post_rows(bundle))
        return {
            "key": key,
            "ok": True,
            "skipped": False,
            "elapsed_s": elapsed,
            "path": str(out_path),
            "error": None,
        }
    except Exception as exc:
        elapsed = time.time() - t0
        err = f"{type(exc).__name__}: {exc}"
        fail = {
            "key": key,
            "ok": False,
            "error": err,
            "traceback": traceback.format_exc(),
            "elapsed_s": elapsed,
            "world": {
                "event_id": event_id,
                "condition": condition,
                "seed": seed,
                "tau": tau,
                "shuffle_graph": shuffle,
            },
        }
        write_json(out_path, fail)
        return {
            "key": key,
            "ok": False,
            "skipped": False,
            "elapsed_s": elapsed,
            "path": str(out_path),
            "error": err,
        }


def load_ok_runs():
    out = {}
    if not STUDY.exists():
        return out
    for pth in sorted(STUDY.glob("*.json")):
        if pth.name in {"INDEX.json", "detectability.json"}:
            continue
        try:
            rec = json.loads(pth.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not rec.get("ok"):
            continue
        key = rec.get("key") or pth.stem
        out[key] = rec
    return out


def fmt3(x):
    if x is None:
        return "N/A"
    if isinstance(x, str):
        return x
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return "N/A"
    return f"{float(x):.3f}"


def fmt_t20(vals):
    nums = []
    for v in vals:
        if v is None or v == "TO RUN":
            continue
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            continue
    if not nums:
        return "—"
    if len(nums) < len(vals):
        return f"{_mean(nums):.3f} ({len(nums)}/{len(vals)} seeds)"
    return fmt3(_mean(nums))


def mean_field(recs, path):
    vals = []
    for r in recs:
        cur = r
        ok = True
        for k in path:
            if not isinstance(cur, dict) or k not in cur:
                ok = False
                break
            cur = cur[k]
        if ok and isinstance(cur, (int, float)):
            vals.append(float(cur))
    if not vals:
        return None
    return _mean(vals)


def recs_for(runs, event, condition, tau=None):
    out = []
    t = 1.0 if tau is None else tau
    for s in SEEDS:
        if condition == "C-shuffled":
            key = cell_name(event, "C", s, t, True)
        else:
            key = cell_name(event, condition, s, t, False)
        r = runs.get(key)
        if r and r.get("ok"):
            out.append(r)
    return out




def e01_overshoot(path):
    best_t = None
    best_gap = None
    max_gap = None
    max_gap_t = None
    for t_idx in range(min(6, len(path))):
        row = path[t_idx]
        gap = float(row["official"]) - float(row["retail_panic"])
        pop = float(row["population"])
        off = float(row["official"])
        if max_gap is None or gap > max_gap:
            max_gap = gap
            max_gap_t = t_idx + 1
        if gap >= 5.0 and pop < off:
            if best_t is None:
                best_t = t_idx + 1
                best_gap = gap
    if best_t is None:
        return "no", "max gap %s at t=%s (threshold 5 not met or pop not below official)" % (fmt3(max_gap), max_gap_t)
    return str(best_t), fmt3(best_gap)


def e02_lag(path):
    if len(path) < 3:
        return "no (path too short)"
    lag_ok = False
    lag_end = None
    for i in range(1, len(path) - 1):
        g0 = float(path[i]["official"]) - float(path[i]["retail_panic"])
        g1 = float(path[i + 1]["official"]) - float(path[i + 1]["retail_panic"])
        if g0 >= 3.0 and g1 >= 3.0:
            lag_ok = True
            lag_end = i + 1
            break
    if not lag_ok:
        best = 0
        cur = 0
        for i in range(1, len(path)):
            gap = float(path[i]["official"]) - float(path[i]["retail_panic"])
            if gap >= 3.0:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return "no (max consecutive rounds after r1 with gap>=3: %s)" % best
    for j in range(lag_end, len(path) - 1):
        off_up = float(path[j + 1]["official"]) > float(path[j]["official"])
        pan_up = float(path[j + 1]["retail_panic"]) > float(path[j]["retail_panic"])
        if off_up and pan_up:
            return "yes"
    return "no (lag observed but both roles did not subsequently rise)"


def avg_role_path(recs):
    if not recs:
        return []
    n_r = min(len(r.get("role_means_by_round") or []) for r in recs)
    out = []
    for t in range(n_r):
        out.append({
            "official": _mean(float(r["role_means_by_round"][t]["official"]) for r in recs),
            "retail_panic": _mean(float(r["role_means_by_round"][t]["retail_panic"]) for r in recs),
            "population": _mean(float(r["role_means_by_round"][t]["population"]) for r in recs),
        })
    return out


def write_index(entries, wall):
    ok = [e for e in entries if e.get("ok")]
    fail = [e for e in entries if not e.get("ok")]
    obj = {
        "author": "Hossein Tabasi",
        "n_agents": 120,
        "rounds": 12,
        "seeds": SEEDS,
        "tau_grid": TAUS,
        "generator": "prompt-only-decoder",
        "n_runs": len(entries),
        "n_ok": len(ok),
        "n_fail": len(fail),
        "wall_elapsed_s": wall,
        "sum_run_elapsed_s": sum(float(e.get("elapsed_s") or 0.0) for e in entries),
        "runs": [
            {
                "key": e["key"],
                "elapsed_s": e.get("elapsed_s"),
                "ok": e.get("ok"),
                "skipped": e.get("skipped"),
                "error": e.get("error"),
                "path": e.get("path"),
            }
            for e in entries
        ],
    }
    write_json(STUDY / "INDEX.json", obj)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=max(1, cpu_count()))
    parser.add_argument("--fill-only", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    STUDY.mkdir(parents=True, exist_ok=True)
    (STUDY / "posts_c").mkdir(parents=True, exist_ok=True)
    grid = build_grid()
    print("grid cells=%s workers=%s" % (len(grid), args.workers), flush=True)
    wall0 = time.time()
    entries = []
    if args.fill_only:
        for spec in grid:
            key = cell_name(spec["event"], spec["condition"], spec["seed"], spec["tau"], spec["shuffle"])
            path = STUDY / ("%s.json" % key)
            if not path.exists():
                entries.append({"key": key, "ok": False, "elapsed_s": 0.0, "error": "missing", "skipped": False, "path": str(path)})
                continue
            rec = json.loads(path.read_text(encoding="utf-8"))
            entries.append({"key": key, "ok": bool(rec.get("ok")), "elapsed_s": float(rec.get("elapsed_s") or 0.0), "error": rec.get("error"), "skipped": True, "path": str(path)})
    else:
        first_spec = {"event": "E01", "condition": "C", "seed": 20260311, "tau": 1.0, "shuffle": False}
        print("timing first cell C E01 seed 20260311 ...", flush=True)
        first = run_cell(first_spec)
        print("first %s ok=%s skipped=%s elapsed_s=%.3f err=%s" % (first["key"], first["ok"], first.get("skipped"), first["elapsed_s"], first.get("error")), flush=True)
        entries.append(first)
        rest = []
        for spec in grid:
            key = cell_name(spec["event"], spec["condition"], spec["seed"], spec["tau"], spec["shuffle"])
            if key == first["key"]:
                continue
            rest.append(spec)
        if args.limit and args.limit > 0:
            rest = rest[: max(0, args.limit - 1)]
        n_workers = max(1, int(args.workers))
        if n_workers == 1 or len(rest) == 0:
            for spec in rest:
                r = run_cell(spec)
                entries.append(r)
                print("%s ok=%s skipped=%s elapsed_s=%.2f" % (r["key"], r["ok"], r.get("skipped"), r["elapsed_s"]), flush=True)
        else:
            with Pool(processes=n_workers, maxtasksperchild=4) as pool:
                for r in pool.imap_unordered(run_cell, rest):
                    entries.append(r)
                    print("%s ok=%s skipped=%s elapsed_s=%.2f err=%s" % (r["key"], r["ok"], r.get("skipped"), r["elapsed_s"], r.get("error")), flush=True)
    wall = time.time() - wall0
    write_index(entries, wall)
    print("wrote", STUDY / "INDEX.json", "n=%s wall_s=%.1f" % (len(entries), wall), flush=True)
    return 0 if all(e.get("ok") for e in entries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
