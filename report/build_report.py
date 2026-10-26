"""Build the architecture diagram, the PDF report and the review PPT.

    pip install python-pptx playwright pillow pygments   # uses the installed Google Chrome
    python capture_screens.py   # optional: refresh live-app screenshots
    python build_report.py

AWS console screenshots: save them as report/screens/aws/<key>.png using the
keys in content.AWS_SCREENS; missing ones are shown as labelled placeholders.
"""
from __future__ import annotations

import html
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename

import content as C

HERE = Path(__file__).parent
ROOT = HERE.parent
SCREENS = HERE / "screens"
AWS_DIR = SCREENS / "aws"
OUT_PDF = HERE / "CloudDQ_AI_Report.pdf"
OUT_PPT = HERE / "CloudDQ_AI_Review.pptx"
ARCH_PNG = HERE / "architecture.png"

SEA = "#1d6b5c"
INK = "#13202b"
MIST = "#dce8e1"
CORAL = "#c8613f"
PAPER = "#f3f7f4"


# ---------------------------------------------------------------- architecture

def architecture_svg() -> str:
    boxes = {
        "user": (30, 400, 180, 120, "User (browser)", "Data User · Business User", "#5b6b78"),
        "github": (270, 190, 240, 100, "GitHub", "clouddq-ai · main branch", "#24292f"),
        "amplify": (270, 400, 240, 120, "AWS Amplify", "React SPA hosting + CI", "#c2410c"),
        "cognito": (420, 670, 340, 120, "Amazon Cognito", "User pool · DataUser / BusinessUser", "#b91c1c"),
        "apigw": (590, 400, 240, 120, "Amazon API Gateway", "REST · Cognito authorizer", "#7c3aed"),
        "lambda": (900, 400, 240, 120, "AWS Lambda", "clouddq-api · Python 3.12", "#d97706"),
        "s3": (1290, 175, 280, 90, "Amazon S3", "Private CSV bucket", "#15803d"),
        "dynamo": (1290, 283, 280, 90, "Amazon DynamoDB", "Table CloudDQ · GSI1", "#1d4ed8"),
        "comprehend": (1290, 391, 280, 90, "Amazon Comprehend", "PII detection in columns", "#0e7490"),
        "bedrock": (1290, 499, 280, 90, "Amazon Bedrock", "Nova Lite · access pending", "#0f766e"),
        "sns": (1290, 607, 280, 90, "Amazon SNS", "Alert + alarm emails", "#a21caf"),
        "cw": (1290, 715, 280, 90, "Amazon CloudWatch", "Logs + error alarm", "#be185d"),
    }
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="960" viewBox="0 0 1600 960" '
        'font-family="Helvetica, Arial, sans-serif">',
        '<defs><marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>',
        f'<rect width="1600" height="960" fill="{PAPER}"/>',
        f'<text x="30" y="52" font-size="32" font-weight="700" fill="{INK}">CloudDQ AI — AWS serverless architecture</text>',
        '<text x="30" y="84" font-size="17" fill="#4b5b66">Region us-east-1 (N. Virginia) · single AWS account</text>',
        f'<rect x="1270" y="160" width="320" height="682" rx="18" fill="none" stroke="{SEA}" stroke-dasharray="8 6" stroke-width="2"/>',
        f'<text x="1430" y="829" font-size="14" text-anchor="middle" fill="{SEA}">via IAM role clouddq-lambda-role</text>',
    ]
    for x, y, w, h, title, sub, color in boxes.values():
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="white" stroke="{color}" stroke-width="2.5"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="10" rx="5" fill="{color}"/>')
        parts.append(f'<text x="{x + w / 2}" y="{y + h / 2 - 2}" font-size="21" font-weight="700" text-anchor="middle" fill="{INK}">{html.escape(title)}</text>')
        parts.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 24}" font-size="14" text-anchor="middle" fill="#4b5b66">{html.escape(sub)}</text>')

    def arrow(x1, y1, x2, y2, label="", lx=None, ly=None):
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="2.2" marker-end="url(#a)"/>')
        if label:
            cx = lx if lx is not None else (x1 + x2) / 2
            cy = ly if ly is not None else (y1 + y2) / 2
            tw = len(label) * 7.2 + 10
            parts.append(f'<rect x="{cx - tw / 2}" y="{cy - 12}" width="{tw}" height="20" rx="4" fill="{PAPER}"/>')
            parts.append(f'<text x="{cx}" y="{cy + 3}" font-size="13" text-anchor="middle" fill="{INK}">{html.escape(label)}</text>')

    arrow(210, 460, 268, 460, "HTTPS", 239, 436)
    arrow(390, 290, 390, 398, "CI build on push", 460, 344)
    arrow(510, 445, 588, 445, "JWT", 549, 421)
    arrow(830, 460, 898, 460, "proxy", 864, 436)
    arrow(430, 520, 520, 668, "sign-in → ID token", 390, 600)
    arrow(700, 520, 650, 668, "validates JWT", 755, 600)
    arrow(1140, 415, 1288, 220, "presigned URL / read")
    arrow(1140, 433, 1288, 328, "datasets, runs, issues")
    arrow(1140, 451, 1288, 436, "sample values")
    arrow(1140, 469, 1288, 544, "metrics JSON only")
    arrow(1140, 487, 1288, 652, "alert email")
    arrow(1140, 505, 1288, 760, "logs")
    parts.append(f'<path d="M120 400 L120 140 L1430 140 L1430 178" fill="none" stroke="{SEA}" stroke-width="2.2" '
                 f'stroke-dasharray="7 6" marker-end="url(#a)"/>')
    parts.append(f'<rect x="420" y="120" width="720" height="22" fill="{PAPER}"/>')
    parts.append(f'<text x="780" y="136" font-size="15" text-anchor="middle" fill="{SEA}">CSV upload straight to S3 with a 15-minute presigned PUT URL (no AWS keys in browser)</text>')
    parts.append(f'<rect x="30" y="855" width="1560" height="80" rx="14" fill="white" stroke="#334155" stroke-width="2"/>')
    parts.append(f'<text x="810" y="889" font-size="20" font-weight="700" text-anchor="middle" fill="{INK}">AWS IAM</text>')
    parts.append('<text x="810" y="917" font-size="15" text-anchor="middle" fill="#4b5b66">'
                 'IAM users Pooja · DewlynMary · LathikaShree (scoped policies) · Lambda execution role clouddq-lambda-role</text>')
    parts.append("</svg>")
    return "".join(parts)


