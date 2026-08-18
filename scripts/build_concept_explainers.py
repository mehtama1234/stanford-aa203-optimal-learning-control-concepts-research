#!/usr/bin/env python3
"""Build the AA203 concept-explainers registry: the mechanism map.

The deep-track pages already teach each idea from first principles. This page is
the MAP over them, organized not by lecture order but by the HIDDEN QUANTITY each
concept really measures -- the invisible number that governs its behavior. That
is where the cross-concept patterns live (a shadow price, a cost-to-go, whether a
backward recursion has stopped changing).

Ported from cv-conference-analysis/scripts/build_paper_explainer_index.py and
re-themed to the AA203 light stylesheet (site/assets/styles.css).

Data source: analysis/concept_registry.json
  A list of buckets: {"bucket": str, "gloss": str, "concepts": [ {id, name,
  object_changed, hidden_quantity, math_object, mechanism}, ... ] }
Bucket order in the file is the display order.

Usage:  python3 scripts/build_concept_explainers.py
"""
import json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "analysis" / "concept_registry.json"
OUT = ROOT / "site" / "concept-explainers.html"
DEEP = ROOT / "site" / "concepts"   # to verify each <id>-deep.html exists


def e(s):
    return html.escape(str(s), quote=True)


# The reading contract: what every row gives you (the paper-registry 7-part shape,
# compressed to the four columns a one-line registry row can carry + the page it opens).
LEGEND = [
    ("Object it changes", "the concrete thing the idea operates on -- a control law, a value function, a trajectory, a constraint set"),
    ("Hidden quantity", "the invisible number it really tracks -- a cost-to-go, a shadow price, whether a recursion has settled"),
    ("Math object", "the one compact equation the idea reduces to -- the only place raw symbols appear"),
    ("Why it works", "the actual mechanism in plain words -- not “improves performance,” the causal reason"),
]

CSS = """
.reg-hero .kick{color:var(--accent-2)}
.legend4{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin:18px 0 6px}
.legend4 .cell{border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;background:var(--paper);padding:12px 14px}
.legend4 .cell b{display:block;font-size:13.5px;color:var(--accent);margin-bottom:3px;letter-spacing:.01em}
.legend4 .cell span{font-size:13px;color:var(--muted)}
.bucket{margin:30px 0 6px}
.bucket .bh{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:6px}
.bucket h2{margin:0;font-size:22px}
.bucket .q{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;color:var(--accent-2);font-weight:760;text-transform:uppercase;letter-spacing:.06em}
.bucket .gloss{color:var(--muted);font-size:14px;flex-basis:100%;margin:2px 0 0}
.reg-rows{display:grid;gap:11px;margin-top:14px}
.reg-row{border:1px solid var(--line);border-radius:10px;background:var(--paper);padding:15px 17px;display:grid;grid-template-columns:1.05fr 2fr auto;gap:18px;align-items:start}
.reg-row .rtitle{font-size:16.5px;font-weight:760;line-height:1.28;margin:0 0 8px}
.reg-row .rtitle a{text-decoration:none;color:var(--ink)}
.reg-row .rtitle a:hover{color:var(--accent);text-decoration:underline}
.reg-row .obj{font-size:13.5px;color:#2c3a40}
.reg-row .obj .k{display:block;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin-bottom:1px}
.tri{display:grid;gap:8px;font-size:13.5px}
.tri .k{display:block;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin-bottom:1px}
.tri .v{color:#24323a}
.tri .mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;color:var(--accent);background:var(--soft);border:1px solid #cfe4e0;border-radius:5px;padding:3px 7px;display:inline-block;line-height:1.5}
.tri .mech{color:#2c3a40;border-left:2px solid var(--soft);padding-left:10px}
.act{display:flex;flex-direction:column;align-items:flex-end;gap:9px;white-space:nowrap}
.badge{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;padding:4px 9px;border-radius:999px;font-weight:760;background:var(--accent);color:#fff}
.badge.q{background:var(--paper);color:var(--accent-2);border:1px solid #e2cbb6}
.open{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;text-decoration:none;color:var(--accent);border:1px solid var(--line);border-radius:7px;padding:6px 11px;background:var(--paper)}
.open:hover{background:var(--soft)}
@media(max-width:820px){.reg-row{grid-template-columns:1fr}.act{flex-direction:row;align-items:center}}
"""


