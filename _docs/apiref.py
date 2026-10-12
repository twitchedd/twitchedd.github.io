#!/usr/bin/env python3
"""Generate _docs/pages/api.html (the API reference) from Cascade's XML doc comments.

    python3 _docs/apiref.py [path/to/com.twitched.cascade] [path/to/com.twitched.cascade.lite]

Reads every public type and member under Runtime/, takes its /// <summary> (and <param>/<returns>), and
marks each member Lite when the same declaration exists in the Lite package. Run build.py afterwards.
Python 3.9+, stdlib only.
"""
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRO = Path(sys.argv[1] if len(sys.argv) > 1 else "/Users/or/Projects/UnityUI/com.twitched.cascade")
LITE = Path(sys.argv[2] if len(sys.argv) > 2 else
            Path.home() / ".cache/cascade-lite-verify/Packages/com.twitched.cascade.lite")

# Types shown, in reading order, with the section each belongs to. Anything public not listed is skipped
# (internal plumbing that happens to be public for the editor or tests).
SECTIONS = [
    ("Start an animation", ["VisualElementAnimationExtensions"]),
    ("The animation handle", ["TweenSequence", "LoopMode", "Edge"]),
    ("Easing", ["Ease", "EaseKind"]),
    ("Springs", ["SpringPreset", "SpringConfig"]),
    ("Stagger", ["StaggerBuilder", "Stagger"]),
    ("Transitions", ["Transition", "TransitionExtensions"]),
    ("Hover, press and focus", ["InteractionExtensions", "Interaction", "InteractionTrigger"]),
    ("Named states", ["VariantExtensions", "VariantSet", "VariantState"]),
    ("Settings and accessibility", ["MotionSettings", "MotionMode", "MotionChannel", "MotionStats"]),
    ("JSON sequences and presets", ["SequencePreset", "MotionError", "MotionErrorCode", "MotionAdvice",
                                    "MotionAdviceCode", "TransitionPreset", "InteractionPreset"]),
    ("Effects", ["DropShadowElement", "FilterEffects"]),
]

# Doc-comment sentences meant for us, not customers. A summary containing one is cut at that sentence.
INTERNAL = [r"pending in-editor QA", r"future work", r"\bPREVIEW\.", r"regression", r"mutation",
            r"\bv2(\.\d)?\b", r"\bv3\b", r"Phase \d", r"TODO", r"HACK", r"FIXME", r"\bspec\b"]

# Summaries for types whose doc comment is missing or is written for us rather than for customers.
OVERRIDES = {
    "TweenSequence": "What <code>Animate()</code> returns: you chain verbs on it to build the animation, and keep it "
                     "to control the animation (<code>Pause</code>, <code>Resume</code>, <code>Cancel</code>, "
                     "<code>await</code>). Verbs add to the current step and run together; <code>Then()</code> starts "
                     "the next step. The animation starts on the element's next frame, so everything you chain in "
                     "the same line applies.",
    "StaggerBuilder": "The builder <code>AnimateEach()</code> returns: the same verbs as an animation, played on every "
                      "element of a list, each starting <code>Stagger(seconds)</code> after the previous one.",
    "DropShadowElement": "A soft drop shadow or outer glow drawn with a mesh: no shaders, works in any render pipeline. "
                         "Put the element you want shadowed inside it as a child. For a glow, set both offsets to 0 "
                         "and use a bright color with more spread. Usable from UXML as <code>&lt;Cascade.DropShadowElement&gt;</code>.",
    "TransitionPreset": "An asset (Create ▸ Cascade ▸ Transition Preset) holding an enter/exit transition for the "
                        "UI Animator component or for code: <code>preset.ToTransition()</code>.",
    "InteractionPreset": "An asset (Create ▸ Cascade ▸ Interaction Preset) holding a hover, press or focus look for "
                         "the UI Animator component or for code: <code>preset.Apply(element, trigger)</code>.",
}

TYPE_RE = re.compile(r"^\s*public\s+(?:static\s+|sealed\s+|abstract\s+|readonly\s+|partial\s+)*"
                     r"(class|struct|enum|interface)\s+(\w+)")
MEMBER_RE = re.compile(r"^\s*(?:\[[^\]]*\]\s*)*public\s+(?!class|struct|enum|interface)(.+)$")


def strip_comment(line):
    return re.sub(r"//.*$", "", re.sub(r'"(?:\\.|[^"\\])*"', '""', line))


