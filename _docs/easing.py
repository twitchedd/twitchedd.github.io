#!/usr/bin/env python3
"""Generate _docs/pages/easing.html: every Cascade easing curve drawn as an inline SVG.

The formulas are ported one-to-one from Runtime/Easing/Ease.cs (the easings.net set). Run build.py after.
"""
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
PI = math.pi
C1 = 1.70158
C2 = C1 * 1.525
C3 = C1 + 1


def out_bounce(t):
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


def elastic(kind):
    def f(t):
        if t <= 0:
            return 0.0
        if t >= 1:
            return 1.0
        if kind == "in":
            return -2 ** (10 * t - 10) * math.sin((t * 10 - 10.75) * (2 * PI / 3))
        if kind == "out":
            return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * PI / 3)) + 1
        c5 = 2 * PI / 4.5
        return (-(2 ** (20 * t - 10) * math.sin((20 * t - 11.125) * c5)) / 2 if t < 0.5
                else (2 ** (-20 * t + 10) * math.sin((20 * t - 11.125) * c5)) / 2 + 1)
    return f


EASES = [
    ("Linear", lambda t: t, "Constant speed. Mechanical; use for progress bars and spinners."),
    ("InSine", lambda t: 1 - math.cos(t * PI / 2), ""),
    ("OutSine", lambda t: math.sin(t * PI / 2), ""),
    ("InOutSine", lambda t: -(math.cos(PI * t) - 1) / 2, "Gentle both ends. Good for looping pulses."),
    ("InQuad", lambda t: t * t, ""),
    ("OutQuad", lambda t: 1 - (1 - t) ** 2, ""),
    ("InOutQuad", lambda t: 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2, ""),
    ("InCubic", lambda t: t ** 3, "Accelerates away. Good for exits."),
    ("OutCubic", lambda t: 1 - (1 - t) ** 3, "Fast start, soft landing. The default for entrances."),
    ("InOutCubic", lambda t: 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2, "For moves between two resting places."),
    ("InQuart", lambda t: t ** 4, ""),
    ("OutQuart", lambda t: 1 - (1 - t) ** 4, ""),
    ("InOutQuart", lambda t: 8 * t ** 4 if t < 0.5 else 1 - (-2 * t + 2) ** 4 / 2, ""),
    ("InExpo", lambda t: 0 if t <= 0 else 2 ** (10 * t - 10), ""),
    ("OutExpo", lambda t: 1 if t >= 1 else 1 - 2 ** (-10 * t), "Very fast start, long settle."),
    ("InOutExpo", lambda t: 0 if t <= 0 else 1 if t >= 1 else (2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2), ""),
    ("InCirc", lambda t: 1 - math.sqrt(1 - t * t), ""),
    ("OutCirc", lambda t: math.sqrt(1 - (t - 1) ** 2), ""),
    ("InOutCirc", lambda t: (1 - math.sqrt(1 - (2 * t) ** 2)) / 2 if t < 0.5 else (math.sqrt(1 - (-2 * t + 2) ** 2) + 1) / 2, ""),
    ("InBack", lambda t: C3 * t ** 3 - C1 * t * t, "Pulls back before leaving."),
    ("OutBack", lambda t: 1 + C3 * (t - 1) ** 3 + C1 * (t - 1) ** 2, "Overshoots slightly, then settles. Dialogs and pop-ins."),
    ("InOutBack", lambda t: ((2 * t) ** 2 * ((C2 + 1) * 2 * t - C2)) / 2 if t < 0.5 else ((2 * t - 2) ** 2 * ((C2 + 1) * (t * 2 - 2) + C2) + 2) / 2, ""),
    ("InElastic", elastic("in"), ""),
    ("OutElastic", elastic("out"), "Wobbles into place. Playful rewards."),
    ("InOutElastic", elastic("inout"), ""),
    ("InBounce", lambda t: 1 - out_bounce(1 - t), ""),
    ("OutBounce", out_bounce, "Lands and bounces. A drop or a falling badge."),
    ("InOutBounce", lambda t: (1 - out_bounce(1 - 2 * t)) / 2 if t < 0.5 else (1 + out_bounce(2 * t - 1)) / 2, ""),
]


