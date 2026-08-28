"""
Build docs/deck.html from docs/deck.template.html.

Every number on the deck is parsed out of a real captured run of
poc_bypass.py, so the slides cannot drift from what the code prints.

    make deck
"""

import base64
import html
import pathlib
import re
import sys

DOCS = pathlib.Path(__file__).parent
CAP = DOCS / "captures"
THRESHOLD = 0.85

# Rows of section [3]:  class  sim  inj  verdict  prompt
ROW = re.compile(
    r"^\s+(surface|rewrite)\s+(-?\d+\.\d+)\s+(\d+\.\d+)\s+(HIT|miss)\s+(.*)$"
)


def b64(path: pathlib.Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def parse_variants(text: str):
    rows = []
    for line in text.splitlines():
        m = ROW.match(line.rstrip())
        if m:
            kind, sim, inj, verdict, prompt = m.groups()
            rows.append((kind, float(sim), float(inj), verdict, prompt.strip()))
    return rows


def meters(rows) -> str:
    out = []
    for kind, sim, inj, verdict, prompt in rows:
        hit = verdict == "HIT"
        width = max(0.0, min(1.0, sim)) * 100
        cls = "hit" if hit else "miss"
        # Escape first, then append the entity - escaping it would show it raw.
        label = html.escape(prompt) if len(prompt) <= 62 else html.escape(prompt[:60]) + "&hellip;"
        out.append(
            f'<div class="meter-row">'
            f'<span class="m-class">{kind}</span>'
            f'<span class="m-track">'
            f'<span class="m-fill {cls}" style="width:{width:.1f}%"></span>'
            f'<span class="m-thresh" style="left:{THRESHOLD * 100:.0f}%"></span>'
            f'<span class="m-label">{label}</span>'
            f"</span>"
            f'<span class="m-sim">{sim:.3f}</span>'
            f'<span class="m-inj">{inj:.3f}</span>'
            f'<span class="m-verdict {"red" if hit else "dim"}">{verdict.upper()}</span>'
            f"</div>"
        )
    return "\n".join(out)


def terminal(text: str) -> str:
    """Escape the captured run and colour the lines that carry the argument.

    Trimmed to fit one slide without scrolling: the loader chatter goes, and
    so does the closing prose, which slides 8 and 10 already say better.
    """
    keep = []
    skipping = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("loading "):
            continue
        # Section [5] is the sweep, which slide 9 renders as a table.
        if stripped.startswith("[5]"):
            skipping = True
            continue
        if skipping:
            if stripped.startswith("="):
                skipping = False
            else:
                continue
        # Section [4] re-lists the same five prompts [3] already showed.
        if stripped.startswith("sim=") and "served poisoned response" in stripped:
            continue
        # Everything from here on is restated on later slides.
        if stripped.startswith("The variants that get through"):
            keep.append("=" * 78)
            break
        if not stripped and keep and not keep[-1]:
            continue
        keep.append(line.rstrip())
    body = "\n".join(keep).strip("\n")

    esc = html.escape(body)
    # Highlight, most specific first so earlier spans are not re-matched.
    esc = re.sub(r"(BLOCKED)", r'<span class="r">\1</span>', esc)
    esc = re.sub(r"(\bHIT\b)", r'<span class="r">\1</span>', esc)
    esc = re.sub(r"(score=1\.000|1\.000)", r'<span class="g">\1</span>', esc)
    esc = re.sub(r"(filter invocations[^\n]*: 0)", r'<span class="r">\1</span>', esc)
    esc = re.sub(r"^(\[\d\][^\n]*)$", r'<span class="c">\1</span>', esc, flags=re.M)
    esc = re.sub(r"^(=+)$", r'<span class="d">\1</span>', esc, flags=re.M)
    return esc


def main() -> int:
    tpl_path = DOCS / "deck.template.html"
    cap_path = CAP / "demo-output.txt"
    for p in (tpl_path, cap_path, CAP / "problem-dark.png",
              CAP / "architecture-dark.png", CAP / "flow-dark.png"):
        if not p.exists():
            print(f"missing: {p}", file=sys.stderr)
            return 1

    captured = cap_path.read_text(encoding="utf-8")
    rows = parse_variants(captured)
    if len(rows) != 10:
        print(f"expected 10 variant rows, parsed {len(rows)}", file=sys.stderr)
        return 1

    hits = sum(1 for r in rows if r[3] == "HIT")
    caught = sum(1 for r in rows if r[2] > 0.5)
    print(f"  parsed {len(rows)} variants: {hits} cache hits, {caught} flagged by filter")

    out = tpl_path.read_text(encoding="utf-8")
    out = out.replace("{{METERS}}", meters(rows))
    out = out.replace("{{TERM_HTML}}", terminal(captured))
    out = out.replace("{{PROBLEM_PNG}}", b64(CAP / "problem-dark.png"))
    out = out.replace("{{ARCH_PNG}}", b64(CAP / "architecture-dark.png"))
    out = out.replace("{{FLOW_PNG}}", b64(CAP / "flow-dark.png"))

    for token in ("{{METERS}}", "{{TERM_HTML}}", "{{PROBLEM_PNG}}",
                  "{{ARCH_PNG}}", "{{FLOW_PNG}}"):
        if token in out:
            print(f"unsubstituted token: {token}", file=sys.stderr)
            return 1

    dest = DOCS / "deck.html"
    dest.write_text(out, encoding="utf-8")
    print(f"  wrote {dest}  ({dest.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