def flow_svg() -> str:
    steps = ["Sign in\n(Cognito)", "Upload CSV\n(presigned S3)", "Analyse\n(Lambda DQ engine)", "Store\n(DynamoDB)",
             "Report\n(dashboard)", "AI summary\n(Bedrock)", "Alert\n(Business User)", "Correct &\nre-validate"]
    w, gap, x0, y = 165, 22, 30, 60
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="230" viewBox="0 0 1600 230" font-family="Helvetica, Arial, sans-serif">',
             f'<rect width="1600" height="230" fill="{PAPER}"/>',
             f'<defs><marker id="b" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>']
    for i, s in enumerate(steps):
        x = x0 + i * (w + gap + 5)
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="110" rx="14" fill="white" stroke="{SEA}" stroke-width="2.5"/>')
        parts.append(f'<circle cx="{x + 22}" cy="{y + 22}" r="14" fill="{SEA}"/><text x="{x + 22}" y="{y + 27}" font-size="15" fill="white" text-anchor="middle" font-weight="700">{i + 1}</text>')
        a, b = s.split("\n")
        parts.append(f'<text x="{x + w / 2}" y="{y + 62}" font-size="18" font-weight="700" text-anchor="middle" fill="{INK}">{a}</text>')
        parts.append(f'<text x="{x + w / 2}" y="{y + 88}" font-size="14" text-anchor="middle" fill="#4b5b66">{b}</text>')
        if i < len(steps) - 1:
            parts.append(f'<line x1="{x + w + 2}" y1="{y + 55}" x2="{x + w + gap + 3}" y2="{y + 55}" stroke="{INK}" stroke-width="2.2" marker-end="url(#b)"/>')
    parts.append("</svg>")
    return "".join(parts)


def render_svgs(browser) -> None:
    for name, svg, (w, h) in [("architecture", architecture_svg(), (1600, 960)), ("flow", flow_svg(), (1600, 230))]:
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        page.set_content(f"<html><body style='margin:0'>{svg}</body></html>")
        page.screenshot(path=str(HERE / f"{name}.png"))
        page.close()


# ---------------------------------------------------------------- PDF report

def esc(s: str) -> str:
    return html.escape(s)


def img_tag(path: Path, caption: str, cls: str = "shot") -> str:
    if path.exists():
        return f'<figure class="{cls}"><img src="{path.resolve().as_uri()}"/><figcaption>{esc(caption)}</figcaption></figure>'
    return (f'<figure class="{cls}"><div class="placeholder">Insert screenshot<br/><small>{esc(caption)}</small><br/>'
            f'<code>report/screens/aws/{esc(path.stem)}.png</code></div><figcaption>{esc(caption)}</figcaption></figure>')


def code_html() -> tuple[str, str]:
    formatter = HtmlFormatter(style="friendly", nowrap=False, linenos="inline")
    blocks, toc = [], []
    for gi, (group, files) in enumerate(C.CODE_GROUPS):
        toc.append(f"<li>{esc(group)}<ul>" + "".join(f"<li><code>{esc(f)}</code></li>" for f in files) + "</ul></li>")
        blocks.append(f'<h2 class="{"pb" if gi else ""}">{esc(group)}</h2>')
        for f in files:
            path = ROOT / f
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            if not text.strip():
                text = "# (empty package marker)\n" if f.endswith(".py") else "(empty)\n"
            try:
                lexer = get_lexer_for_filename(f)
            except Exception:  # noqa: BLE001
                from pygments.lexers import TextLexer
                lexer = TextLexer()
            blocks.append(f'<h3 class="file"><code>{esc(f)}</code> <span>{len(text.splitlines())} lines</span></h3>')
            blocks.append(highlight(text, lexer, formatter))
    return "<ol>" + "".join(toc) + "</ol>", "".join(blocks), formatter.get_style_defs(".highlight")


