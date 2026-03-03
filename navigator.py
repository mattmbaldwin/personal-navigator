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

DUTY_RE = re.compile(
    r'(?<![a-z])'                         # not mid-word
    r'('
    r'you must\b'
    r'|you will need to\b'
    r'|you are required to\b'
    r'|must be (signed|completed|provided|submitted)\b'
    r'|provide evidence\b'
    r'|provide a (copy|document|statement)\b'
    r'|failure to\b'
    r'|you should (tell|notify|contact)\b'
    r')',
    re.IGNORECASE
)


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


def extract_sentence(text, match, max_len=200):
    """
    Walk backwards to the nearest sentence boundary before the match,
    and forwards to the nearest boundary after — giving a clean, readable duty.
    """
    boundaries = r'[.!?\n]'
    before = text[:match.start()]
    after = text[match.end():]

    start_boundary = max(
        (m.end() for m in re.finditer(boundaries, before)),
        default=max(0, match.start() - max_len)
    )
    end_boundary_match = re.search(boundaries, after)
    end_boundary = match.end() + (end_boundary_match.start() + 1 if end_boundary_match else max_len)
    end_boundary = min(end_boundary, match.start() + max_len)

    sentence = text[start_boundary:end_boundary].replace('\n', ' ').strip()
    return f'"{sentence}"'


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

# ── Duties with citations ─────────────────────────────────────────────────────
print("=" * 60)
print("DUTIES")
print("=" * 60)
seen_duties = set()
duties_found = False
for page_num, text in enumerate(pages_text, start=1):
    for match in DUTY_RE.finditer(text):
        sentence = extract_sentence(text, match)
        if sentence not in seen_duties:
            seen_duties.add(sentence)
            print(f"[p.{page_num}]  {sentence}\n")
            duties_found = True
if not duties_found:
    print("No duties found.\n")

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
