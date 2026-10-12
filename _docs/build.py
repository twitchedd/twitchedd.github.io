#!/usr/bin/env python3
"""Build the Cascade docs pages: _docs/pages/*.html (body fragments) -> cascade/docs/*.html.

Each fragment starts with a header block of `key: value` lines, then a line with `---`, then the body HTML.
Keys: title, description, order, label. Code blocks written as <pre><code class="cs"> get simple
highlighting (comments, numbers, method names) in the site's colors.

    python3 _docs/build.py

Folders starting with "_" are not published by GitHub Pages, so this source stays private to the repo.
Python 3.9+, stdlib only.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent / "pages"
OUT = ROOT / "cascade" / "docs"
BASE = "https://twitchedd.github.io/cascade/docs/"
PRO = "https://assetstore.unity.com/packages/slug/394760"
LITE = "https://assetstore.unity.com/packages/slug/394764"


def highlight(code):
    out = []
    for line in html.unescape(code).split("\n"):
        comment = ""
        m = re.search(r"//.*$", line)
        if m:
            line, comment = line[:m.start()], m.group(0)
        s = html.escape(line, quote=False)
        s = re.sub(r"(?<![\w.#-])(\d+(?:\.\d+)?f?)\b", r'<span class="n">\1</span>', s)
        s = re.sub(r"\.([A-Z]\w*)(?=\(|&lt;)", r'.<span class="k">\1</span>', s)
        if comment:
            s += '<span class="c">' + html.escape(comment, quote=False) + "</span>"
        out.append(s)
    return "\n".join(out)


def parse(path):
    head, body = path.read_text().split("\n---\n", 1)
    meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
    body = re.sub(r'<pre><code class="cs">(.*?)</code></pre>',
                  lambda m: '<pre><code class="cs">' + highlight(m.group(1).strip("\n")) + "</code></pre>",
                  body, flags=re.S)
    def anchor(m):
        text = re.sub(r"<[^>]+>", "", m.group(2))
        aid = re.sub(r"[^a-z0-9]+", "-", html.unescape(text).lower()).strip("-")
        return f'<{m.group(1)} id="{aid}">{m.group(2)}</{m.group(1)}>'
    body = re.sub(r"<(h2|h3)>(.*?)</\1>", anchor, body)
    slug = path.stem
    return {**meta, "slug": slug, "file": "index.html" if slug == "index" else slug + ".html", "body": body}


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://twitchedd.github.io/img/cover.png">
<link rel="icon" href="../../img/avatar.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="docs.css">
<script src="search.js" defer></script>
<script type="application/ld+json">
{jsonld}
</script>
</head>
<body>
<div class="layout">
<nav class="side" aria-label="Cascade docs">
  <a class="home" href="../../">twitched<span>_</span></a>
  <div class="search" role="search">
    <input id="q" type="search" placeholder="Search docs  /" aria-label="Search the docs" autocomplete="off" spellcheck="false">
    <ul id="results" role="listbox" hidden></ul>
  </div>
{nav}
  </ul>
  <p class="group">Get it</p>
  <ul>
    <li><a href="{lite}">Cascade Lite (free)</a></li>
    <li><a href="{pro}">Cascade Pro</a></li>
  </ul>
</nav>
<main class="doc">
<article>
{body}
</article>
<nav class="pager" aria-label="Next and previous page">{pager}</nav>
</main>
</div>
<footer>twitched · Cascade, the animation library for Unity UI Toolkit · <a href="../../">twitchedd.github.io</a></footer>
</body>
</html>
"""