def report_html() -> str:
    toc_code, code_blocks, pyg_css = code_html()
    team_rows = "".join(f"<tr><td>{i + 1}</td><td>{esc(m['name'])}</td><td>{esc(m['reg'])}</td><td>{esc(m['role'])}</td></tr>"
                        for i, m in enumerate(C.TEAM))
    modules_list = "".join(f"<tr><td><b>{m['id']}</b></td><td>{esc(m['name'])}</td><td>{esc(m['summary'])}</td><td>{esc(m['aws'])}</td></tr>"
                           for m in C.MODULES)
    module_details = "".join(
        f"<h3>{m['id']} · {esc(m['name'])}</h3><p class='muted'>AWS services: {esc(m['aws'])}</p><ul>"
        + "".join(f"<li>{esc(d)}</li>" for d in m["details"]) + "</ul>"
        for m in C.MODULES)
    services_rows = "".join(f"<tr><td><b>{i + 1}. {esc(n)}</b></td><td>{esc(u)}</td><td><code>{esc(r)}</code></td></tr>"
                            for i, (n, u, r) in enumerate(C.AWS_SERVICES))
    contrib = "".join(
        f"<h3>{esc(c['name'])} — {esc(c['focus'])}</h3><p class='muted'>Modules: {esc(c['modules'])}</p><ul>"
        + "".join(f"<li>{esc(i)}</li>" for i in c["items"]) + "</ul>"
        for c in C.CONTRIBUTIONS)
    tools_rows = "".join(f"<tr><td><b>{esc(k)}</b></td><td>{esc(v)}</td></tr>" for k, v in C.TOOLS)
    aws_shots = "".join(img_tag(AWS_DIR / f"{k}.png", f"{svc} — {where}") for k, svc, where in C.AWS_SCREENS)
    walk_dir = SCREENS / "walkthrough_sns"
    walkthrough = "".join(img_tag(walk_dir / f"{k}.png", f"Step {i + 1}: {t} — {d}")
                          for i, (k, t, d) in enumerate(C.WALKTHROUGH_SNS))
    feat_shots = "".join(img_tag(SCREENS / f"{k}.png", f"Fig. {i + 1}: {t} — {d}")
                         for i, (k, t, d) in enumerate(C.FEATURE_SCREENS))
    challenges = "".join(f"<li><b>{esc(t)}.</b> {esc(d)}</li>" for t, d in C.CHALLENGES)
    refs = "".join(f"<li>{esc(r)}</li>" for r in C.REFERENCES)

    return f"""<!doctype html><html><head><meta charset="utf-8"/><style>
@page {{ size: A4; margin: 18mm 16mm 18mm 16mm; }}
body {{ font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; color: {INK}; font-size: 10.5pt; line-height: 1.5; }}
h1 {{ color: {SEA}; font-size: 20pt; margin: 0 0 6pt; border-bottom: 2px solid {MIST}; padding-bottom: 4pt; page-break-before: always; }}
h1.first {{ page-break-before: avoid; }}
h2 {{ color: {SEA}; font-size: 14pt; margin: 14pt 0 6pt; }}
h2.pb {{ page-break-before: always; }}
h3 {{ font-size: 11.5pt; margin: 12pt 0 3pt; }}
h3.file {{ font-size: 9.5pt; background: {MIST}; padding: 3pt 6pt; border-radius: 4px; margin-top: 12pt; page-break-after: avoid; }}
h3.file span {{ float: right; font-weight: 400; color: #4b5b66; }}
.muted {{ color: #4b5b66; margin: 0 0 4pt; font-size: 9.5pt; }}
table {{ border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 9.5pt; }}
th, td {{ border: 1px solid #c9d6cf; padding: 5pt 6pt; vertical-align: top; text-align: left; }}
th {{ background: {SEA}; color: white; }}
tr:nth-child(even) td {{ background: #f7faf8; }}
code {{ font-family: Menlo, Consolas, monospace; font-size: 8.5pt; }}
.cover {{ height: 255mm; display: flex; flex-direction: column; justify-content: center; }}
.cover .t {{ font-size: 40pt; font-weight: 800; color: {SEA}; margin: 0; }}
.cover .s {{ font-size: 16pt; margin: 6pt 0 24pt; }}
.cover table td {{ font-size: 11pt; }}
.formula {{ background: {PAPER}; border-left: 4px solid {SEA}; padding: 8pt 10pt; font-family: Menlo, monospace; font-size: 9.5pt; }}
figure {{ margin: 8pt 0 12pt; page-break-inside: avoid; }}
figure img {{ width: 100%; border: 1px solid #c9d6cf; border-radius: 6px; }}
figcaption {{ font-size: 9pt; color: #4b5b66; text-align: center; margin-top: 3pt; }}
figure.half {{ display: inline-block; width: 48.5%; vertical-align: top; margin-right: 1%; }}
.placeholder {{ height: 150pt; border: 2px dashed #9fb3a9; border-radius: 8px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center; color: #4b5b66; background: #fbfdfc; font-size: 11pt; padding: 6pt; }}
.highlight {{ font-size: 7.4pt; line-height: 1.35; }}
.highlight pre {{ margin: 0; white-space: pre-wrap; word-break: break-word; font-family: Menlo, Consolas, monospace; }}
.highlight {{ padding: 4pt 6pt; border-radius: 4px; }}
.highlight .linenos {{ color: #9aa7b0; padding-right: 6pt; }}
.team th:nth-child(1) {{ width: 5%; }} .team th:nth-child(2) {{ width: 22%; }} .team th:nth-child(3) {{ width: 18%; }}
.toc li {{ margin: 2pt 0; }}
{pyg_css}
</style></head><body>

<section class="cover">
  <p class="t">{esc(C.TITLE)}</p>
  <p class="s">{esc(C.SUBTITLE)}</p>
  <table><tr><th style="width:20%">Team name</th><td colspan="3">{esc(C.TEAM_NAME)}</td></tr></table>
  <table class="team"><tr><th>#</th><th>Team member</th><th>Reg. No.</th><th>Role</th></tr>{team_rows}</table>
  <p class="muted" style="margin-top:18pt">Live application: {esc(C.LIVE_URL)}<br/>Source: {esc(C.REPO)}</p>
</section>

<h1>Contents</h1>
<ol class="toc">
<li>Title and Team</li><li>Objective</li><li>List of Modules</li><li>Detailed Description of the Modules</li>
<li>Architecture</li><li>Individual Contribution</li><li>Tools / Software Requirements</li><li>AWS Services Used</li>
<li>Screenshots of AWS Services</li><li>Feature Output Screenshots</li><li>Results, Challenges and Future Scope</li>
<li>References</li><li>Appendix — Complete Module Code</li></ol>

<h1>1. Title and Team</h1>
<p><b>Project title:</b> {esc(C.TITLE)} — {esc(C.SUBTITLE)}</p>
<p><b>Team name:</b> {esc(C.TEAM_NAME)}</p>
<table class="team"><tr><th>#</th><th>Team member</th><th>Reg. No.</th><th>Role</th></tr>{team_rows}</table>

<h1>2. Objective</h1>
<p>{esc(C.OBJECTIVE)}</p>
<ul>{''.join(f'<li>{esc(p)}</li>' for p in C.OBJECTIVE_POINTS)}</ul>
<h2>Data quality score</h2>
<div class="formula">DQ = 0.25×Completeness + 0.20×Validity + 0.15×Uniqueness + 0.15×Consistency + 0.15×Accuracy + 0.10×Timeliness<br/>
Health: 80–100 HEALTHY (fit for analytics) · 60–79 WARNING · &lt;60 CRITICAL</div>

<h1>3. List of Modules</h1>
<table><tr><th>ID</th><th>Module</th><th>Purpose</th><th>AWS services</th></tr>{modules_list}</table>

<h1>4. Detailed Description of the Modules</h1>
{module_details}

<h1>5. Architecture</h1>
<p>CloudDQ AI is fully serverless. The React application is hosted on AWS Amplify. Users sign in to Amazon Cognito and
receive a JWT. Every API call goes to Amazon API Gateway, whose Cognito authorizer validates the token before invoking a single
AWS Lambda function. Lambda issues presigned S3 URLs, reads uploaded CSVs from Amazon S3, runs the data-quality engine, stores
results in Amazon DynamoDB, asks Amazon Bedrock for an executive summary from aggregated metrics, and writes logs to Amazon
CloudWatch. IAM controls the team's console access and the function's permissions.</p>
{img_tag(ARCH_PNG, "Fig. A1: CloudDQ AI AWS architecture")}
{img_tag(HERE / "flow.png", "Fig. A2: End-to-end workflow")}
<h2>DynamoDB single-table design</h2>
<table><tr><th>Entity</th><th>PK</th><th>SK</th><th>GSI1</th></tr>
<tr><td>Dataset</td><td><code>DATASET#&lt;id&gt;</code></td><td><code>META</code></td><td><code>USER#&lt;sub&gt;</code> / <code>DATASET#…</code></td></tr>
<tr><td>Analysis run</td><td><code>DATASET#&lt;id&gt;</code></td><td><code>RUN#&lt;iso time&gt;</code></td><td>—</td></tr>
<tr><td>Issue</td><td><code>DATASET#&lt;id&gt;</code></td><td><code>ISSUE#&lt;id&gt;</code></td><td>—</td></tr>
<tr><td>Alert</td><td><code>ALERT#&lt;id&gt;</code></td><td><code>META</code></td><td><code>USER#&lt;sub&gt;</code> / <code>ALERT#…</code></td></tr></table>
<h2>REST API (JWT-protected)</h2>
<table><tr><th>Method</th><th>Path</th><th>Role</th></tr>
<tr><td>POST</td><td>/datasets/upload-url</td><td>DataUser</td></tr><tr><td>POST</td><td>/datasets</td><td>DataUser</td></tr>
<tr><td>GET</td><td>/datasets, /datasets/{{id}}</td><td>Both</td></tr><tr><td>POST</td><td>/datasets/{{id}}/analyze</td><td>DataUser</td></tr>
<tr><td>GET</td><td>/datasets/{{id}}/runs · /report · /export · /issues</td><td>Both</td></tr>
<tr><td>POST</td><td>/datasets/{{id}}/summary</td><td>Both</td></tr><tr><td>POST</td><td>/datasets/{{id}}/correction</td><td>DataUser</td></tr>
<tr><td>POST / GET</td><td>/alerts</td><td>BusinessUser / Both</td></tr>
<tr><td>POST</td><td>/issues/{{id}}/assign | acknowledge | resolve | reopen</td><td>Mostly DataUser</td></tr></table>
<h2>Security</h2>
<ul><li>Cognito groups for role-based access, enforced again in Lambda.</li><li>JWT validated by API Gateway on every request.</li>
<li>Private, encrypted S3; uploads by 15-minute presigned PUT URLs; the browser never holds AWS keys.</li>
<li>Bedrock receives aggregated metrics JSON only — raw CSV rows stay in S3.</li>
<li>Separate IAM users per team member with scoped policies; no root use for daily work.</li></ul>

<h1>6. Individual Contribution</h1>
<table><tr><th>Member</th><th>Reg. No.</th><th>Focus</th><th>Modules</th></tr>
{''.join(f"<tr><td>{esc(c['name'])}</td><td>{esc(next((m['reg'] for m in C.TEAM if m['name'] == c['name']), '—'))}</td><td>{esc(c['focus'])}</td><td>{esc(c['modules'])}</td></tr>" for c in C.CONTRIBUTIONS[:3])}
</table>
{contrib}

<h1>7. Tools / Software Requirements</h1>
<table><tr><th style="width:22%">Category</th><th>Tools</th></tr>{tools_rows}</table>

<h1>8. AWS Services Used</h1>
<p>Ten application services plus IAM, all in region <b>us-east-1</b> (N. Virginia). Nine run end to end, including the AI
service Amazon Comprehend; Amazon Bedrock is integrated in code and waiting for AWS to enable model access on the account.</p>
<table><tr><th style="width:24%">Service</th><th>Use in CloudDQ AI</th><th style="width:28%">Resource</th></tr>{services_rows}</table>

<h1>9. Screenshots of AWS Services</h1>
<p class="muted">Console screenshots of each configured service.</p>
{aws_shots}
<h2 class="pb">Walkthrough — Lathika connects Amazon SNS to CloudWatch</h2>
<p>Recorded from the LathikaShree IAM user: create the SNS topic, then add it as the notification action of the
clouddq-api-errors alarm. Email subscribers are added on the topic page (step 5) and must confirm the email AWS sends.</p>
{walkthrough}

<h1>10. Feature Output Screenshots</h1>
<p class="muted">Captured from the live deployment {esc(C.LIVE_URL)} with the demo Data User and Business User accounts.</p>
{feat_shots}

<h1>11. Results, Challenges and Future Scope</h1>
<h2>Results</h2><ul>{''.join(f'<li>{esc(r)}</li>' for r in C.RESULTS)}</ul>
<h2>Challenges and how they were handled</h2><ul>{challenges}</ul>
<h2>Future scope</h2><ul>{''.join(f'<li>{esc(f)}</li>' for f in C.FUTURE)}</ul>

<h1>12. References</h1>
<ol>{refs}</ol>

<h1>Appendix — Complete Module Code</h1>
<p class="muted">Every source file of the project, grouped by module.</p>
<div class="toc">{toc_code}</div>
{code_blocks}
</body></html>"""


