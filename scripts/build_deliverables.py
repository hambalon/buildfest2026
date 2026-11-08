"""Build the BuildFest submission files with the required names.

Usage (from the repo root):
    pip install -r requirements-dev.txt          # once: markdown + pypdf
    python scripts/build_deliverables.py --team 12
    python scripts/build_deliverables.py --team 12 --forbid "Firstname Lastname,Other Name"

Writes to submission/ (gitignored):
    Team12_Memo.pdf                 from docs/memo.md         (must be 1-2 pages)
    Team12_AIAppendix.pdf           from docs/ai_appendix.md  (must be 1 page)
    Team12_TechnicalArtifact.zip    every repo file except data, outputs, .git, .venv

Only the part of each .md file after the line `<!-- BEGIN DELIVERABLE -->` is
printed (drafting notes above it stay out). "Team #" / "Team#" become "Team 12".

Safety checks (the build fails if any is violated):
  - page limits; leftover placeholders ("TODO", "___", "[[ ]]");
  - any --forbid name or any e-mail address in the PDFs' text or the zip's files;
  - any data file (.xlsx/.csv/...) in the zip.
PDFs are printed with Google Chrome / Chromium in headless mode.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "submission"
MARK = "<!-- BEGIN DELIVERABLE -->"
DATA_EXT = {".xlsx", ".xls", ".csv", ".parquet", ".pkl", ".sav", ".dta"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
ALLOWED_EMAILS = {"noreply@anthropic.com"}  # AI co-author line in commit docs, not a person

CSS = """
@page { size: Letter; margin: 0.5in 0.6in; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.6pt;
       line-height: 1.36; color: #1b1b1a; margin: 0; }
h1 { font-size: 15pt; margin: 0 0 2pt; color: #0d366b; letter-spacing: -0.2pt; }
h2 { font-size: 10.6pt; margin: 8pt 0 3pt; color: #0d366b; border-bottom: 1px solid #cde2fb;
     padding-bottom: 1pt; }
h3 { font-size: 9.8pt; margin: 6pt 0 2pt; }
p { margin: 0 0 4pt; }
ul, ol { margin: 0 0 4pt; padding-left: 15pt; }
li { margin: 0 0 1.6pt; }
table { border-collapse: collapse; width: 100%; margin: 2pt 0 5pt; font-size: 8.6pt; }
th, td { border-bottom: 1px solid #e3e2dd; padding: 2pt 4pt; text-align: left; vertical-align: top; }
th { background: #f3f6fb; font-weight: 600; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.4pt; background: #f3f3f1; padding: 0 2pt; }
blockquote { margin: 3pt 0 5pt; padding: 3pt 7pt; border-left: 3px solid #2a78d6; background: #f3f6fb; }
.meta { color: #52514e; font-size: 8.8pt; margin-bottom: 5pt; }
.fig { display: grid; grid-template-columns: 1fr 1fr; gap: 10pt; margin: 4pt 0 6pt; }
.fig h4 { font-size: 8.6pt; margin: 0 0 3pt; color: #1b1b1a; }
.bar { display: grid; grid-template-columns: 112pt 1fr 30pt; align-items: center; gap: 4pt;
       font-size: 8pt; margin: 1.5pt 0; }
.track { background: #f0efec; height: 8pt; border-radius: 2pt; position: relative; }
.fill { height: 8pt; border-radius: 2pt; }
.note { color: #52514e; font-size: 7.8pt; margin-top: 2pt; }
"""


def find_chrome() -> str:
    candidates = [
        os.environ.get("CHROME", ""),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        shutil.which("google-chrome") or "", shutil.which("chromium") or "", shutil.which("chromium-browser") or "",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    sys.exit("Chrome/Chromium/Edge not found. Set CHROME=/path/to/chrome and retry.")


def md_to_html(md_path: Path, team: str, title: str) -> str:
    import markdown

    text = md_path.read_text(encoding="utf-8")
    if MARK not in text:
        sys.exit(f"{md_path} has no '{MARK}' line.")
    body = text.split(MARK, 1)[1]
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    body = re.sub(r"Team ?#", f"Team {team}", body)
    html_body = markdown.markdown(body, extensions=["tables", "sane_lists", "attr_list", "md_in_html"])
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
            f"<style>{CSS}</style></head><body>{html_body}</body></html>")


def print_pdf(chrome: str, html_text: str, out: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "doc.html"
        src.write_text(html_text, encoding="utf-8")
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
               "--print-to-pdf-no-header", f"--print-to-pdf={out}", src.as_uri()]
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)


def pdf_info(path: Path) -> tuple[int, str]:
    from pypdf import PdfReader

    r = PdfReader(str(path))
    return len(r.pages), "\n".join(p.extract_text() or "" for p in r.pages)


def scan(text: str, where: str, forbid: list[str]) -> list[str]:
    problems = []
    for name in forbid:
        if name and re.search(re.escape(name), text, re.IGNORECASE):
            problems.append(f"{where}: contains forbidden name '{name}'")
    for e in set(EMAIL.findall(text)) - ALLOWED_EMAILS:
        if e.lower().endswith(("example.com", "example.org")):  # reserved placeholder domains
            continue
        problems.append(f"{where}: contains an e-mail address ({e})")
    return problems


def artifact_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.split("\n")
    files = []
    for f in filter(None, out):
        p = ROOT / f
        if not p.is_file() or f.startswith(("submission/", "data/", "outputs/")):
            continue
        files.append(p)
    # placeholders that keep the folders
    files += [ROOT / "data" / "README.md", ROOT / "outputs" / ".gitkeep"]
    return sorted(set(f for f in files if f.exists()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--team", required=True, help="Your assigned team number, e.g. 12")
    ap.add_argument("--forbid", default="", help="Comma-separated names that must not appear anywhere")
    ap.add_argument("--skip-zip", action="store_true")
    a = ap.parse_args()
    team = a.team.strip()
    forbid = [n.strip() for n in a.forbid.split(",") if n.strip()]
    OUT.mkdir(exist_ok=True)
    chrome = find_chrome()
    problems: list[str] = []

    docs = [("Memo", ROOT / "docs" / "memo.md", 2), ("AIAppendix", ROOT / "docs" / "ai_appendix.md", 1)]
    for kind, src, max_pages in docs:
        out = OUT / f"Team{team}_{kind}.pdf"
        print_pdf(chrome, md_to_html(src, team, f"Team {team} {kind}"), out)
        pages, text = pdf_info(out)
        status = "OK" if pages <= max_pages else f"TOO LONG (limit {max_pages})"
        print(f"{out.name}: {pages} page(s) {status}")
        if pages > max_pages:
            problems.append(f"{out.name} has {pages} pages; the limit is {max_pages}")
        for ph in ("TODO", "___", "[[", "]]", "Team #", "Team#"):
            if ph in text:
                problems.append(f"{out.name}: placeholder '{ph}' still in the text")
        problems += scan(text, out.name, forbid)

    if not a.skip_zip:
        zpath = OUT / f"Team{team}_TechnicalArtifact.zip"
        files = artifact_files()
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                rel = f.relative_to(ROOT)
                if f.suffix.lower() in DATA_EXT:
                    problems.append(f"zip: refusing data file {rel}")
                    continue
                if f.suffix.lower() in {".py", ".md", ".txt", ".toml", ".bat", ".command", ".cfg", ""}:
                    problems += scan(f.read_text(encoding="utf-8", errors="ignore"), f"zip:{rel}", forbid)
                z.write(f, Path(f"Team{team}_TechnicalArtifact") / rel)
        print(f"{zpath.name}: {len(files)} files, {zpath.stat().st_size / 1024:.0f} KB (no data, no outputs)")

    if problems:
        print("\nPROBLEMS (fix before submitting):")
        for p in problems:
            print("  -", p)
        return 1
    print(f"\nAll checks passed. Files are in {OUT}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