def main():
    pages = sorted((parse(p) for p in SRC.glob("*.html")), key=lambda p: int(p["order"]))
    for i, p in enumerate(pages):
        url = BASE + ("" if p["slug"] == "index" else p["file"])
        current = ' aria-current="page"'
        nav, group = [], None
        for q in pages:
            if q.get("group") != group:
                if group is not None:
                    nav.append('  </ul>')
                group = q.get("group")
                nav.append(f'  <p class="group">{html.escape(group or "")}</p>\n  <ul>')
            nav.append(f'    <li><a href="{q["file"]}"{current if q is p else ""}>{html.escape(q["label"])}</a></li>')
        nav = "\n".join(nav)
        prev_ = pages[i - 1] if i else None
        next_ = pages[i + 1] if i + 1 < len(pages) else None
        pager = (f'<a href="{prev_["file"]}">← {html.escape(prev_["label"])}</a>' if prev_ else "<span></span>") + \
                (f'<a href="{next_["file"]}">{html.escape(next_["label"])} →</a>' if next_ else "")
        jsonld = json.dumps({
            "@context": "https://schema.org", "@type": "TechArticle",
            "headline": p["title"], "description": p["description"], "url": url,
            "author": {"@type": "Organization", "name": "twitched", "url": "https://twitchedd.github.io/"},
            "about": {"@type": "SoftwareApplication", "name": "Cascade",
                      "applicationCategory": "DeveloperApplication",
                      "operatingSystem": "Unity 6000.0 or later",
                      "description": "Animation library for Unity UI Toolkit: tweens, springs, stagger and transitions.",
                      "offers": [{"@type": "Offer", "name": "Cascade Lite", "price": "0", "priceCurrency": "USD", "url": LITE},
                                 {"@type": "Offer", "name": "Cascade Pro", "url": PRO}]},
        }, indent=1)
        page = TEMPLATE.format(title=html.escape(p["title"]), description=html.escape(p["description"]),
                               url=url, jsonld=jsonld, nav=nav, body=p["body"].strip(), pager=pager,
                               lite=LITE, pro=PRO)
        (OUT / p["file"]).write_text(page)
        print("wrote", (OUT / p["file"]).relative_to(ROOT))

    index = []
    for q in pages:
        # one entry per section: the text from each h2/h3 to the next one
        body = q["body"]
        cuts = [(m.start(), m.group(2),
                 re.sub(r"<[^>]+>", "", re.sub(r'<span class="(?:tier|kind)[^"]*">.*?</span>', "", m.group(3))))
                for m in re.finditer(r'<(h1|h2|h3)(?: id="([^"]*)")?>(.*?)</\1>', body, flags=re.S)]
        for k, (start, aid, head) in enumerate(cuts):
            end = cuts[k + 1][0] if k + 1 < len(cuts) else len(body)
            text = re.sub(r"</?(?:span|code|a|strong|em|mark)\b[^>]*>", "", body[start:end])   # inline: no gap
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", html.unescape(text)).strip()
            head = html.unescape(head).strip()
            text = text[len(head):].strip()
            index.append({"p": q["label"], "h": head, "u": q["file"] + (f"#{aid}" if aid else ""), "x": text[:1200]})
        for m in re.finditer(r'<div class="member" id="([^"]+)"><pre class="sig"><code>(.*?)</code></pre>'
                             r'<div class="mdoc">(.*?)</div></div>', body, flags=re.S):
            sig = html.unescape(m.group(2))
            text = re.sub(r'<span class="tier[^"]*">.*?</span>', "", m.group(3))
            text = re.sub(r"</?(?:span|code|a|strong|em|mark)\b[^>]*>", "", text)
            text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()
            typ, member = m.group(1).split("-")[:2]
            index.append({"p": f"API · {typ}", "h": member, "u": f'{q["file"]}#{m.group(1)}', "x": f"{sig}. {text}"[:600]})
    (OUT / "search-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote search-index.json ({len(index)} sections)")

    urls = ["https://twitchedd.github.io/"] + [BASE + ("" if p["slug"] == "index" else p["file"]) for p in pages]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    llms = ["# Cascade: animation library for Unity UI Toolkit", "",
            "> Cascade animates Unity UI Toolkit VisualElements (UXML/USS, UIElements) at runtime: tweens, easing, "
            "springs, stagger, enter/exit and screen transitions, hover/press/focus, named states, a no-code "
            "UI Animator and validated JSON animation sequences. Unity 6000.0+, pure C#, no dependencies. "
            f"Cascade Lite is free and MIT licensed ({LITE}); Cascade Pro adds springs, stagger, transitions, "
            f"interactions, variants, the UI Animator, JSON sequences and effects ({PRO}). "
            "Agent skill: npx skills add twitchedd/cascade-skill", "", "## Docs", ""]
    for q in pages:
        u = BASE + ("" if q["slug"] == "index" else q["file"])
        llms.append(f"- [{q['label']}]({u}): {q['description']}")
    (ROOT / "llms.txt").write_text("\n".join(llms) + "\n")
    schema = Path("/Users/or/Projects/UnityUI/com.twitched.cascade/Documentation~/cascade-sequence.schema.json")
    if schema.exists():
        (OUT / schema.name).write_text(schema.read_text())
    (ROOT / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://twitchedd.github.io/sitemap.xml\n")
    print("wrote sitemap.xml, robots.txt, llms.txt, schema")


if __name__ == "__main__":
    main()