# ---------------------------------------------------------------- PPT

def rgb(hexstr: str) -> RGBColor:
    return RGBColor.from_string(hexstr.lstrip("#"))


class Deck:
    W, H = Inches(13.333), Inches(7.5)

    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = self.W, self.H
        self.blank = self.prs.slide_layouts[6]
        self.n = 0

    def slide(self, title: str | None = None, kicker: str | None = None):
        s = self.prs.slides.add_slide(self.blank)
        self.n += 1
        bg = s.background.fill
        bg.solid()
        bg.fore_color.rgb = rgb(PAPER)
        if title:
            bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.18), self.H)
            bar.fill.solid(); bar.fill.fore_color.rgb = rgb(SEA); bar.line.fill.background()
            if kicker:
                self.text(s, kicker.upper(), Inches(0.6), Inches(0.35), Inches(12), Inches(0.35), 12, SEA, bold=True)
            self.text(s, title, Inches(0.6), Inches(0.6), Inches(12.2), Inches(0.8), 30, INK, bold=True)
            self.text(s, f"CloudDQ AI  ·  {self.n}", Inches(10.8), Inches(7.05), Inches(2.3), Inches(0.3), 10, "#7b8a94", align=PP_ALIGN.RIGHT)
        return s

    def text(self, s, txt, x, y, w, h, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
        tb = s.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        lines = txt.split("\n")
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            r = p.add_run()
            r.text = line
            r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = rgb(color); r.font.name = "Calibri"
        return tb

    def bullets(self, s, items, x, y, w, h, size=16, color=INK, gap=6):
        tb = s.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(gap)
            bold_part = None
            if isinstance(item, tuple):
                bold_part, item = item
            r0 = p.add_run(); r0.text = "▪  "; r0.font.size = Pt(size); r0.font.color.rgb = rgb(SEA)
            if bold_part:
                rb = p.add_run(); rb.text = bold_part + " — "; rb.font.bold = True
                rb.font.size = Pt(size); rb.font.color.rgb = rgb(INK); rb.font.name = "Calibri"
            r = p.add_run(); r.text = item
            r.font.size = Pt(size); r.font.color.rgb = rgb(color); r.font.name = "Calibri"
        return tb

    def card(self, s, x, y, w, h, fill="#ffffff", line=MIST):
        shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        shp.adjustments[0] = 0.06
        shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill)
        shp.line.color.rgb = rgb(line); shp.line.width = Pt(1.25)
        shp.shadow.inherit = False
        return shp

    def image(self, s, path: Path, x, y, w, h, caption: str | None = None):
        if caption:
            h = h - Inches(0.35)
        if path.exists():
            im = Image.open(path)
            iw, ih = im.size
            if ih / iw > (h / w) * 1.3:
                ih = int(iw * h / w)
                path = HERE / "build" / f"crop_{path.name}"
                path.parent.mkdir(exist_ok=True)
                im.crop((0, 0, iw, ih)).save(path)
            scale = min(w / iw, h / ih)
            dw, dh = int(iw * scale), int(ih * scale)
            dx, dy = x + (w - dw) // 2, y + (h - dh) // 2
            pic = s.shapes.add_picture(str(path), dx, dy, dw, dh)
            pic.line.color.rgb = rgb("#c9d6cf"); pic.line.width = Pt(0.75)
        else:
            shp = self.card(s, x, y, w, h, fill="#fbfdfc", line="#9fb3a9")
            shp.line.dash_style = 4
            tf = shp.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
            r = p.add_run(); r.text = "Insert console screenshot"; r.font.size = Pt(16); r.font.bold = True; r.font.color.rgb = rgb("#4b5b66")
            p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
            r2 = p2.add_run(); r2.text = f"screens/aws/{path.name}"; r2.font.size = Pt(11); r2.font.color.rgb = rgb("#7b8a94")
        if caption:
            self.text(s, caption, x, y + h + Inches(0.05), w, Inches(0.35), 11, "#4b5b66", align=PP_ALIGN.CENTER)

    def table(self, s, rows, x, y, w, col_w, size=12, header=True, row_h=Inches(0.4)):
        shape = s.shapes.add_table(len(rows), len(rows[0]), x, y, w, row_h * len(rows))
        t = shape.table
        for ci, cw in enumerate(col_w):
            t.columns[ci].width = Emu(int(w * cw))
        for ri, row in enumerate(rows):
            for ci, val in enumerate(row):
                cell = t.cell(ri, ci)
                cell.text = str(val)
                cell.margin_left = cell.margin_right = Inches(0.08)
                cell.margin_top = cell.margin_bottom = Inches(0.04)
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(size); r.font.name = "Calibri"
                        r.font.bold = header and ri == 0
                        r.font.color.rgb = rgb("#ffffff" if header and ri == 0 else INK)
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(SEA if header and ri == 0 else ("#ffffff" if ri % 2 else "#eef4f0"))
        return t

    def code(self, s, path: str, start: int, end: int, x, y, w, h, size=10.5):
        lines = (ROOT / path).read_text(encoding="utf-8").splitlines()[start - 1:end]
        box = self.card(s, x, y, w, h, fill="#13202b", line="#13202b")
        tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.TOP
        tf.margin_left = tf.margin_right = Inches(0.2); tf.margin_top = Inches(0.15)
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
        r = p.add_run(); r.text = f"{path}  (lines {start}–{end})"; r.font.size = Pt(10); r.font.color.rgb = rgb("#8fd3c1"); r.font.name = "Menlo"
        for line in lines:
            q = tf.add_paragraph(); q.alignment = PP_ALIGN.LEFT
            rr = q.add_run(); rr.text = line if line else " "
            rr.font.size = Pt(size); rr.font.name = "Menlo"; rr.font.color.rgb = rgb("#e6edf3")


