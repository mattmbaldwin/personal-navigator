import re
import pdfplumber
from pathlib import Path

PDF_PATH = Path(__file__).parent / "practice.pdf"

DOLLAR_RE = re.compile(r'\$\s*([\d,]+(?:\.\d{2})?)')
DATE_PATTERN = re.compile(
    r'\b\d{1,2}\s+'
    r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
    r'\s+\d{4}\b',
    re.IGNORECASE
)
NUMERIC_DATE_RE = re.compile(r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}\b')


def make_snippet(full_text, match, context=60):
    """Return the matched value plus up to `context` chars either side, with ellipses."""
    start = max(0, match.start() - context)
    end = min(len(full_text), match.end() + context)
    snippet = full_text[start:end].replace('\n', ' ').strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(full_text):
        snippet = snippet + "..."
    return f'"{snippet}"'


def print_table(title, headers, rows):
    col_widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0))
                  for i, h in enumerate(headers)]
    divider = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header_row = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"

    print(f"\n{title}")
    print(divider)
    print(header_row)
    print(divider)
    if rows:
        for row in rows:
            print("| " + " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers))) + " |")
    else:
        empty_msg = "No entries found"
        total_width = sum(col_widths) + 3 * (len(headers) - 1)
        print("| " + empty_msg.ljust(total_width) + " |")
    print(divider)


def find_entries(all_lines, name_label, balance_label):
    """
    Scan lines for a name_label, then look ahead up to 8 lines for
    a balance_label and extract the dollar amount on that line or the next.
    """
    entries = []
    for i, line in enumerate(all_lines):
        if name_label.lower() in line.lower():
            name = line.lower().replace(name_label.lower(), "").strip() or "(blank)"

            balance = "(blank)"
            window = all_lines[i + 1: i + 9]
            for j, lookahead in enumerate(window):
                if balance_label.lower() in lookahead.lower():
                    match = DOLLAR_RE.search(lookahead)
                    if match:
                        balance = f"${match.group(1)}"
                    elif j + 1 < len(window):
                        match = DOLLAR_RE.search(window[j + 1])
                        if match:
                            balance = f"${match.group(1)}"
                    break

            entries.append((name.title(), balance))
    return entries


# ── Extract full text per page (for snippets) and all lines (for tables) ─────
pages_text = []
all_lines = []
with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ""
        pages_text.append(text)
        all_lines.extend(text.splitlines())

# ── Dollars with citations ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("DOLLARS")
print("=" * 60)
for page_num, text in enumerate(pages_text, start=1):
    for match in DOLLAR_RE.finditer(text):
        value = f"${match.group(1)}"
        snippet = make_snippet(text, match)
        print(f"[p.{page_num}]  {value}")
        print(f"          {snippet}\n")

# ── Dates with citations ──────────────────────────────────────────────────────
print("=" * 60)
print("DATES")
print("=" * 60)
dates_found = False
for page_num, text in enumerate(pages_text, start=1):
    for pattern in (DATE_PATTERN, NUMERIC_DATE_RE):
        for match in pattern.finditer(text):
            snippet = make_snippet(text, match)
            print(f"[p.{page_num}]  {match.group()}")
            print(f"          {snippet}\n")
            dates_found = True
if not dates_found:
    print("No dates found.\n")

# ── Bank Accounts table ───────────────────────────────────────────────────────
bank_entries = find_entries(
    all_lines,
    name_label="Name of bank, building society or credit union",
    balance_label="Balance of account",
)
print_table("BANK ACCOUNTS", ["Institution", "Balance"], bank_entries)

# ── Superannuation table ──────────────────────────────────────────────────────
super_entries = find_entries(
    all_lines,
    name_label="Name of institution/fund manager",
    balance_label="Account balance",
)
print_table("SUPERANNUATION", ["Fund", "Balance"], super_entries)
