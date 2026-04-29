#!/usr/bin/env python
"""Regenerate _data/publications.yml from cv/my_publications_zotero.bib.

Single source of truth for the website's publications section. Articles only.
PDFs are resolved in this order: existing pdfs/<FirstAuthor>_et_al_<year>*.pdf,
then a copy from the Zotero `file` field via the /mnt/c WSL mount, then a
warning printed at the end.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import bibtexparser
import yaml

ROOT = Path(__file__).resolve().parents[2]
BIB_PATH = ROOT / "cv" / "my_publications_zotero.bib"
PDF_DIR = ROOT / "pdfs"
OUT_PATH = ROOT / "_data" / "publications.yml"
SELECTED_TEX_PATH = ROOT / "cv" / "selected_pubs.tex"
SELECTED_COUNT = 5
HIGHLIGHT_FAMILY = "Tai Udovicic"
WIN_PATH_RE = re.compile(r"^([A-Za-z]):[\\/]")

LATEX_REPLACEMENTS = [
    (r"\\&", "&"),
    (r"\\%", "%"),
    (r"\\_", "_"),
    (r"\\#", "#"),
    (r"--", "\u2013"),
    (r"\\textendash\b", "\u2013"),
    (r"\\textemdash\b", "\u2014"),
]


def strip_braces(text: str) -> str:
    if not text:
        return text
    prev = None
    while text != prev:
        prev = text
        text = re.sub(r"\{\{([^{}]*)\}\}", r"\1", text)
        text = re.sub(r"\{([^{}]*)\}", r"\1", text)
    return text


def clean_text(text: str) -> str:
    text = strip_braces(text or "")
    for pattern, repl in LATEX_REPLACEMENTS:
        text = re.sub(pattern, repl, text)
    return re.sub(r"\s+", " ", text).strip()


def parse_authors(raw: str) -> list[tuple[str, str]]:
    """Split 'A and B and C' into [(family, given), ...]."""
    out: list[tuple[str, str]] = []
    for part in re.split(r"\s+and\s+", raw or ""):
        part = part.strip()
        if not part:
            continue
        if "," in part:
            family, given = (s.strip() for s in part.split(",", 1))
        else:
            tokens = part.split()
            family = tokens[-1] if tokens else part
            given = " ".join(tokens[:-1])
        out.append((clean_text(family), clean_text(given)))
    return out


def fmt_author(family: str, given: str, *, bold: bool) -> str:
    s = f"{family}, {given}" if given else family
    return f"<b>{s}</b>" if bold else s


def format_author_list(authors: list[tuple[str, str]]) -> str:
    """Bold the user; <=5 authors list all, otherwise abbreviate with et al."""
    is_user = [fam == HIGHLIGHT_FAMILY for fam, _ in authors]
    user_idx = is_user.index(True) if any(is_user) else -1

    if len(authors) <= 5:
        return ", ".join(
            fmt_author(fam, giv, bold=is_user[i])
            for i, (fam, giv) in enumerate(authors)
        )

    first = fmt_author(authors[0][0], authors[0][1], bold=is_user[0])
    if user_idx <= 0:
        if user_idx == 0:
            second = fmt_author(authors[1][0], authors[1][1], bold=False)
            return f"{first}, {second}, et al."
        return f"{first}, et al."
    user = fmt_author(authors[user_idx][0], authors[user_idx][1], bold=True)
    return f"{first}, et al. including {user}"


def parse_year(date: str) -> str:
    m = re.match(r"(\d{4})", date or "")
    return m.group(1) if m else (date or "")


def parse_volume(entry: dict) -> str | None:
    v = (entry.get("volume") or "").strip()
    n = (entry.get("number") or "").strip()
    if v and n:
        return f"{v}({n})"
    return v or None


def normalize_doi(doi: str) -> str | None:
    doi = (doi or "").strip()
    if not doi:
        return None
    return doi if doi.startswith("http") else f"https://doi.org/{doi}"


def canonical_pdf_stem(authors: list[tuple[str, str]], year: str) -> str:
    if not authors:
        return ""
    first_family = authors[0][0].replace(" ", "_")
    suffix = "_et_al" if len(authors) > 1 else ""
    return f"{first_family}{suffix}_{year}"


def windows_to_wsl(path: str) -> Path | None:
    """Translate a Zotero BibTeX file path to a WSL-mounted path."""
    if not path:
        return None
    p = path.strip().replace(r"\:", ":").replace("\\\\", "\\")
    m = WIN_PATH_RE.match(p)
    if not m:
        return None
    rest = p[m.end():].replace("\\", "/")
    return Path(f"/mnt/{m.group(1).lower()}/{rest}")


def resolve_pdf(
    entry: dict,
    authors: list[tuple[str, str]],
    year: str,
    citekey: str,
) -> tuple[str | None, str | None]:
    stem = canonical_pdf_stem(authors, year)
    if not stem:
        return None, None

    matches = sorted(PDF_DIR.glob(f"{stem}*.pdf"))
    if matches:
        return f"pdfs/{matches[0].name}", None

    for src_str in (entry.get("file") or "").split(";"):
        src_str = src_str.strip()
        if not src_str.lower().endswith(".pdf"):
            continue
        wsl = windows_to_wsl(src_str)
        if wsl and wsl.exists():
            target = PDF_DIR / f"{stem}.pdf"
            if target.exists():
                target = PDF_DIR / f"{stem}_{citekey}.pdf"
            shutil.copy2(wsl, target)
            return f"pdfs/{target.name}", f"Copied {wsl} -> pdfs/{target.name}"

    return None, (
        f"No PDF found for {citekey} (looked for pdfs/{stem}*.pdf"
        " and Zotero file field)"
    )


def main() -> int:
    if not BIB_PATH.exists():
        print(f"ERROR: {BIB_PATH} not found", file=sys.stderr)
        return 1
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    with BIB_PATH.open(encoding="utf-8") as fh:
        db = bibtexparser.load(fh)

    articles = [e for e in db.entries if e.get("ENTRYTYPE", "").lower() == "article"]
    articles.sort(key=lambda e: e.get("date", ""), reverse=True)

    records: list[dict] = []
    warnings: list[str] = []
    notes: list[str] = []

    for entry in articles:
        authors = parse_authors(entry.get("author", ""))
        year = parse_year(entry.get("date", ""))
        rec: dict = {
            "title": clean_text(entry.get("title", "")),
            "authors": format_author_list(authors),
            "journal": clean_text(
                entry.get("journaltitle") or entry.get("journal") or ""
            ),
        }
        vol = parse_volume(entry)
        if vol:
            rec["volume"] = vol
        rec["year"] = int(year) if year.isdigit() else year
        if entry.get("pages"):
            rec["pages"] = clean_text(entry["pages"])
        doi = normalize_doi(entry.get("doi", ""))
        if doi:
            rec["doi"] = doi
        pdf, msg = resolve_pdf(entry, authors, year, entry.get("ID", ""))
        if pdf:
            rec["pdf"] = pdf
            if msg and msg.startswith("Copied"):
                notes.append(msg)
        elif msg:
            warnings.append(msg)
        records.append(rec)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        fh.write("# AUTO-GENERATED by cv/scripts/update_publications.py\n")
        fh.write("# Source of truth: cv/my_publications_zotero.bib (Zotero export).\n")
        fh.write("# Do not edit by hand; changes will be overwritten on next run.\n")
        yaml.safe_dump(
            records,
            fh,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=1000,
        )

    selected_keys = [e["ID"] for e in articles[:SELECTED_COUNT] if e.get("ID")]
    SELECTED_TEX_PATH.write_text(
        "% AUTO-GENERATED by cv/scripts/update_publications.py - do not edit.\n"
        "% Top {n} most recent articles for cv_onepage.tex.\n"
        "\\nocite{{{keys}}}\n".format(n=len(selected_keys), keys=",".join(selected_keys)),
        encoding="utf-8",
    )

    print(f"Wrote {len(records)} publications to {OUT_PATH.relative_to(ROOT)}")
    print(
        f"Wrote selected ({len(selected_keys)}) cite keys to "
        f"{SELECTED_TEX_PATH.relative_to(ROOT)}"
    )
    for n in notes:
        print(f"  + {n}")
    if warnings:
        print("\nMissing PDFs:")
        for w in warnings:
            print(f"  - {w}")
        print(
            "\nDrop missing PDFs into pdfs/ (named like "
            "<FirstAuthor>_et_al_<year>.pdf) or attach them in Zotero "
            "and rerun the update."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