def find_line(path: str, needle: str) -> int:
    for i, line in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if needle in line:
            return i
    return 1


def build_ppt() -> None:
    d = Deck()
    L, T = Inches(0.6), Inches(1.55)
    FW = Inches(12.1)

    # 1 Title
    s = d.slide()
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, d.W, Inches(4.2))
    band.fill.solid(); band.fill.fore_color.rgb = rgb(SEA); band.line.fill.background()
    d.text(s, "REVIEW PRESENTATION", L, Inches(0.8), Inches(8), Inches(0.4), 14, "#cfe7df", bold=True)
    d.text(s, C.TITLE, L, Inches(1.2), Inches(12), Inches(1.2), 54, "#ffffff", bold=True)
    d.text(s, C.SUBTITLE, L, Inches(2.4), Inches(11.5), Inches(1.2), 22, "#eaf5f1")
    d.text(s, f"Team: {C.TEAM_NAME}", L, Inches(3.5), Inches(8), Inches(0.5), 16, "#ffffff", bold=True)
    for i, m in enumerate(C.TEAM):
        x = L + i * Inches(4.1)
        d.card(s, x, Inches(4.7), Inches(3.85), Inches(1.75))
        d.text(s, m["name"], x + Inches(0.25), Inches(4.85), Inches(3.4), Inches(0.5), 20, INK, bold=True)
        d.text(s, f"Reg. No.: {m['reg']}", x + Inches(0.25), Inches(5.35), Inches(3.4), Inches(0.4), 14, SEA, bold=True)
        d.text(s, m["role"], x + Inches(0.25), Inches(5.75), Inches(3.4), Inches(0.7), 12, "#4b5b66")
    d.text(s, f"Live: {C.LIVE_URL}", L, Inches(6.75), Inches(12), Inches(0.4), 12, "#4b5b66")

    # 2 Objective
    s = d.slide("Objective", "Why CloudDQ AI")
    d.text(s, C.OBJECTIVE, L, T, Inches(6.3), Inches(3.5), 16)
    d.card(s, Inches(7.2), T, Inches(5.5), Inches(5.2))
    d.bullets(s, C.OBJECTIVE_POINTS, Inches(7.4), T + Inches(0.15), Inches(5.1), Inches(5), 13, gap=7)
    d.card(s, L, Inches(5.0), Inches(6.3), Inches(1.75), fill="#ffffff")
    d.text(s, "DQ score", L + Inches(0.2), Inches(5.1), Inches(6), Inches(0.4), 14, SEA, bold=True)
    d.text(s, "0.25·Completeness + 0.20·Validity + 0.15·Uniqueness\n+ 0.15·Consistency + 0.15·Accuracy + 0.10·Timeliness\nHealthy 80–100 · Warning 60–79 · Critical <60",
           L + Inches(0.2), Inches(5.45), Inches(6), Inches(1.3), 13)

    # 3 Module list
    s = d.slide("List of Modules", "Scope")
    for i, m in enumerate(C.MODULES):
        col, row = i % 2, i // 2
        x, y = L + col * Inches(6.15), T + row * Inches(1.32)
        d.card(s, x, y, Inches(5.95), Inches(1.18))
        d.text(s, m["id"], x + Inches(0.2), y + Inches(0.18), Inches(0.8), Inches(0.6), 22, SEA, bold=True)
        d.text(s, m["name"], x + Inches(1.0), y + Inches(0.12), Inches(4.8), Inches(0.4), 16, INK, bold=True)
        d.text(s, m["summary"], x + Inches(1.0), y + Inches(0.48), Inches(4.8), Inches(0.4), 12, "#4b5b66")
        d.text(s, m["aws"], x + Inches(1.0), y + Inches(0.8), Inches(4.8), Inches(0.3), 10.5, SEA)

    # 4-7 Module details (2 per slide)
    for i in range(0, len(C.MODULES), 2):
        s = d.slide("Detailed Description of Modules", f"Modules {C.MODULES[i]['id']}–{C.MODULES[i + 1]['id']}")
        for j, m in enumerate(C.MODULES[i:i + 2]):
            x = L + j * Inches(6.15)
            d.card(s, x, T, Inches(5.95), Inches(5.35))
            d.text(s, f"{m['id']} · {m['name']}", x + Inches(0.25), T + Inches(0.15), Inches(5.5), Inches(0.5), 18, SEA, bold=True)
            d.text(s, f"AWS: {m['aws']}", x + Inches(0.25), T + Inches(0.62), Inches(5.5), Inches(0.35), 11.5, "#4b5b66")
            d.bullets(s, m["details"], x + Inches(0.25), T + Inches(1.0), Inches(5.5), Inches(4.3), 14, gap=8)

    # Architecture
    s = d.slide("Architecture", "AWS serverless design")
    d.image(s, ARCH_PNG, L, Inches(1.4), FW, Inches(5.6))
    s = d.slide("End-to-End Workflow & Data Model", "Architecture")
    d.image(s, HERE / "flow.png", L, Inches(1.45), FW, Inches(1.9))
    d.table(s, [["Entity", "PK", "SK", "GSI1"],
                ["Dataset", "DATASET#<id>", "META", "USER#<sub> / DATASET#…"],
                ["Analysis run", "DATASET#<id>", "RUN#<iso time>", "—"],
                ["Issue", "DATASET#<id>", "ISSUE#<id>", "—"],
                ["Alert", "ALERT#<id>", "META", "USER#<sub> / ALERT#…"]],
            L, Inches(3.55), Inches(6.6), [0.2, 0.27, 0.23, 0.3], 12)
    d.card(s, Inches(7.45), Inches(3.55), Inches(5.25), Inches(3.3))
    d.text(s, "Security by design", Inches(7.65), Inches(3.65), Inches(5), Inches(0.4), 16, SEA, bold=True)
    d.bullets(s, ["Cognito JWT checked by API Gateway on every call",
                  "Roles re-checked inside Lambda (403 on wrong role)",
                  "Private encrypted S3, 15-min presigned uploads",
                  "Browser never holds AWS keys",
                  "Bedrock sees metrics JSON only, never raw rows",
                  "Separate IAM user per member, scoped policies"],
              Inches(7.65), Inches(4.1), Inches(4.9), Inches(2.7), 13, gap=4)

    # AWS services
    s = d.slide("AWS Services Used (10 + IAM)", "Cloud stack · us-east-1")
    rows = [["Service", "Use in CloudDQ AI", "Resource"]] + [[n, u, r] for n, u, r in C.AWS_SERVICES]
    d.table(s, rows, L, Inches(1.4), FW, [0.2, 0.55, 0.25], 11, row_h=Inches(0.44))

    # Individual contribution
    s = d.slide("Individual Contribution", "Team")
    for i, c in enumerate(C.CONTRIBUTIONS[:3]):
        x = L + i * Inches(4.1)
        reg = next((m["reg"] for m in C.TEAM if m["name"] == c["name"]), "")
        d.card(s, x, T, Inches(3.9), Inches(4.75))
        d.text(s, c["name"], x + Inches(0.2), T + Inches(0.12), Inches(3.5), Inches(0.45), 19, INK, bold=True)
        d.text(s, f"{reg}  ·  {c['focus']}", x + Inches(0.2), T + Inches(0.55), Inches(3.5), Inches(0.4), 11.5, SEA, bold=True)
        d.text(s, f"Modules: {c['modules']}", x + Inches(0.2), T + Inches(0.9), Inches(3.5), Inches(0.35), 11, "#4b5b66")
        d.bullets(s, c["items"], x + Inches(0.2), T + Inches(1.3), Inches(3.55), Inches(3.4), 11.5, gap=4)
    d.text(s, "Shared by all three: " + C.CONTRIBUTIONS[3]["items"][0], L, Inches(6.45), FW, Inches(0.5), 13, "#4b5b66")

    # Tools
    s = d.slide("Tools / Software Requirements", "Environment")
    d.table(s, [["Category", "Tools"]] + [list(t) for t in C.TOOLS], L, Inches(1.5), FW, [0.2, 0.8], 14, row_h=Inches(0.62))

    # AWS screenshots: 2 per slide
    shots = C.AWS_SCREENS
    for i in range(0, len(shots), 2):
        s = d.slide("Screenshots of AWS Services", "AWS console")
        for j, (k, svc, where) in enumerate(shots[i:i + 2]):
            x = L + j * Inches(6.15)
            d.text(s, svc, x, Inches(1.4), Inches(5.95), Inches(0.4), 16, SEA, bold=True)
            d.image(s, AWS_DIR / f"{k}.png", x, Inches(1.85), Inches(5.95), Inches(5.1), where)

    # Lathika's SNS walkthrough: 2 steps per slide
    walk = C.WALKTHROUGH_SNS
    for i in range(0, len(walk), 2):
        s = d.slide("Walkthrough: Lathika connects SNS", f"Steps {i + 1}–{min(i + 2, len(walk))} of {len(walk)} · LathikaShree")
        for j, (k, t, desc) in enumerate(walk[i:i + 2]):
            x = L + j * Inches(6.15)
            d.text(s, f"{i + j + 1}. {t}", x, Inches(1.4), Inches(5.95), Inches(0.4), 15, SEA, bold=True)
            d.image(s, SCREENS / "walkthrough_sns" / f"{k}.png", x, Inches(1.85), Inches(5.95), Inches(3.9))
            d.text(s, desc, x, Inches(5.85), Inches(5.95), Inches(1.1), 11.5, "#4b5b66")

    # Code highlights
    code_slides = [
        ("M4 · DQ engine — weighted score and health", "backend/src/dq_engine/dimensions.py", "def compute_dimensions", 22),
        ("M8 · Lambda entry point — routing", "backend/src/handler.py", "def lambda_handler", 34),
        ("M6 · Bedrock Converse — metrics only", "backend/src/ai/bedrock.py", "def _invoke_bedrock", 20),
        ("M3 · Presigned S3 upload URL", "backend/src/store/s3.py", "def presigned_put_url", 12),
        ("M1 · Cognito sign-in in the browser", "frontend/src/lib/cognito.ts", "export function login", 39),
    ]
    for title, path, needle, n in code_slides:
        s = d.slide(title, "Module code (complete code in report appendix)")
        start = find_line(path, needle)
        d.code(s, path, start, start + n, L, Inches(1.45), FW, Inches(5.5), size=10.5 if n <= 24 else (9 if n <= 34 else 8))

    # Feature screenshots
    for i, (k, t, desc) in enumerate(C.FEATURE_SCREENS):
        s = d.slide(t, f"Feature output {i + 1}/{len(C.FEATURE_SCREENS)}")
        d.image(s, SCREENS / f"{k}.png", L, Inches(1.4), FW, Inches(5.25))
        d.text(s, desc, L, Inches(6.7), Inches(10), Inches(0.4), 13, "#4b5b66")

    # Results + challenges
    s = d.slide("Results", "Outcome")
    d.bullets(s, C.RESULTS, L, T, Inches(6.5), Inches(5), 15, gap=10)
    d.image(s, SCREENS / "sec_dimensions.png", Inches(7.4), T, Inches(5.3), Inches(3.6))
    s = d.slide("Challenges & Future Scope", "Learning")
    d.card(s, L, T, Inches(6.0), Inches(5.3))
    d.text(s, "Challenges", L + Inches(0.2), T + Inches(0.1), Inches(5.6), Inches(0.4), 17, SEA, bold=True)
    d.bullets(s, list(C.CHALLENGES), L + Inches(0.2), T + Inches(0.55), Inches(5.6), Inches(4.7), 11.5, gap=6)
    d.card(s, Inches(6.75), T, Inches(5.95), Inches(5.3))
    d.text(s, "Future scope", Inches(6.95), T + Inches(0.1), Inches(5.6), Inches(0.4), 17, SEA, bold=True)
    d.bullets(s, C.FUTURE, Inches(6.95), T + Inches(0.55), Inches(5.55), Inches(4.7), 13, gap=8)

    # References
    s = d.slide("References", "Sources")
    d.bullets(s, C.REFERENCES, L, Inches(1.4), FW, Inches(5.6), 10.5, gap=3)

    # Thank you
    s = d.slide()
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, d.W, d.H)
    band.fill.solid(); band.fill.fore_color.rgb = rgb(SEA); band.line.fill.background()
    d.text(s, "Thank you", L, Inches(2.6), FW, Inches(1.2), 60, "#ffffff", bold=True, align=PP_ALIGN.CENTER)
    d.text(s, "Questions?   ·   " + C.LIVE_URL, L, Inches(3.9), FW, Inches(0.6), 18, "#eaf5f1", align=PP_ALIGN.CENTER)
    d.text(s, "  ·  ".join(m["name"] for m in C.TEAM), L, Inches(4.6), FW, Inches(0.5), 16, "#cfe7df", align=PP_ALIGN.CENTER)

    d.prs.save(OUT_PPT)
    print("saved", OUT_PPT, f"({d.n} slides)")


def main() -> None:
    AWS_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        render_svgs(browser)
        page = browser.new_page()
        tmp = HERE / "report.html"
        tmp.write_text(report_html(), encoding="utf-8")
        page.goto(tmp.resolve().as_uri())
        page.wait_for_timeout(1000)
        page.pdf(path=str(OUT_PDF), format="A4", print_background=True,
                 display_header_footer=True, header_template="<span></span>",
                 footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#7b8a94">'
                                 'CloudDQ AI — Project Report · <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
                 margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"})
        browser.close()
        print("saved", OUT_PDF)
    build_ppt()


if __name__ == "__main__":
    main()