def svg(f):
    w, h, pad = 120, 90, 18          # the 0..1 box sits inside, with room for overshoot above and below
    pts = []
    for i in range(101):
        t = i / 100
        y = f(t)
        pts.append(f"{t * w:.1f},{pad + (1 - y) * (h - 2 * pad):.1f}")
    return (f'<svg viewBox="-4 0 {w + 8} {h}" role="img" aria-hidden="true">'
            f'<line x1="0" y1="{pad}" x2="{w}" y2="{pad}" class="g"/>'
            f'<line x1="0" y1="{h - pad}" x2="{w}" y2="{h - pad}" class="g"/>'
            f'<polyline points="{" ".join(pts)}" class="curve"/></svg>')


def main():
    out = ["order: 12", "group: Reference", "label: Easing curves",
           "title: Easing curves for Unity UI Toolkit animation: every Cascade ease, drawn",
           "description: All 28 easing functions in Cascade for Unity UI Toolkit, drawn as curves, with which to "
           "use for entrances, exits, pop-ins and loops, plus custom AnimationCurve easing.",
           "---",
           "<h1>Easing curves</h1>",
           "<p class=\"lede\">An ease shapes the speed of an animation over its duration. Every curve below is "
           "in both Lite and Pro, under <code>Ease</code>.</p>",
           "<pre><code class=\"cs\">panel.Animate().MoveY(0f, 0.4f).From(24f).Ease(Ease.OutCubic);</code></pre>",
           "<h2>Which one to use</h2><ul>",
           "<li><strong>Entrances:</strong> <code>OutCubic</code> (the default) or <code>OutQuart</code>. Fast start, soft landing.</li>",
           "<li><strong>Exits:</strong> <code>InCubic</code>. Accelerating away reads as \"gone\".</li>",
           "<li><strong>Moving between two places on screen:</strong> <code>InOutCubic</code>.</li>",
           "<li><strong>Pop-ins and dialogs:</strong> <code>OutBack</code> for a small overshoot "
           "(or a <a href=\"spring-animation.html\">spring</a> in Pro).</li>",
           "<li><strong>Loops and pulses:</strong> <code>InOutSine</code> with <code>LoopMode.PingPong</code>.</li>",
           "<li><strong>Progress and spinners:</strong> <code>Linear</code>.</li></ul>",
           "<h2>All curves</h2>",
           "<p class=\"muted\">The two lines mark the start and end values. Curves that cross them overshoot.</p>",
           "<div class=\"eases\">"]
    for name, f, note in EASES:
        out.append(f'<figure class="ease">{svg(f)}<figcaption><code>Ease.{name}</code>'
                   + (f"<span>{note}</span>" if note else "") + "</figcaption></figure>")
    out += ["</div>",
            "<h2>Your own curve</h2>",
            "<p>Draw a curve in the inspector and use it as an ease:</p>",
            "<pre><code class=\"cs\">[SerializeField] AnimationCurve curve = AnimationCurve.EaseInOut(0, 0, 1, 1);\n\n"
            "badge.Animate().ScaleTo(1.2f, 0.5f).Ease(Ease.FromCurve(curve));</code></pre>",
            "<p>The curve is sampled from time 0 to 1. Values above 1 or below 0 overshoot.</p>",
            "<h2>Easing in the inspector and JSON</h2>",
            "<p>Presets and JSON sequences name the ease as text (<code>\"ease\": \"OutBack\"</code>). They accept "
            "this subset: Linear, InSine, OutSine, InOutSine, InQuad, OutQuad, InOutQuad, InCubic, OutCubic, "
            "InOutCubic, OutQuart, OutExpo, OutCirc, InBack, OutBack, InOutBack, OutElastic, OutBounce. Code can use "
            "all of the curves above.</p>"]
    (HERE / "pages" / "easing.html").write_text("\n".join(out) + "\n")
    print("easing.html:", len(EASES), "curves")


if __name__ == "__main__":
    main()