def legend_html():
    cells = "".join(
        f'<div class="cell"><b>{e(t)}</b><span>{e(d)}</span></div>' for t, d in LEGEND
    )
    return f'<div class="legend4">{cells}</div>'


def row_html(c):
    cid = c["id"]
    page = f"concepts/{cid}-deep.html"
    complete = (DEEP / f"{cid}-deep.html").exists()
    title = e(c["name"])
    title_html = f'<a href="{e(page)}">{title}</a>' if complete else title
    badge = '<span class="badge">deep dive</span>' if complete else '<span class="badge q">queued</span>'
    action = (f'<a class="open" href="{e(page)}">open &rarr;</a>' if complete
              else '<span class="muted" style="font-size:12px">page pending</span>')
    return f"""<div class="reg-row">
<div class="head"><p class="rtitle">{title_html}</p>
<div class="obj"><span class="k">Object it changes</span>{e(c["object_changed"])}</div></div>
<div class="tri">
<div><span class="k">Hidden quantity measured</span><span class="v">{e(c["hidden_quantity"])}</span></div>
<div><span class="k">Math object</span><span class="mono">{e(c["math_object"])}</span></div>
<div class="mech"><span class="k">Why it works</span>{e(c["mechanism"])}</div>
</div>
<div class="act">{badge}{action}</div>
</div>"""


def bucket_html(b):
    rows = "".join(row_html(c) for c in b["concepts"])
    gloss = f'<p class="gloss">{e(b["gloss"])}</p>' if b.get("gloss") else ""
    return (f'<div class="bucket"><div class="bh"><h2>{e(b["bucket"])}</h2>'
            f'<span class="q">the hidden quantity</span>{gloss}</div>'
            f'<div class="reg-rows">{rows}</div></div>')


def page(buckets):
    total = sum(len(b["concepts"]) for b in buckets)
    fams = len(buckets)
    built = sum(1 for b in buckets for c in b["concepts"]
                if (DEEP / f'{c["id"]}-deep.html').exists())
    sections = "\n".join(bucket_html(b) for b in buckets)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Mechanism Map · Stanford AA203 Control Lab</title>
<link rel="stylesheet" href="assets/styles.css">
<style>{CSS}</style></head><body>
<header class="topbar"><a class="brand" href="index.html">Stanford AA203 Control Lab</a>
<nav><a href="index.html">Overview</a><a href="concepts.html">Concepts</a><a href="deep-track.html">Deep track</a><a class="active" href="concept-explainers.html">Mechanism map</a><a href="course-spine.html">Spine</a></nav></header>
<main>
<div class="hero reg-hero"><div class="kick">the mechanism map · every concept by the hidden quantity it measures</div>
<h1>The Mechanism Map</h1>
<p class="lede">The deep track teaches each idea from first principles. This is the map over all {total} of them &mdash; sorted not by lecture order but by the <b>hidden quantity each concept really measures</b>: the invisible number that governs how it behaves. That is where the cross-concept patterns live.</p>
<div class="stats"><div class="stat"><strong>{total}</strong>concepts</div><div class="stat"><strong>{fams}</strong>hidden quantities</div><div class="stat"><strong>{built}</strong>deep dives linked</div></div>
</div>
<p class="lede" style="font-size:16px;margin-top:22px">Every row names four things, then opens the full deep dive. The goal is not to summarize a concept &mdash; it is to surface the object it changes, the hidden quantity it tracks, the one equation it reduces to, and the mechanism that makes it work.</p>
{legend_html()}
{sections}
<p class="muted" style="font-size:12px;margin-top:40px;border-top:1px solid var(--line);padding-top:18px">Mechanism map · generated by scripts/build_concept_explainers.py · data in analysis/concept_registry.json · add a concept by appending to its bucket.</p>
</main></body></html>"""


def main():
    buckets = json.loads(DATA.read_text())
    OUT.write_text(page(buckets), encoding="utf-8")
    total = sum(len(b["concepts"]) for b in buckets)
    print(f"wrote {OUT.relative_to(ROOT)} | {total} concepts, {len(buckets)} hidden-quantity buckets")


if __name__ == "__main__":
    main()
