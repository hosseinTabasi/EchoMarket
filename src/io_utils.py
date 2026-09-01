"""JSONL / CSV / YAML helpers. Author: Hossein Tabasi."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROMPTS = ROOT / "prompts"
REPORTS = ROOT / "reports"
CONFIG = ROOT / "config"


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_prompt(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")


def _parse_scalar(raw: str) -> Any:
    s = raw.strip()
    if s in {"true", "True"}:
        return True
    if s in {"false", "False"}:
        return False
    if s in {"null", "None", "~"}:
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(x.strip()) for x in inner.split(",")]
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def _load_yaml_subset(text: str) -> Dict[str, Any]:
    """Minimal indent YAML (mappings, nested maps, inline lists). Fallback if PyYAML missing."""
    lines = []
    for raw in text.splitlines():
        if "#" in raw:
            # keep quoted hashes out; our files only use full-line or trailing comments
            in_q = False
            out = []
            for ch in raw:
                if ch in "\"'" and not in_q:
                    in_q = True
                    out.append(ch)
                elif ch in "\'" and in_q:
                    in_q = False
                    out.append(ch)
                elif ch == "#" and not in_q:
                    break
                else:
                    out.append(ch)
            raw = "".join(out)
        if raw.strip():
            lines.append(raw.rstrip())

    def indent_of(s: str) -> int:
        return len(s) - len(s.lstrip(" "))

    def parse_block(idx: int, min_indent: int):
        node: Dict[str, Any] = {}
        n = len(lines)
        while idx < n:
            line = lines[idx]
            ind = indent_of(line)
            if ind < min_indent:
                break
            if ind > min_indent and min_indent >= 0 and node:
                break
            stripped = line.strip()
            if stripped.startswith("- "):
                raise ValueError("block lists not used in default.yaml")
            if ":" not in stripped:
                idx += 1
                continue
            key, rest = stripped.split(":", 1)
            key = key.strip()
            rest = rest.strip()
            nxt = idx + 1
            if rest:
                node[key] = _parse_scalar(rest)
                idx = nxt
            else:
                # nested mapping
                child, idx2 = parse_block(nxt, ind + 2)
                node[key] = child
                idx = idx2
        return node, idx

    root, _ = parse_block(0, 0)
    return root


def load_yaml(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except Exception:
        return _load_yaml_subset(text)


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


_ABBREV_PROTECT = [
    ("S.A. de C.V.", "§SADECV§"),
    ("S.A. de C.V", "§SADECV§"),
    ("S.A.", "§SAABBR§"),
    ("C.V.", "§CVABBR§"),
    ("U.S.", "§USABBR§"),
    ("U.K.", "§UKABBR§"),
    ("D.C.", "§DCABBR§"),
    ("Mr.", "§MRABBR§"),
    ("Mrs.", "§MRSABBR§"),
    ("Ms.", "§MSABBR§"),
    ("Dr.", "§DRABBR§"),
    ("Inc.", "§INCABBR§"),
    ("Ltd.", "§LTDABBR§"),
    ("No.", "§NOABBR§"),
    ("Jan.", "§JANABBR§"),
    ("Feb.", "§FEBABBR§"),
    ("Mar.", "§MARABBR§"),
    ("Apr.", "§APRABBR§"),
    ("Jun.", "§JUNABBR§"),
    ("Jul.", "§JULABBR§"),
    ("Aug.", "§AUGABBR§"),
    ("Sep.", "§SEPABBR§"),
    ("Sept.", "§SEPTABBR§"),
    ("Oct.", "§OCTABBR§"),
    ("Nov.", "§NOVABBR§"),
    ("Dec.", "§DECABBR§"),
]


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    work = text.strip()
    for a, b in _ABBREV_PROTECT:
        work = work.replace(a, b)
    chunks = re.split(r"(?<=[.!?])\s+", work)
    parts = []
    for ch in chunks:
        s = ch.strip()
        if not s:
            continue
        for a, b in _ABBREV_PROTECT:
            s = s.replace(b, a)
        parts.append(s)
    return parts