def parse(root):
    """{type: {"kind", "doc", "members": [(signature, doc)]}} for every public type under Runtime/."""
    types = {}
    for f in sorted((root / "Runtime").rglob("*.cs")):
        lines = f.read_text().splitlines()
        doc, stack, depth = [], [], 0
        i = 0
        while i < len(lines):
            line = lines[i]
            s = line.strip()
            if s.startswith("///"):
                doc.append(s[3:].strip())
                i += 1
                continue
            if s.startswith("#") or not s:
                i += 1
                continue
            current = stack[-1][0] if stack else None
            m = TYPE_RE.match(line)
            if m:
                kind, name = m.groups()
                t = types.setdefault(name, {"kind": kind, "doc": "", "members": []})
                if doc and not t["doc"]:
                    t["doc"] = " ".join(doc)
                pending = (name, kind)
            else:
                pending = None
                mm = MEMBER_RE.match(line)
                cur_kind = stack[-1][2] if stack else None
                s = re.sub(r"\s*//.*$", "", s)
                enum_line = cur_kind == "enum" and not mm and re.match(r"^\w+\s*(=\s*[^,]+)?(\s*,\s*\w+\s*(=\s*[^,]+)?)*,?$", s)
                if current and enum_line:
                    for v in [x.strip() for x in s.split(",") if x.strip()]:
                        members = types[current]["members"]
                        if all(x[0] != v for x in members):
                            members.append((v, " ".join(doc)))
                elif current and mm:
                    sig = mm.group(1)
                    # join a signature split across lines
                    j = i
                    while sig.count("(") > sig.count(")") and j + 1 < len(lines):
                        j += 1
                        sig += " " + lines[j].strip()
                    sig = re.sub(r"\s*(=>.*|\{.*|;.*)$", "", sig).strip()
                    sig = re.sub(r"\s+", " ", sig)
                    if not sig.startswith("override ") and "operator" not in sig:
                        members = types[current]["members"]
                        if all(x[0] != sig for x in members):
                            members.append((sig, " ".join(doc)))
            code = strip_comment(line)
            opens, closes = code.count("{"), code.count("}")
            if pending and opens:
                stack.append((pending[0], depth, pending[1]))
            elif pending:
                # brace on a later line
                stack.append((pending[0], depth, pending[1]))
            depth += opens - closes
            while stack and depth <= stack[-1][1] and closes:
                stack.pop()
            doc = []
            i += 1
    return types


def lite_index(root):
    if not root.exists():
        sys.exit(f"Lite package not found at {root}")
    text = "\n".join(re.sub(r"\s+", " ", f.read_text()) for f in (root / "Runtime").rglob("*.cs"))
    return text


