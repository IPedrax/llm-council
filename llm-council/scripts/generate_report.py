#!/usr/bin/env python3
"""
generate_report.py - Render an LLM Council session into a standalone HTML report.

Usage:
    python generate_report.py <session.json> [output.html]

If output.html is omitted, the report is written next to the JSON as
council-report-<date>-<slug>.html and the final path is printed to stdout.

The report is a single self-contained HTML file (inline CSS + inline SVG icons,
no external assets) that looks good on screen AND prints/exports to PDF cleanly:
backgrounds are forced on for print, sections avoid awkward page breaks, and
nothing is hidden behind collapsible widgets. No third-party dependencies.

------------------------------------------------------------------------------
SESSION JSON SCHEMA
------------------------------------------------------------------------------
{
  "topic":    "Short title for the decision",          # required
  "question": "The full framed question advisors got", # required
  "date":     "2026-06-15",        # optional; defaults to today (local date)
  "mode":     "Full Council",      # optional label, e.g. "Full Council" / "Solo Council"
  "models":   "Opus / Sonnet / Haiku",  # optional; only meaningful in model-mixing runs

  "advisors": [                    # required, 1+ entries
    {
      "name":     "The Contrarian",
      "model":    "claude-opus-4-8",   # optional; shown under the name if present
      "response": "Markdown text of the advisor's full response."
    }
  ],

  "peer_reviews": [                # optional
    {
      "reviewer": "The Contrarian",    # who wrote the review
      "text":     "Markdown text of their review (the 3 answers)."
    }
  ],

  "verdict": {                     # required
    "agrees":         "Markdown - where the council agreed.",
    "clashes":        "Markdown - genuine disagreements.",
    "blind_spots":    "Markdown - what peer review surfaced.",
    "recommendation": "Markdown - the single clear recommendation.",
    "first_step":     "Markdown - the one concrete next step."
  }
}
------------------------------------------------------------------------------
"""

import sys
import json
import re
import html
import datetime
from pathlib import Path

# Palette used to color-code advisors (cycled by index).
PALETTE = [
    "#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444",
    "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#84cc16",
]

# Inline SVG icons (stroke = currentColor so they inherit text color).
ICON_PATHS = {
    "scales": '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>'
              '<path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>'
              '<path d="M7 21h10"/><path d="M12 3v18"/>'
              '<path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    "check":  '<circle cx="12" cy="12" r="9"/><path d="m8.5 12.5 2.5 2.5 4.5-5"/>',
    "clash":  '<path d="M9 6 3 12l6 6"/><path d="M15 6l6 6-6 6"/>',
    "eye":    '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>'
              '<circle cx="12" cy="12" r="3"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/>'
              '<circle cx="12" cy="12" r="1.6"/>',
    "arrow":  '<circle cx="12" cy="12" r="9"/><path d="M11 8l4 4-4 4"/><path d="M8 12h7"/>',
    "users":  '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
              '<circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
              '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "review": '<path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "quote":  '<circle cx="12" cy="12" r="9"/>'
              '<path d="M9.2 9.4a3 3 0 0 1 5.6 1.1c0 2-3 2.5-3 2.5"/><path d="M12 17h.01"/>',
}


def ico(name):
    return (f'<span class="ico"><svg viewBox="0 0 24 24" aria-hidden="true">'
            f'{ICON_PATHS[name]}</svg></span>')


def initials(name):
    stop = {"o", "a", "os", "as", "the", "de", "da", "do", "e", "of"}
    words = re.findall(r"[A-Za-zÀ-ÿ]+", name or "")
    picks = [w for w in words if w.lower() not in stop] or words
    return "".join(w[0] for w in picks[:2]).upper() or "?"


def slugify(text, maxlen=40):
    text = re.sub(r"[^\w\s-]", "", (text or "").lower()).strip()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:maxlen].strip("-") or "council"


def esc(text):
    return html.escape(text or "", quote=False)


