# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Personal Navigator** — A tool that extracts "Dates, Dollars, and Duties" from Aged Care and Probate PDFs, presenting the results as a structured, accordion-style HTML widget. The core script is `engine.py` (currently saved as `engine.py.save`).

## Dependencies

Python 3 with these pip packages:
- `pdfplumber` — PDF parsing and text extraction with font metadata
- `beautifulsoup4` — HTML parsing (imported but used for potential web scraping)
- `requests` — HTTP requests

Install:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pdfplumber
```

## Running the Script

```bash
# Run against test.pdf in the same directory → produces output.html
python3 engine.py

# The script expects a PDF in the same directory as the script
```

## Architecture

The script has two main stages:

1. **`extract_pdf_content(pdf_filename)`** — Opens a PDF with `pdfplumber`, iterates pages, and classifies each word as either a header or body text based on font size. The "base" font size is determined as the most common font size on the page; any word 1.5pt larger is treated as a header. Returns a list of `{"header": str, "body": str}` dicts.

2. **`create_accordion_html(data, brand_url, original_pdf_name)`** — Takes the extracted segments and generates a self-contained HTML string with inline CSS and JavaScript. Produces a clickable accordion widget with a download button for the original PDF.

Output is written to `output.html`. The `images/` directory contains hero PNG images (likely extracted from a prior PDF run).

## Key Design Notes

- Font-size heuristic: headers are words with size > (most common size + 1.5pt). This is per-page, so each page recalculates its own base size.
- The HTML output is a self-contained embeddable widget (not a full HTML document), intended to be inserted into a CMS or webpage.
- `get_universal_path()` uses `pathlib.Path` so all file paths are relative to the script's location, working cross-platform.