def xml_to_html(doc):
    doc = re.sub(r"<example>.*?</example>", "", doc, flags=re.S)
    parts = {}
    for tag in ("param", "typeparam"):
        parts[tag] = re.findall(rf'<{tag} name="(\w+)">(.*?)</{tag}>', doc, flags=re.S)
        doc = re.sub(rf'<{tag} name="\w+">.*?</{tag}>', "", doc, flags=re.S)
    ret = re.findall(r"<returns>(.*?)</returns>", doc, flags=re.S)
    doc = re.sub(r"<returns>.*?</returns>|<remarks>|</remarks>", " ", doc, flags=re.S)
    summary = re.sub(r"</?summary>", " ", doc)

    def inline(t):
        t = html.escape(html.unescape(t), quote=False)
        t = re.sub(r"&lt;see (?:cref|langword)=&quot;(?:[A-Z]:)?([^&]+?)&quot;\s*/&gt;",
                   lambda m: "<code>" + m.group(1).split(".")[-1].split("(")[0] + "</code>", t)
        t = re.sub(r'&lt;see (?:cref|langword)="(?:[A-Z]:)?([^"]+?)"\s*/&gt;',
                   lambda m: "<code>" + m.group(1).split(".")[-1].split("(")[0] + "</code>", t)
        t = re.sub(r'&lt;paramref name="(\w+)"\s*/&gt;', r"<code>\1</code>", t)
        t = re.sub(r"&lt;c&gt;(.*?)&lt;/c&gt;", r"<code>\1</code>", t)
        t = re.sub(r"&lt;b&gt;(.*?)&lt;/b&gt;", r"<strong>\1</strong>", t)
        # multi-statement examples flatten badly onto one line; the guides carry the examples instead
        t = re.sub(r"&lt;code&gt;(.*?)&lt;/code&gt;",
                   lambda m: "" if ";" in m.group(1) else "<code>" + m.group(1) + "</code>", t, flags=re.S)
        t = re.sub(r"(:|, e\.g\.|for example)\s*(?=[.<]|$)", ".", t)
        t = re.sub(r"&lt;/?(para|list|item|description|term|br)\s*/?&gt;", " ", t)
        t = re.sub(r"&lt;[^&]*?&gt;", "", t)
        t = t.replace("⚠️", "").replace("—", ",").replace(" ,", ",")
        return re.sub(r"\s+", " ", t).strip()

    text = inline(summary)
    text = re.sub(r"\s*\((?:see )?[^()]*(?:API-FINDINGS|Documentation~)[^()]*\)", "", text)
    text = re.sub(r"[^.]*(?:API-FINDINGS|Documentation~)[^.]*\.?", "", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept = []
    for s_ in sentences:
        if any(re.search(p, s_, re.I) for p in INTERNAL):
            break
        kept.append(s_)
    text = " ".join(kept)
    extra = ""
    if parts["param"]:
        extra += "<dl class=\"params\">" + "".join(
            f"<dt><code>{n}</code></dt><dd>{inline(d)}</dd>" for n, d in parts["param"]) + "</dl>"
    if ret:
        extra += f"<p class=\"ret\">Returns: {inline(ret[0])}</p>"
    return text, extra


def main():
    pro = parse(PRO)
    lite = lite_index(LITE)
    out = ["order: 13", "group: Reference", "label: API reference",
           "title: Cascade API reference: Unity UI Toolkit animation (C#)",
           "description: Every public type and method in Cascade, the animation library for Unity UI Toolkit: "
           "Animate, TweenSequence verbs, easing, springs, stagger, transitions, interactions, variants, "
           "settings, JSON sequences and effects. Lite and Pro marked.",
           "---",
           "<h1>API reference</h1>",
           "<p class=\"lede\">Every public type and member, generated from the comments in the source. Members "
           "marked <span class=\"tier lite\">Lite</span> are in both tiers; everything else is Pro.</p>",
           "<p>All types are in the <code>Cascade</code> namespace. Durations are in seconds.</p>",
           "<nav class=\"toc\"><ul>"]
    for sec, names in SECTIONS:
        anchor = re.sub(r"\W+", "-", sec.lower()).strip("-")
        out.append(f'<li><a href="#{anchor}">{html.escape(sec)}</a></li>')
    out.append("</ul></nav>")
    missing = []
    count = 0
    for sec, names in SECTIONS:
        anchor = re.sub(r"\W+", "-", sec.lower()).strip("-")
        out.append(f'<h2 id="{anchor}">{html.escape(sec)}</h2>')
        for name in names:
            t = pro.get(name)
            if not t:
                missing.append(name)
                continue
            in_lite = re.search(rf"\b(class|struct|enum)\s+{name}\b", lite) is not None
            badge = '<span class="tier lite">Lite</span>' if in_lite else '<span class="tier pro">Pro</span>'
            summary = OVERRIDES.get(name) or xml_to_html(t["doc"])[0]
            out.append(f'<h3 id="{name}"><code>{name}</code> <span class="kind">{t["kind"]}</span> {badge}</h3>')
            if summary:
                out.append(f"<p>{summary}</p>")
            rows = []
            for sig, doc in t["members"]:
                if t["kind"] == "enum" or ("(" not in sig.split("=")[0] and "=" in sig):
                    sig = sig.split("=")[0].strip()   # enum values and fields: drop the initializer
                if name == "SequencePreset" and "(" not in sig:
                    continue                          # the serialized step/action fields; the JSON format covers them
                member_lite = in_lite and re.sub(r"\s+", " ", sig) in lite
                desc, extra = xml_to_html(doc)
                tag = ' <span class="tier lite">Lite</span>' if member_lite else ""
                mname = re.search(r"(\w+)\s*(?:\(|$)", sig.split("=")[0].strip()).group(1)
                mid = f"{name}-{mname}"
                n = sum(1 for r in rows if f'id="{mid}' in r)
                if n:
                    mid += f"-{n + 1}"
                rows.append(f'<div class="member" id="{mid}"><pre class="sig"><code>{html.escape(sig)}</code></pre>'
                            f'<div class="mdoc">{tag} {desc}{extra}</div></div>')
                count += 1
            out.extend(rows)
    (HERE / "pages" / "api.html").write_text("\n".join(out) + "\n")
    print(f"api.html: {count} members; types not found: {missing or 'none'}")


if __name__ == "__main__":
    main()
