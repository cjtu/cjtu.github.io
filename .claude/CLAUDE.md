# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal CV/resume site for Christian J. Tai Udovicic, built with Jekyll and served by GitHub Pages at https://cjtu.github.io/. Based on Joel Glovier's resume template.

## Commands

```sh
bundle install                       # install gems
bundle exec jekyll serve --no-watch  # build + serve locally (default: http://127.0.0.1:4000)
bundle exec jekyll build             # one-shot build into _site/
```

There is no test suite, linter, or CI in this repo — GitHub Pages handles the production build automatically on push to `master`.

After editing `_config.yml`, restart the Jekyll server; config changes are not picked up by live regeneration.

## Architecture

The site is **content-driven via YAML data files**, not hand-written HTML. To add or update CV entries, edit the relevant file in `_data/` rather than touching layouts.

- `index.html` — trivial entry point; just declares `layout: resume`.
- `_layouts/resume.html` — the only layout. Iterates over `site.data.*` collections (education, publications, experience, projects, presentations, outreach, recognitions, etc.) and renders each section. Each section is gated by a `resume_section_*` flag in `_config.yml` — toggle visibility there, don't delete layout blocks.
- `_data/*.yml` — one file per CV section. Schema is defined implicitly by how `resume.html` consumes each entry (e.g. `publications.yml` entries use `title`, `authors`, `journal`, `volume`, `year`, `pages`, `doi`, `pdf`). Match existing entries when adding new ones.
- `_config.yml` — site metadata, contact info, intro blurb, and section toggles. The `resume_header_intro` is HTML.
- `_includes/` — `head.html`, `icon-links.html`, social links, icons partial.
- `_sass/` — SCSS partials compiled via Jekyll's built-in SCSS (`sass.style: compressed` in `_config.yml`). Output goes to `css/`.
- `pdfs/` — published paper PDFs referenced by `pdf:` fields in `_data/publications.yml` (paths are relative to site root, e.g. `pdfs/Foo_2025.pdf`).
- `images/` — avatar and other static images.
- `CNAME` — present (empty) for GitHub Pages custom domain support.

## Publications workflow

`cv/my_publications_zotero.bib` (Zotero "Better BibTeX" → BibLaTeX export) is the **single source of truth** for publications on the website and in the CVs. To refresh:

1. Re-export the bibliography from Zotero, overwriting `cv/my_publications_zotero.bib`.
2. Run the `update-cv` skill (or directly: `python cv/scripts/update_publications.py` from the `claude` conda env, then rebuild both PDFs in `cv/` via `pdflatex` + `biber` + two more `pdflatex` passes).
3. Resolve any "Missing PDFs" warnings: drop the PDF into `pdfs/` named `<FirstAuthor>_et_al_<year>.pdf`, or attach it in Zotero (synced under `/mnt/c/Users/cjtai/Zotero/storage/`), then rerun.
4. Commit `_data/publications.yml`, `cv/cv_long.pdf`, `cv/cv_onepage.pdf`, `cv/selected_pubs.tex`, and any new files in `pdfs/`.

`_data/publications.yml` and `cv/selected_pubs.tex` are auto-generated — do not hand-edit. Conferences, awards, grants, and other non-article entries stay inline in the `.tex` files. LaTeX build artifacts land in `cv/build/` (gitignored); the resulting `.pdf` files in `cv/` are tracked.

## Notes

- Gems are pinned via `Gemfile` to `github-pages` so local builds match the GitHub Pages production environment — don't add gems outside what `github-pages` supports.
