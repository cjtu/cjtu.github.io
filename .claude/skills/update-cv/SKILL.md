---
name: update-cv
description: Use after re-exporting cv/my_publications_zotero.bib from Zotero to regenerate _data/publications.yml and rebuild cv_long.pdf and cv_onepage.pdf from the updated bibliography.
---

# update-cv

Single source of truth: `cv/my_publications_zotero.bib` (Zotero "Better BibTeX" → BibLaTeX export).

When this skill is invoked, run the steps below in order. The Python script regenerates the website data and the LaTeX `\nocite` keys; `pdflatex`+`biber` rebuild the two CV PDFs.

## Prerequisites

- `claude` conda env with `bibtexparser`, `pyyaml`, `pylatexenc` (already installed).
- System packages: `biber`, `texlive-bibtex-extra`, `texlive-latex-extra` (already installed via apt).

## Steps

1. **Confirm the bib file is current.** Tell the user:
   > "Did you re-export `cv/my_publications_zotero.bib` from Zotero before I update?"
   If they say no, stop and wait.

2. **Regenerate website data and selected-pubs cite keys.** From the repo root:
   ```bash
   source /home/cjtu/miniforge3/etc/profile.d/conda.sh && conda activate claude && python cv/scripts/update_publications.py
   ```
   The script writes `_data/publications.yml` (all articles) and `cv/selected_pubs.tex` (top 5 newest \nocite keys for the one-page CV). It prints a count and any "Missing PDFs" warnings.

3. **Surface missing-PDF warnings to the user.** If the script reports any, tell them:
   > "These papers have no PDF link. Either drop a PDF into `pdfs/` named like `<FirstAuthor>_et_al_<year>.pdf`, or attach the PDF to the Zotero entry (synced under `/mnt/c/Users/cjtai/Zotero/storage/`), then rerun."

4. **Rebuild both CV PDFs.** All artifacts go into `cv/build/`; only the PDFs are copied back.
   ```bash
   cd cv && mkdir -p build && cp --remove-destination my_publications_zotero.bib build/ && \
   pdflatex -interaction=nonstopmode -output-directory=build cv_long.tex && \
   (cd build && biber cv_long) && \
   pdflatex -interaction=nonstopmode -output-directory=build cv_long.tex && \
   pdflatex -interaction=nonstopmode -output-directory=build cv_long.tex && \
   cp build/cv_long.pdf cv_long.pdf && \
   pdflatex -interaction=nonstopmode -output-directory=build cv_onepage.tex && \
   (cd build && biber cv_onepage) && \
   pdflatex -interaction=nonstopmode -output-directory=build cv_onepage.tex && \
   pdflatex -interaction=nonstopmode -output-directory=build cv_onepage.tex && \
   cp build/cv_onepage.pdf cv_onepage.pdf
   ```
   (The `.bib` is copied into `build/` because biber resolves it relative to its working directory. Three pdflatex passes resolve biber refs and longtable column widths.)

5. **Verify.** Confirm both `cv/cv_long.pdf` and `cv/cv_onepage.pdf` were regenerated. If `pdftoppm` is available, render page 2 of `cv_long.pdf` and verify the user's name renders bold in publication entries.

6. **Report to the user.** Summarize: number of publications written, any missing PDFs, both PDFs rebuilt. Remind them to commit `_data/publications.yml`, `cv/cv_long.pdf`, `cv/cv_onepage.pdf`, `cv/selected_pubs.tex`, and any new files in `pdfs/`.

## Notes

- `_data/publications.yml` is auto-generated. Do not hand-edit; the next run clobbers manual changes.
- LaTeX build artifacts (`*.aux`, `*.bbl`, `*.bcf`, `*.blg`, etc.) are gitignored.
- Conferences, awards, and grants stay inline in the `.tex` files; only `@article` entries flow through the script.
- The author-name bolding in the CVs depends on the family-name match `Tai\bibnamedelima Udovicic`. If the user's display name changes, update `\boldfamily` in both `cv_long.tex` and `cv_onepage.tex`.
