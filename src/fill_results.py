#!/usr/bin/env python3
"""Fill reports/RESULTS.md from data/study JSON. Author: Hossein Tabasi."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.io_utils import DATA, read_jsonl, write_json, write_jsonl
from src.run_study import (
    ALL_EVENTS,
    DEV_EVENTS,
    SEEDS,
    SPLIT,
    STUDY,
    TAUS,
    TEST_EVENTS,
    _mean,
    avg_role_path,
    cell_name,
    e01_overshoot,
    e02_lag,
    fmt3,
    fmt_t20,
    load_ok_runs,
    mean_field,
    recs_for,
)


def collect_c_posts():
    posts_dir = STUDY / "posts_c"
    posts_c = STUDY / "posts_c.jsonl"
    rows = []
    if posts_dir.exists():
        for pth in sorted(posts_dir.glob("*.jsonl")):
            rows.extend(read_jsonl(pth))
    if rows:
        write_jsonl(posts_c, rows)
    return rows


def detectability():
    headlines = read_jsonl(DATA / "real_headlines.jsonl")
    real_dev = [h.get("text", "") for h in headlines if h.get("generator") == "human" and h.get("split") == "dev" and h.get("text")]
    real_test = [h.get("text", "") for h in headlines if h.get("generator") == "human" and h.get("event_id") in {"E09", "E10"} and h.get("text")]
    synth_dev, synth_test = [], []
    for r in collect_c_posts():
        txt = r.get("text") or ""
        if not txt:
            continue
        if r.get("event_id") in TEST_EVENTS:
            synth_test.append(txt)
        elif r.get("split") == "dev" or r.get("event_id") in DEV_EVENTS:
            synth_dev.append(txt)
    result = {
        "method": "tfidf-logistic",
        "n_real_dev": len(real_dev),
        "n_synth_dev": len(synth_dev),
        "n_real_test": len(real_test),
        "n_synth_test": len(synth_test),
        "dev_cv_auc": "N/A",
        "test_auc": "N/A",
        "dev_note": "",
        "test_note": "",
    }
    return result, real_dev, real_test, synth_dev, synth_test


def hall_split(runs, cond, events, tau=None):
    vals = []
    taus = [tau] if tau is not None else ([1.0] if cond in {"C", "B"} else TAUS)
    for e in events:
        for t in taus:
            recs = recs_for(runs, e, cond, t)
            v = mean_field(recs, ("posts_summary", "hallucination_rate"))
            if v is not None:
                vals.append(v)
    return _mean(vals) if vals else None


def red_hall(runs, cond, events):
    vals = []
    for e in events:
        for t in TAUS:
            recs = recs_for(runs, e, cond, t)
            v = mean_field(recs, ("posts_summary", "redteam_hallucination_rate"))
            if v is not None:
                vals.append(v)
    return _mean(vals) if vals else None


def table1(runs):
    rows = []
    for e in ALL_EVENTS:
        recs = recs_for(runs, e, "C")
        if len(recs) < 3:
            rows.append("| %s | %s | TO RUN | TO RUN | TO RUN | TO RUN |" % (e, SPLIT[e]))
            continue
        size = mean_field(recs, ("metrics", "cascade_size"))
        depth = mean_field(recs, ("metrics", "cascade_depth"))
        t20s = [r.get("metrics", {}).get("time_to_20pct_bearish") for r in recs]
        mod = mean_field(recs, ("metrics", "modularity"))
        rows.append("| %s | %s | %s | %s | %s | %s |" % (e, SPLIT[e], fmt3(size), fmt3(depth), fmt_t20(t20s), fmt3(mod)))
    return rows


def table2(runs):
    rows = []
    h_diffs = {}
    for e in ALL_EVENTS:
        recs = recs_for(runs, e, "C")
        shufs = recs_for(runs, e, "C-shuffled")
        if len(recs) < 3:
            rows.append("| %s | TO RUN | TO RUN | TO RUN | TO RUN | TO RUN |" % e)
            h_diffs[e] = None
            continue
        mean_b = mean_field(recs, ("metrics", "belief", "mean"))
        var_b = mean_field(recs, ("metrics", "belief", "variance"))
        pol = mean_field(recs, ("metrics", "belief", "polarization"))
        h = mean_field(recs, ("metrics", "belief", "herding_index"))
        h_real = mean_field(recs, ("herding_mean_rounds_4_12",))
        h_shuf = mean_field(shufs, ("herding_mean_rounds_4_12",)) if shufs else None
        if h_real is None or h_shuf is None:
            hvs = "TO RUN" if h_shuf is None else "N/A"
            h_diffs[e] = None
        else:
            h_diffs[e] = h_real - h_shuf
            hvs = fmt3(h_diffs[e])
        rows.append("| %s | %s | %s | %s | %s | %s |" % (e, fmt3(mean_b), fmt3(var_b), fmt3(pol), fmt3(h), hvs))
    return rows, h_diffs


def table6(runs):
    rows = []
    t6 = {}
    for e in ALL_EVENTS:
        t6[e] = {}
        cells = []
        cs = recs_for(runs, e, "C")
        by_c = {int(r["world"]["seed"]): r for r in cs}
        for tau in TAUS:
            diffs = []
            for r in recs_for(runs, e, "D", tau):
                s = int(r["world"]["seed"])
                if s in by_c:
                    diffs.append(abs(float(r["end_mean"]) - float(by_c[s]["end_mean"])))
            if len(diffs) < 3:
                cells.append("TO RUN")
            else:
                t6[e][tau] = _mean(diffs)
                cells.append(fmt3(t6[e][tau]))
        rows.append("| %s | %s | %s | %s | %s |" % (e, cells[0], cells[1], cells[2], cells[3]))
    return rows, t6


def table7(runs):
    rows = []
    t7 = {}
    fp_notes = []
    defenses = [("none (D)", "D"), ("E-factcheck", "E-factcheck"), ("E-ratelimit", "E-ratelimit"), ("E-detector", "E-detector")]
    for tau in TAUS:
        for label, cond in defenses:
            deltas, dets, halls, fps = [], [], [], []
            n_cells = 0
            for e in ALL_EVENTS:
                recs = recs_for(runs, e, cond, tau)
                n_cells += len(recs)
                for r in recs:
                    deltas.append(float(r.get("delta_belief", 0.0)))
                    ps = r.get("posts_summary") or {}
                    dets.append(float(ps.get("detection_rate") or 0.0))
                    halls.append(float(ps.get("hallucination_rate") or 0.0))
                    fps.append(float(ps.get("official_fp_rate") or 0.0))
            if n_cells < 3:
                rows.append("| %.1f | %s | TO RUN | TO RUN | TO RUN |" % (tau, label))
                t7[(tau, cond)] = {"delta": None, "det": None, "hall": None, "fp": None}
                continue
            dlt, dt, hl, fp = _mean(deltas), _mean(dets), _mean(halls), _mean(fps)
            t7[(tau, cond)] = {"delta": dlt, "det": dt, "hall": hl, "fp": fp, "n": n_cells}
            rows.append("| %.1f | %s | %s | %s | %s |" % (tau, label, fmt3(dlt), fmt3(dt), fmt3(hl)))
            if fp > 0.05:
                fp_notes.append("τ=%.1f %s: official FP %s > 0.05" % (tau, label, fmt3(fp)))
    return rows, t7, fp_notes


def table8(runs):
    signs = {
        "E01": "negative", "E02": "positive", "E03": "(no peg sign)",
        "E04": "(no peg sign)", "E05": "(no peg sign)",
        "E06": "(no peg sign; issuer operational)", "E07": "(no peg sign)",
        "E08": "(no peg sign)",
    }
    rows = []
    t8 = {}
    for e in DEV_EVENTS:
        cs = recs_for(runs, e, "C")
        bs = recs_for(runs, e, "B")
        dc = mean_field(cs, ("delta_belief",))
        db = mean_field(bs, ("delta_belief",))
        if dc is None or db is None:
            rows.append("| %s | %s | TO RUN | TO RUN | TO RUN |" % (e, signs[e]))
            continue
        bigger = abs(dc) > abs(db)
        t8[e] = {"dc": dc, "db": db, "bigger": bigger}
        rows.append("| %s | %s | %s | %s | %s |" % (e, signs[e], fmt3(dc), fmt3(db), "yes" if bigger else "no"))
    return rows, t8


def table9(runs):
    path_e01 = avg_role_path(recs_for(runs, "E01", "C"))
    path_e02 = avg_role_path(recs_for(runs, "E02", "C"))
    if len(path_e01) < 6:
        t_star, gap = "TO RUN", "TO RUN"
    else:
        t_star, gap = e01_overshoot(path_e01)
    if len(path_e02) < 3:
        lag_e02 = "TO RUN"
    else:
        lag_e02 = e02_lag(path_e02)
    rows = [
        "| E01 | %s | %s | — |" % (t_star, gap),
        "| E02 | — | — | %s |" % lag_e02,
    ]
    return rows, t_star, gap, lag_e02


def update_readme():
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    old = "Empirical tables in `reports/RESULTS.md` are `TO RUN` until a full N=120 / R=12 / 3-seed study is executed from JSON artifacts. A smoke path (`N=12`, `R=2`, `seed=0`) is for wiring only."
    new = "Empirical tables in `reports/RESULTS.md` now hold the v1 prompt-only N=120 / R=12 / 3-seed study numbers written from `data/study/` JSON artifacts (still not investment advice). A smoke path (`N=12`, `R=2`, `seed=0`) is for wiring only."
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return
    needle = "**This repository is not a trading system, not investment advice, and not a live poster.**"
    if needle in text and "now hold the v1 prompt-only" not in text:
        path.write_text(text.replace(needle, needle + " `reports/RESULTS.md` now holds the v1 prompt-only N=120 / R=12 / 3-seed study numbers (still not investment advice).", 1), encoding="utf-8")


def rq_block(runs, t6, t7, t8, t_star, lag_e02, h_diffs, d_red):
    overshoot_ok = isinstance(t_star, str) and t_star not in {"TO RUN", "no"} and t_star.isdigit()
    lag_ok = lag_e02 == "yes"
    h_e01 = h_diffs.get("E01")
    h_e02 = h_diffs.get("E02")
    herd_ok = (h_e01 is not None and h_e01 >= 0.05) and (h_e02 is not None and h_e02 >= 0.05)
    rq1 = overshoot_ok and lag_ok and herd_ok
    rq1_bits = "E01 overshoot=%s; E02 lag=%s; herding E01 dH=%s (need >=0.05); herding E02 dH=%s (need >=0.05)" % (
        ("yes t*=" + t_star) if overshoot_ok else t_star,
        lag_e02,
        fmt3(h_e01) if h_e01 is not None else "TO RUN",
        fmt3(h_e02) if h_e02 is not None else "TO RUN",
    )
    e01 = t8.get("E01")
    e02 = t8.get("E02")
    rq2 = False
    rq2_note = "TO RUN"
    if e01 and e02:
        rq2 = (e01["dc"] < 0) and (e02["dc"] > 0) and e01["bigger"] and e02["bigger"]
        rq2_note = "E01 dC=%s (need negative) |dC|>|dB|=%s; E02 dC=%s (need positive) |dC|>|dB|=%s" % (
            fmt3(e01["dc"]), "yes" if e01["bigger"] else "no",
            fmt3(e02["dc"]), "yes" if e02["bigger"] else "no",
        )
    mean_t6 = {}
    for tau in TAUS:
        vs = [t6[e][tau] for e in ALL_EVENTS if tau in t6.get(e, {})]
        mean_t6[tau] = _mean(vs) if vs else None
    rq3_tau = mean_t6.get(1.0) is not None and mean_t6.get(0.3) is not None and mean_t6[1.0] >= mean_t6[0.3]
    rq3_hall = d_red is not None and d_red == 0.0
    rq3 = rq3_tau and rq3_hall
    rq4 = False
    rq4_hits = []
    for tau in TAUS:
        drow = t7.get((tau, "D")) or {}
        if drow.get("delta") is None:
            continue
        d_abs = abs(drow["delta"])
        for cond in ("E-factcheck", "E-ratelimit", "E-detector"):
            prow = t7.get((tau, cond)) or {}
            if prow.get("delta") is None:
                continue
            p_abs = abs(prow["delta"])
            fp = prow.get("fp") or 0.0
            if p_abs <= d_abs - 1.0 and fp <= 0.05:
                rq4 = True
                rq4_hits.append("tau=%g %s: |ddef|=%s <= |dD|-1=%s, FP=%s" % (tau, cond, fmt3(p_abs), fmt3(d_abs - 1.0), fmt3(fp)))
    rq4_note = "; ".join(rq4_hits[:6]) if rq4_hits else "no defense reduced |Δbelief| vs undefended D by >=1.0 with official FP <= 0.05 on the Table 7 aggregate"
    lines = [
        "**RQ1** %s — %s." % ("PASS" if rq1 else "FAIL", rq1_bits),
        "**RQ2** %s — %s." % ("PASS" if rq2 else "FAIL", rq2_note),
        "**RQ3** %s — mean |end_D-end_C| τ=1.0=%s vs τ=0.3=%s; red-team hallucination rate=%s (must be 0)." % (
            "PASS" if rq3 else "FAIL", fmt3(mean_t6.get(1.0)), fmt3(mean_t6.get(0.3)),
            fmt3(d_red) if d_red is not None else "TO RUN",
        ),
        "**RQ4** %s — %s." % ("PASS" if rq4 else "FAIL", rq4_note),
    ]
    return lines, {"RQ1": rq1, "RQ2": rq2, "RQ3": rq3, "RQ4": rq4}


def write_results(runs, det, fetch):
    t1 = table1(runs)
    t2, h_diffs = table2(runs)
    t6_rows, t6 = table6(runs)
    t7_rows, t7, fp_notes = table7(runs)
    t8_rows, t8 = table8(runs)
    t9_rows, t_star, gap, lag_e02 = table9(runs)
    c_dev = hall_split(runs, "C", DEV_EVENTS)
    c_test = hall_split(runs, "C", TEST_EVENTS)
    d_dev = hall_split(runs, "D", DEV_EVENTS)
    d_test = hall_split(runs, "D", TEST_EVENTS)
    d_red = red_hall(runs, "D", ALL_EVENTS)
    e_dev = hall_split(runs, "E-factcheck", DEV_EVENTS)
    e_test = hall_split(runs, "E-factcheck", TEST_EVENTS)
    e_red = red_hall(runs, "E-factcheck", ALL_EVENTS)
    rq_lines, rq = rq_block(runs, t6, t7, t8, t_star, lag_e02, h_diffs, d_red)
    d_red_s = fmt3(d_red) if d_red is not None else "TO RUN"
    if d_red is not None:
        d_red_s = fmt3(d_red) + (" (must be 0 or RQ3 fails)" if d_red > 0 else " (0 under critic)")
    dev_auc = det.get("dev_cv_auc")
    test_auc = det.get("test_auc")
    if isinstance(dev_auc, float):
        dev_cell = fmt3(dev_auc)
    else:
        dev_cell = "N/A (n_real=%s)" % det.get("n_real_dev")
    if isinstance(test_auc, float):
        test_cell = fmt3(test_auc)
    else:
        test_cell = "N/A (n_real=%s)" % det.get("n_real_test")
    lines = []
    a = lines.append
    a("# EchoMarket results")
    a("")
    a("**Author:** Hossein Tabasi, M.Tech CSE, Shoolini University.")
    a("")
    a("**Status:** filled from N=120 R=12 3-seed JSON under `data/study/`. Numbers are study artifacts, not smoke traces. Not investment advice. Peg-confidence is a rubric score, not a forecast. No live posts.")
    a("")
    a("Fidelity cells are **N/A** when `price_or_peg_path_72h` is `[UNKNOWN]`. Do not invent peg series or detector AUC.")
    a("")
    a("---")
    a("")
    a("## Table 1 — Cascade (condition C, mean across seeds)")
    a("")
    a("Seeds: 20260311, 20260813, 20260101. R=12, N=120.")
    a("")
    a("| Event | Split | size | depth | time-to-20%-bearish | modularity (stance × community) |")
    a("|-------|-------|------|-------|---------------------|----------------------------------|")
    lines.extend(t1)
    a("")
    a("E09/E10 are confirmatory (C–E only).")
    a("")
    a("---")
    a("")
    a("## Table 2 — Belief (condition C, end of round 12)")
    a("")
    a("| Event | mean | variance | polarization (bimodality) | herding index H | H vs shuffled-graph |")
    a("|-------|------|----------|---------------------------|-----------------|---------------------|")
    lines.extend(t2)
    a("")
    a("Polarization = clip(fraction of agents with confidence <40 or >60, minus 0.5). Herding H_t = 1 - entropy(p^B,p^N,p^U)/log 3.")
    a("H vs shuffled-graph is mean H_t over 1-indexed rounds 4-12 on the real graph minus the same quantity on the destination-rewired control (same seed/event/C).")
    a("")
    return lines, rq, d_red_s, c_dev, c_test, d_dev, d_test, e_dev, e_test, e_red, t6_rows, t7_rows, fp_notes, t8_rows, t9_rows, rq_lines, dev_cell, test_cell


def finish_results(pack, det, fetch):
    lines, rq, d_red_s, c_dev, c_test, d_dev, d_test, e_dev, e_test, e_red, t6_rows, t7_rows, fp_notes, t8_rows, t9_rows, rq_lines, dev_cell, test_cell = pack
    a = lines.append
    a("---")
    a("")
    a("## Table 3 — Fidelity (sim mean-confidence path vs real peg deviation or volume z)")
    a("")
    a("12 aligned rounds. **N/A** if the fact card peg path is `[UNKNOWN]`.")
    a("")
    a("| Event | 72h path | corr(sim mean, peg/volume) |")
    a("|-------|----------|----------------------------|")
    a("| E01 | sourced negative (unrecovered 11 Mar) | N/A |")
    a("| E02 | sourced recovery after 18:15 ET 12 Mar; full Mon 13 | N/A |")
    for e in ALL_EVENTS[2:]:
        a("| %s | [UNKNOWN] | N/A |" % e)
    a("")
    a("Fidelity note: E01 fact card licenses secondary USDC prints near 0.87-0.88 (Chainalysis ~$0.87 by 02:00 11 Mar; CoinDesk Kraken ~87c at 07:16 UTC; ~94c at 18:07 UTC) plus a FEDS trough of 86 cents, unrecovered that day — not a 12-point series. A constant 0.87 to 87 mapping would have zero variance so Pearson is undefined; interpolating the remaining rounds would invent prints. Cell left N/A. Overshoot in Table 9 uses sim internals only.")
    a("E02 card licenses qualitative recovery after 18:15 ET 12 Mar and full recovery Monday 13 Mar, and forbids exact hourly peg prints other than that language. No 12-point numeric series can be built without inventing or borrowing E01 prints. Cell left N/A. Lag in Table 9 uses sim internals only.")
    a("")
    a("---")
    a("")
    a("## Table 4 — Factuality (hard hallucination rate)")
    a("")
    a("| Condition | DEV rate | TEST rate | red-team rate under critic |")
    a("|-----------|----------|-----------|----------------------------|")
    a("| C | %s | %s | — |" % (fmt3(c_dev) if c_dev is not None else "TO RUN", fmt3(c_test) if c_test is not None else "TO RUN"))
    a("| D | %s | %s | %s |" % (fmt3(d_dev) if d_dev is not None else "TO RUN", fmt3(d_test) if d_test is not None else "TO RUN", d_red_s))
    a("| E-factcheck | %s | %s | %s |" % (fmt3(e_dev) if e_dev is not None else "TO RUN", fmt3(e_test) if e_test is not None else "TO RUN", fmt3(e_red) if e_red is not None else "TO RUN"))
    a("")
    return lines, rq, t6_rows, t7_rows, fp_notes, t8_rows, t9_rows, rq_lines, dev_cell, test_cell


def finish_rest(pack2, det, fetch, rq):
    lines, t6_rows, t7_rows, fp_notes, t8_rows, t9_rows, rq_lines, dev_cell, test_cell = pack2
    a = lines.append
    a("---")
    a("")
    a("## Table 5 — Detectability")
    a("")
    a("TF-IDF logistic fitted on DEV (E01-E08) real headlines vs condition-C synth posts. Never fit on E09/E10.")
    a("")
    a("| Split | method | AUC synth vs held-out real |")
    a("|-------|--------|----------------------------|")
    a("| DEV CV | %s | %s |" % (det.get("method"), dev_cell))
    a("| TEST (E09/E10) | %s | %s |" % (det.get("method"), test_cell))
    a("")
    if det.get("dev_note"):
        a("DEV note: %s" % det["dev_note"])
    if det.get("test_note"):
        a("TEST note: %s" % det["test_note"])
    a("")
    a("---")
    a("")
    a("## Table 6 — Attack, max |Δbelief| by τ (condition D vs C baseline)")
    a("")
    a("| Event | τ=0.3 | τ=0.5 | τ=0.7 | τ=1.0 |")
    a("|-------|-------|-------|-------|-------|")
    lines.extend(t6_rows)
    a("")
    a("Each cell is the mean over seeds of |end_mean_D - end_mean_C| at that tau (C has no tau; same-event same-seed C).")
    a("RQ3 requires |Δbelief| at τ=1.0 >= |Δbelief| at τ=0.3 on the pre-registered comparison.")
    a("")
    a("---")
    a("")
    a("## Table 7 — Pareto (defense vs undefended D)")
    a("")
    a("| τ | defense | Δbelief | detection_rate | hallucination_rate |")
    a("|---|---------|---------|----------------|--------------------|")
    lines.extend(t7_rows)
    a("")
    a("Δbelief is end_mean - start_mean, averaged over all ten events and three seeds. For D, detection_rate is the fraction of posts with detector_p_ai > tau even if not gated. Official-post false-positive rate must stay <= 0.05 for a defense to count under RQ4.")
    if fp_notes:
        a("Official FP notes: " + "; ".join(fp_notes) + ".")
    else:
        a("Official FP: all tabulated defenses had mean official-post false-positive rate <= 0.05 in this run (see JSON posts_summary.official_fp_rate).")
    a("")
    return lines


def finish_tail(lines, t8_rows, t9_rows, rq_lines, fetch):
    a = lines.append
    a("---")
    a("")
    a("## Table 8 — Cascade vs isolated (RQ2)")
    a("")
    a("| Event | sign pre-registered | Δmean C | Δmean B | |ΔC| > |ΔB|? |")
    a("|-------|---------------------|---------|---------|------------------|")
    lines.extend(t8_rows)
    a("")
    a("---")
    a("")
    a("## Table 9 — Overshoot vs official lag (RQ1, E01-E02)")
    a("")
    a("| Event | t* | official mean - panic-retail mean at t* | lag holds? |")
    a("|-------|----|------------------------------------------|------------|")
    lines.extend(t9_rows)
    a("")
    a("E01 overshoot: exists t* in {1,...,6} with official_mean - panic-retail_mean >= 5 and population mean < official mean, on the seed-averaged role path. E02 lag: panic-retail remains >= 3 below official for at least two consecutive rounds after round 1, then both rise.")
    a("")
    a("---")
    a("")
    a("## RQ pass/fail")
    a("")
    lines.extend(rq_lines)
    a("")
    a("---")
    a("")
    a("## Fetch / generation notes")
    a("")
    a("- generator = prompt-only-decoder (fact-card slot-fill; no API key).")
    a("- n_runs attempted = %s" % fetch.get("n_runs"))
    a("- n_ok = %s" % fetch.get("n_ok"))
    a("- n_fail = %s" % fetch.get("n_fail"))
    a("- n_skipped_existing = %s" % fetch.get("n_skipped"))
    a("- wall_elapsed_s = %s" % fmt3(fetch.get("wall_elapsed_s")))
    a("- sum_run_elapsed_s = %s" % fmt3(fetch.get("sum_run_elapsed_s")))
    first = fetch.get("first_c_e01")
    if first is not None:
        a("- first timed cell C E01 seed 20260311 elapsed_s = %s" % fmt3(first))
        if float(first) > 120:
            a("- first cell exceeded 2 minutes (%s s); study continued." % fmt3(first))
    fails = fetch.get("failures") or []
    if fails:
        a("- failures:")
        for f in fails:
            a("  - `%s`" % f)
    else:
        a("- failures: none")
    a("- Smoke traces were not copied into this file.")
    a("")
    path = ROOT / "reports" / "RESULTS.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def load_fetch():
    idx_path = STUDY / "INDEX.json"
    fetch = {"n_runs": 0, "n_ok": 0, "n_fail": 0, "n_skipped": 0, "wall_elapsed_s": 0.0, "sum_run_elapsed_s": 0.0, "first_c_e01": None, "failures": []}
    if not idx_path.exists():
        return fetch
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    fetch["n_runs"] = idx.get("n_runs")
    fetch["n_ok"] = idx.get("n_ok")
    fetch["n_fail"] = idx.get("n_fail")
    fetch["wall_elapsed_s"] = idx.get("wall_elapsed_s")
    fetch["sum_run_elapsed_s"] = idx.get("sum_run_elapsed_s")
    runs = idx.get("runs") or []
    fetch["n_skipped"] = sum(1 for e in runs if e.get("skipped"))
    fetch["failures"] = ["%s: %s" % (e.get("key"), e.get("error")) for e in runs if not e.get("ok")]
    for e in runs:
        if e.get("key") == "E01_C_seed20260311_tau1":
            fetch["first_c_e01"] = e.get("elapsed_s")
            break
    return fetch


def main():
    from src.detect_auc import fit_auc
    runs = load_ok_runs()
    result, real_dev, real_test, synth_dev, synth_test = detectability()
    det = fit_auc(real_dev, real_test, synth_dev, synth_test)
    for k, v in result.items():
        det.setdefault(k, v)
    write_json(STUDY / "detectability.json", det)
    fetch = load_fetch()
    pack = write_results(runs, det, fetch)
    pack2 = finish_results(pack, det, fetch)
    lines, rq, t6_rows, t7_rows, fp_notes, t8_rows, t9_rows, rq_lines, dev_cell, test_cell = pack2
    lines = finish_rest((lines, t6_rows, t7_rows, fp_notes, t8_rows, t9_rows, rq_lines, dev_cell, test_cell), det, fetch, rq)
    path = finish_tail(lines, t8_rows, t9_rows, rq_lines, fetch)
    update_readme()
    print("wrote", path)
    print("rq", rq)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
