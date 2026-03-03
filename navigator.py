import re
import pdfplumber
from pathlib import Path

PDF_PATH = Path(__file__).parent / "practice.pdf"

DOLLAR_RE = re.compile(r'\$\s*([\d,]+(?:\.\d{2})?)')


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
            # Everything after the label on the same line is the institution name
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


# ── Extract all text lines across the whole PDF ──────────────────────────────
all_lines = []
with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            all_lines.extend(text.splitlines())

# ── Bank Accounts ─────────────────────────────────────────────────────────────
bank_entries = find_entries(
    all_lines,
    name_label="Name of bank, building society or credit union",
    balance_label="Balance of account",
)
print_table(
    "BANK ACCOUNTS",
    ["Institution", "Balance"],
    bank_entries,
)

# ── Superannuation ────────────────────────────────────────────────────────────
super_entries = find_entries(
    all_lines,
    name_label="Name of institution/fund manager",
    balance_label="Account balance",
)
print_table(
    "SUPERANNUATION",
    ["Fund", "Balance"],
    super_entries,
)
