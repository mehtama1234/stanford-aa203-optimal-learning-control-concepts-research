#!/usr/bin/env python3
"""Builder for CVPR-depth 'deep' concept pages.

Each page is a JSON spec in analysis/deep/<id>.json. This renders it to
site/concepts/<id>-deep.html using one shared template + stylesheet, so every
deep page has the same visual quality as the hand-built lqr-deep reference.

Spec schema (all fields plain text unless noted; HTML allowed in 'para'/'insight'):
{
  "id": "lqr",
  "name": "LQR",
  "title": "LQR — when the future cost is a bowl, the best move is a straight line",
  "lede": "one-paragraph promise of the whole page",
  "arc": [["problem","The problem"], ["run","Seen on a real run"], ...],
  "sections": [
    {"id":"problem","h2":"1 · The problem — ...","blocks":[
       {"t":"para","html":"..."},
       {"t":"eq","text":"u* = -K x"},
       {"t":"insight","html":"<strong>The discovered fact:</strong> ..."},
       {"t":"table","headers":[...],"rows":[[...],[...]]},
       {"t":"bars","caption":"...","rows":[["1 step",0.0,"K=0.000",false],...]},
    ]}
  ],
  "recipe": {"summary":"...","eq":"...","note":"..."},
  "related": [["lqr.html","LQR atlas"], ...]
}
"""
import html, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "analysis" / "deep"
OUT = ROOT / "site" / "concepts"

HEAD = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title_tab} · Stanford AA203 Control Lab</title>
  <link rel="stylesheet" href="../assets/styles.css">
  <style>
    .arc{{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0}}
    .arc a{{font-size:12.5px;color:var(--accent);text-decoration:none;border:1px solid var(--line);border-radius:20px;padding:3px 10px;background:var(--paper)}}
    .arc a:hover{{border-color:var(--accent)}}
    .barrow{{display:flex;align-items:center;gap:10px;margin:5px 0;font-size:13px}}
    .barrow .lab{{width:130px;font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--muted);text-align:right}}
    .bar{{height:16px;border-radius:3px;background:var(--accent);min-width:2px}}
    .bar.alt{{background:var(--accent-2)}}
    .barrow .val{{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--ink)}}
    .eq{{font-family:ui-monospace,Menlo,monospace;font-size:13.5px;background:#eef5f4;border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:12px 0;overflow-x:auto;white-space:pre-wrap}}
    .insight{{border-left:3px solid var(--accent-2);background:#fbf3ee;padding:12px 16px;border-radius:0 8px 8px 0;margin:16px 0;font-size:15.5px}}
    figure{{margin:16px 0}}figcaption{{font-size:13px;color:var(--muted);margin-top:6px}}
    .tw{{overflow-x:auto}}
  </style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="../index.html">Stanford AA203 Control Lab</a>
    <nav>
      <a href="../index.html">Overview</a>
      <a href="../concepts.html">Concepts</a>
      <a href="{id}.html">Atlas card</a>
      <a href="../course-spine.html">Spine</a>
      <a href="../derivations.html">Derivations</a>
    </nav>
  </header>
  <main>
    <div class="hero">
      <div class="kick">{kick}</div>
      <h1>{h1}</h1>
      <p class="lede">{lede}</p>
      <div class="arc">{arc}</div>
    </div>
"""

FOOT = """    <footer>Stanford AA203 · {name} deep dive · every quantity measured, not asserted.</footer>
  </main>
</body>
</html>
"""


def esc(s: str) -> str:
    return html.escape(str(s), quote=False)


def render_block(b: dict) -> str:
    t = b["t"]
    if t == "para":
        return f'      <p>{b["html"]}</p>'
    if t == "eq":
        return f'      <div class="eq">{esc(b["text"])}</div>'
    if t == "insight":
        return f'      <div class="insight">{b["html"]}</div>'
    if t == "table":
        head = "".join(f"<th>{esc(h)}</th>" for h in b["headers"])
        rows = ""
        for r in b["rows"]:
            rows += "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>"
        cap = f'<figcaption>{esc(b["caption"])}</figcaption>' if b.get("caption") else ""
        return f'      <div class="tw"><table><tr>{head}</tr>{rows}</table></div>{cap}'
    if t == "bars":
        rows = ""
        for row in b["rows"]:
            lab, val = row[0], row[2]
            try:
                frac = float(row[1])
            except (TypeError, ValueError):
                frac = 0.0            # informational row, no bar
            alt = " alt" if (len(row) > 3 and row[3]) else ""
            w = max(2, round(frac * 150))
            rows += (f'<div class="barrow"><span class="lab">{esc(lab)}</span>'
                     f'<div class="bar{alt}" style="width:{w}px"></div>'
                     f'<span class="val">{esc(val)}</span></div>')
        cap = f'<figcaption>{esc(b["caption"])}</figcaption>' if b.get("caption") else ""
        return f'      <figure>{rows}{cap}</figure>'
    raise ValueError(f"unknown block type {t}")


def render(spec: dict) -> str:
    arc = "".join(f'<a href="#{aid}">{esc(lbl)}</a>' for aid, lbl in spec.get("arc", []))
    arc += f'<a href="{spec["id"]}.html">Atlas card</a>'
    out = [HEAD.format(
        title_tab=esc(spec["name"]) + " (deep)",
        id=esc(spec["id"]),
        kick=esc(spec.get("kick", spec["name"] + " · first principles")),
        h1=esc(spec["title"]),
        lede=spec["lede"],
        arc=arc,
        name=esc(spec["name"]),
    )]
    for s in spec["sections"]:
        out.append(f'    <section class="fp" id="{esc(s["id"])}">')
        out.append(f'      <h2>{esc(s["h2"])}</h2>')
        out.append('      <div class="essay">')
        for b in s["blocks"]:
            out.append(render_block(b))
        out.append("      </div>")
        out.append("    </section>")
    if spec.get("related"):
        rel = " · ".join(f'<a href="{esc(h)}">{esc(l)}</a>' for h, l in spec["related"])
        out.append(f'    <section class="fp"><p class="muted">Related: {rel}</p></section>')
    if spec.get("recipe"):
        rc = spec["recipe"]
        out.append('    <details class="math"><summary>the run recipe — reproduce every number above</summary><div>')
        out.append(f'      <p class="muted">{esc(rc.get("summary",""))}</p>')
        if rc.get("eq"):
            out.append(f'      <div class="eq">{esc(rc["eq"])}</div>')
        if rc.get("note"):
            out.append(f'      <p class="muted">{esc(rc["note"])}</p>')
        out.append("    </div></details>")
    out.append(FOOT.format(name=esc(spec["name"])))
    return "\n".join(out)


def main():
    ids = sys.argv[1:] or [p.stem for p in SPECS.glob("*.json") if not p.stem.startswith("_")]
    n = 0
    for cid in ids:
        spec = json.loads((SPECS / f"{cid}.json").read_text())
        (OUT / f"{cid}-deep.html").write_text(render(spec))
        n += 1
    print(f"built {n} deep pages -> {OUT}")


if __name__ == "__main__":
    main()
