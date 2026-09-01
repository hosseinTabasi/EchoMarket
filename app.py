"""EchoMarket Streamlit playback. Author: Hossein Tabasi.

This demonstration is not investment advice. Peg-confidence is a rubric score, not a forecast.
No module places live posts.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.io_utils import DATA, read_csv, read_json, read_jsonl  # noqa: E402

DISCLAIMER = (
    "This demonstration is not investment advice. Peg-confidence is a rubric score, "
    "not a forecast, and not a recommendation to buy or sell USDT or USDC. "
    "No module places live posts."
)


def _load():
    events = read_csv(DATA / "events.csv")
    cards = {c["event_id"]: c for c in read_jsonl(DATA / "fact_cards.jsonl")}
    world = read_json(DATA / "world.json") if (DATA / "world.json").exists() else {}
    agents = read_jsonl(DATA / "agent.jsonl")
    posts = read_jsonl(DATA / "post.jsonl")
    edges = read_jsonl(DATA / "edge.jsonl")
    panel = read_jsonl(DATA / "panel_readout.jsonl")
    snaps = read_json(DATA / "snapshots.json") if (DATA / "snapshots.json").exists() else []
    return events, cards, world, agents, posts, edges, panel, snaps


def main() -> None:
    import pandas as pd
    import streamlit as st

    st.set_page_config(page_title="EchoMarket", layout="wide")
    st.title("EchoMarket")
    st.caption("Hossein Tabasi · M.Tech CSE · Shoolini University")
    st.warning(DISCLAIMER)

    events, cards, world, agents, posts, edges, panel, snaps = _load()
    if not world:
        st.info("No trace yet. Run `python src/run.py --smoke` first.")
        return

    st.sidebar.markdown("**Trace**")
    st.sidebar.write(
        {
            "event": world.get("event_id"),
            "condition": world.get("condition"),
            "n": world.get("n_agents"),
            "rounds": world.get("rounds"),
            "seed": world.get("seed"),
            "smoke": world.get("smoke"),
        }
    )
    page = st.sidebar.radio(
        "Page",
        ["Round playback", "Graph by confidence", "Post inspector", "Attack vs defense", "Fact card"],
    )
    rounds = sorted({int(p.get("round", 0)) for p in posts} | set(range(int(world.get("rounds") or 1))))
    rnd = st.sidebar.slider("Round", min_value=min(rounds) if rounds else 0, max_value=max(rounds) if rounds else 0, value=min(rounds) if rounds else 0)

    if page == "Round playback":
        st.subheader(f"Round {rnd}")
        rp = [p for p in posts if int(p.get("round", 0)) == rnd]
        st.write(f"{len(rp)} posts this round")
        if snaps and rnd < len(snaps):
            df = pd.DataFrame(snaps[rnd])
            st.line_chart(df.set_index("agent_id")["peg_confidence"])
            st.dataframe(df)
        if rp:
            st.dataframe(pd.DataFrame(rp)[["post_id", "author_id", "stance", "peg_sentiment", "virality", "is_redteam", "is_rebroadcast", "text"]])
        if panel:
            st.markdown("**Risk-officer panel (deterministic rubric)**")
            st.dataframe(pd.DataFrame([r for r in panel if int(r.get("round", -1)) == rnd] or panel[:10]))

    elif page == "Graph by confidence":
        st.subheader("Agents colored by peg-confidence")
        row = snaps[rnd] if snaps and rnd < len(snaps) else [
            {"agent_id": a["agent_id"], "role": a["role"], "community": a.get("community", -1), "peg_confidence": a.get("peg_confidence")}
            for a in agents
        ]
        df = pd.DataFrame(row)
        if "community" in df.columns:
            st.scatter_chart(df, x="community", y="peg_confidence", color="role")
        st.write(f"edges in trace: {len(edges)} (dst follows src)")
        if edges:
            st.dataframe(pd.DataFrame(edges).head(40))

    elif page == "Post inspector":
        st.subheader("Post inspector")
        if not posts:
            st.write("No posts.")
        else:
            ids = [p["post_id"] for p in posts]
            choice = st.selectbox("post_id", ids)
            rec = next(p for p in posts if p["post_id"] == choice)
            st.json(rec)
            st.markdown("**Text**")
            st.write(rec.get("text"))

    elif page == "Attack vs defense":
        st.subheader("Attack vs defense toggle (trace condition is fixed)")
        st.write("Reload a trace with `--condition D` or `--condition E-factcheck|E-ratelimit|E-detector`.")
        cond = st.selectbox("Suggested condition to re-run in the shell", ["A", "B", "C", "D", "E-factcheck", "E-ratelimit", "E-detector"])
        st.code(f"python src/run.py --smoke --condition {cond} --event {world.get('event_id', 'E01')}")
        red = [p for p in posts if p.get("is_redteam")]
        st.write({"redteam_posts": len(red), "condition": world.get("condition"), "tau": world.get("tau")})
        if red:
            st.dataframe(pd.DataFrame(red)[["post_id", "round", "peg_sentiment", "detector_p_ai", "text"]])

    elif page == "Fact card":
        eid = world.get("event_id") or events[0]["event_id"]
        ev = next(e for e in events if e["event_id"] == eid)
        card = cards[eid]
        st.subheader(f"{eid} · {ev['date']} · {ev['asset']} · {ev['event_type']}")
        st.write(ev["fact_summary"])
        st.markdown("**Official status**")
        st.write(card["official_status"])
        st.markdown("**72h peg path**")
        st.write(card["price_or_peg_path_72h"])
        st.markdown("**Verified facts**")
        for f in card["verified_facts"]:
            st.write("- " + f)
        st.markdown("**Forbidden inventions**")
        for f in card["forbidden_inventions"]:
            st.write("- " + f)


if __name__ == "__main__":
    main()