def _inline(text):
    """Apply inline Markdown to an already HTML-escaped string."""
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def md_to_html(text):
    """Minimal, safe block-level Markdown -> HTML (paragraphs + bullet/numbered lists)."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    out = []
    list_type = None
    para = []

    def close_list():
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    def flush_para():
        if para:
            out.append("<p>" + "<br>".join(_inline(esc(l)) for l in para) + "</p>")
            para.clear()

    for line in lines:
        stripped = line.strip()
        ul = re.match(r"^[-*•]\s+(.*)$", stripped)
        ol = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if ul:
            flush_para()
            if list_type != "ul":
                close_list(); out.append("<ul>"); list_type = "ul"
            out.append(f"<li>{_inline(esc(ul.group(1)))}</li>")
        elif ol:
            flush_para()
            if list_type != "ol":
                close_list(); out.append("<ol>"); list_type = "ol"
            out.append(f"<li>{_inline(esc(ol.group(1)))}</li>")
        elif not stripped:
            flush_para(); close_list()
        else:
            close_list(); para.append(stripped)

    flush_para(); close_list()
    return "\n".join(out)


CSS = """
*{box-sizing:border-box}
:root{
  --bg:#f4f5fa; --paper:#fff; --ink:#1f2430; --soft:#3c4453; --muted:#6b7280;
  --line:#e6e8f0; --line2:#eef0f6;
  --accent:#4f46e5; --accent-ink:#3730a3; --accent-bg:#eef0ff;
  --green:#0f9d6b; --green-bg:#e7f6ef; --amber:#b7791f; --amber-bg:#fbf1de;
  --purple:#7c3aed; --purple-bg:#f1ebfe;
}
html,body{margin:0}
body{background:var(--bg);color:var(--ink);
  font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.page{max-width:840px;margin:28px auto;background:var(--paper);
  border:1px solid var(--line);border-radius:18px;box-shadow:0 6px 30px rgba(31,36,48,.07)}
.inner{padding:40px 44px 34px}
.ico{display:inline-flex}
.ico svg{width:1em;height:1em;stroke:currentColor;fill:none;
  stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
a{color:var(--accent)}

.head{display:flex;gap:16px;align-items:flex-start;border-bottom:1px solid var(--line);
  padding-bottom:22px;margin-bottom:24px}
.crest{flex:0 0 auto;width:48px;height:48px;border-radius:13px;background:var(--accent);
  color:#fff;display:flex;align-items:center;justify-content:center;font-size:26px}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:700}
h1{font-size:27px;line-height:1.18;margin:5px 0 11px;letter-spacing:-.01em}
.meta{display:flex;flex-wrap:wrap;gap:7px}
.chip{font-size:12px;color:var(--soft);background:var(--bg);border:1px solid var(--line);
  border-radius:999px;padding:3px 11px}
.chip b{color:var(--ink);font-weight:600}

.question{background:var(--accent-bg);border-radius:14px;padding:15px 18px;margin:0 0 28px}
.qlabel{display:flex;align-items:center;gap:7px;font-size:11px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--accent);font-weight:700;margin-bottom:7px}
.qlabel .ico{font-size:15px}
.question .body{color:var(--accent-ink)}

.sec{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
  font-weight:700;display:flex;align-items:center;gap:8px;margin:32px 0 15px}
.sec .ico{font-size:16px;color:var(--accent)}

.verdict{border:1px solid var(--line);border-radius:16px}
.vrow{display:flex;gap:14px;padding:17px 20px;border-top:1px solid var(--line2)}
.vrow:first-child{border-top:none}
.vbadge{flex:0 0 auto;width:34px;height:34px;border-radius:50%;display:flex;
  align-items:center;justify-content:center;font-size:18px}
.vrow h3{margin:3px 0 5px;font-size:16px}
.vrow .body{color:var(--soft)}
.vrow.key{background:var(--accent-bg)}
.vrow.key:first-child{border-radius:16px 16px 0 0}
.vrow.key:last-child{border-radius:0 0 16px 16px}
.vrow.key h3{color:var(--accent-ink)}
.c-green .vbadge{background:var(--green-bg);color:var(--green)}
.c-amber .vbadge{background:var(--amber-bg);color:var(--amber)}
.c-purple .vbadge{background:var(--purple-bg);color:var(--purple)}
.c-accent .vbadge{background:var(--accent);color:#fff}

.cards{display:grid;gap:14px;grid-template-columns:1fr 1fr}
.card{border:1px solid var(--line);border-radius:14px;padding:16px 18px;background:var(--paper)}
.card .who{display:flex;align-items:center;gap:10px;margin-bottom:9px}
.avatar{flex:0 0 auto;width:30px;height:30px;border-radius:9px;display:flex;align-items:center;
  justify-content:center;font-size:12px;font-weight:700;color:#fff;background:var(--c,#6366f1)}
.card .name{font-weight:700;font-size:14.5px;line-height:1.15}
.card .model{font-size:10.5px;color:var(--muted);margin-top:1px}
.card .body{color:var(--soft);font-size:14.5px}

.reviews{border:1px solid var(--line);border-radius:14px;background:var(--bg)}
.review{padding:13px 18px;border-top:1px solid var(--line)}
.review:first-child{border-top:none}
.review .rname{font-weight:700;font-size:13px;color:var(--soft);margin-bottom:4px}
.review .body{font-size:13.5px;color:var(--muted)}

.body p{margin:.5em 0}.body p:first-child{margin-top:0}.body p:last-child{margin-bottom:0}
.body strong{color:var(--ink)}
.body ul,.body ol{margin:.45em 0;padding-left:1.25em}.body li{margin:.22em 0}
code{background:var(--line2);padding:1px 6px;border-radius:6px;font-size:.88em;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}

footer{margin-top:30px;padding-top:15px;border-top:1px solid var(--line);
  color:var(--muted);font-size:11.5px;display:flex;align-items:center;gap:7px}
footer .ico{font-size:14px}

@media(max-width:680px){.cards{grid-template-columns:1fr}.inner{padding:26px 20px}}

@media print{
  @page{margin:14mm}
  html,body{background:#fff}
  body{font-size:11pt;line-height:1.5}
  *{-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important}
  .page{max-width:none;margin:0;border:none;border-radius:0;box-shadow:none}
  .inner{padding:0}
  .vrow,.card,.review,.question,.head{break-inside:avoid}
  .sec,h1,h3{break-after:avoid}
}
"""


def render(session):
    topic = session.get("topic", "Council Verdict")
    question = session.get("question", "")
    date = session.get("date") or datetime.date.today().isoformat()
    mode = session.get("mode", "")
    models = session.get("models", "")
    advisors = session.get("advisors", []) or []
    reviews = session.get("peer_reviews", []) or []
    verdict = session.get("verdict", {}) or {}

    chips = [f'<span class="chip"><b>{len(advisors)}</b> advisors</span>']
    if mode:
        chips.append(f'<span class="chip">{esc(mode)}</span>')
    if models:
        chips.append(f'<span class="chip">{esc(models)}</span>')
    chips.append(f'<span class="chip">{esc(date)}</span>')

    question_html = ""
    if question:
        question_html = (
            f'<div class="question"><div class="qlabel">{ico("quote")} '
            f'The question put to the council</div>'
            f'<div class="body">{md_to_html(question)}</div></div>'
        )

    vdefs = [
        ("Where the council agrees", "agrees", "check", "c-green", False),
        ("Where the council clashes", "clashes", "clash", "c-amber", False),
        ("Blind spots the council caught", "blind_spots", "eye", "c-purple", False),
        ("The recommendation", "recommendation", "target", "c-accent", True),
        ("The one thing to do first", "first_step", "arrow", "c-accent", True),
    ]
    vrows = []
    for title, key, icon_name, color, keyrow in vdefs:
        body = verdict.get(key) or verdict.get(key.replace("_", "")) or ""
        if not body:
            continue
        cls = f"vrow {color}" + (" key" if keyrow else "")
        vrows.append(
            f'<div class="{cls}"><div class="vbadge">{ico(icon_name)}</div>'
            f'<div><h3>{esc(title)}</h3><div class="body">{md_to_html(body)}</div></div></div>'
        )
    verdict_html = f'<div class="verdict">{"".join(vrows)}</div>' if vrows else ""

    cards = []
    for i, a in enumerate(advisors):
        color = PALETTE[i % len(PALETTE)]
        name = a.get("name", "Advisor")
        model = (f'<div class="model">{esc(a.get("model"))}</div>'
                 if a.get("model") else "")
        cards.append(
            f'<div class="card" style="--c:{color}"><div class="who">'
            f'<div class="avatar">{esc(initials(name))}</div>'
            f'<div><div class="name">{esc(name)}</div>{model}</div></div>'
            f'<div class="body">{md_to_html(a.get("response",""))}</div></div>'
        )
    council_html = ""
    if cards:
        council_html = (f'<div class="sec">{ico("users")} The Council</div>'
                        f'<div class="cards">{"".join(cards)}</div>')

    review_items = []
    for r in reviews:
        review_items.append(
            f'<div class="review"><div class="rname">{esc(r.get("reviewer","Reviewer"))}</div>'
            f'<div class="body">{md_to_html(r.get("text",""))}</div></div>'
        )
    reviews_html = ""
    if review_items:
        reviews_html = (
            f'<div class="sec">{ico("review")} Peer review · anonymized · '
            f'{len(review_items)} reviews</div>'
            f'<div class="reviews">{"".join(review_items)}</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Council Verdict: {esc(topic)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="page"><div class="inner">
  <div class="head">
    <div class="crest">{ico("scales")}</div>
    <div>
      <div class="eyebrow">LLM Council Verdict</div>
      <h1>{esc(topic)}</h1>
      <div class="meta">{"".join(chips)}</div>
    </div>
  </div>
  {question_html}
  {verdict_html}
  {council_html}
  {reviews_html}
  <footer>{ico("scales")} Generated by the LLM Council skill · anonymized peer review adapted from Karpathy's LLM Council</footer>
</div></div>
</body>
</html>"""


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    in_path = Path(argv[1])
    if not in_path.exists():
        print(f"error: session file not found: {in_path}", file=sys.stderr)
        return 1
    try:
        session = json.loads(in_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON in {in_path}: {e}", file=sys.stderr)
        return 1

    if len(argv) >= 3:
        out_path = Path(argv[2])
    else:
        date = session.get("date") or datetime.date.today().isoformat()
        out_path = in_path.parent / f"council-report-{date}-{slugify(session.get('topic',''))}.html"

    out_path.write_text(render(session), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
