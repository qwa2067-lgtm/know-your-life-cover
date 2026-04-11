"""
extract_pds.py
--------------
Runs once. Reads each PDS using pdfplumber, sends to Claude API for structured extraction,
saves output to pds_data.json. Re-run whenever a new PDS version is released.

Usage:
    python3 extract_pds.py

Requirements:
    pip3 install pdfplumber anthropic pandas
    ANTHROPIC_API_KEY must be set as environment variable.
"""

import os
import json
import pdfplumber
import anthropic
from pathlib import Path
from datetime import date

# ── Config ─────────────────────────────────────────────────────────────────────

FOLDER = Path(__file__).parent

PDFS = {
    "TAL": {
        "file": "TAL_Accelerated_Protection_PDS_Dec2025.pdf",
        "product": "Accelerated Protection",
        "version": "December 2025",
    },
    "AIA": {
        "file": "AIA_Priority_Protection_PDS_Nov2025.pdf",
        "product": "Priority Protection",
        "version": "9 November 2025",
    },
    "Zurich": {
        "file": "Zurich_Active_PDS_Nov2025.pdf",
        "product": "Active",
        "version": "1 November 2025",
    },
}

OUTPUT_FILE = FOLDER / "pds_data.json"

# Extraction dimensions — what we ask Claude to pull from each PDS
EXTRACTION_PROMPT = """You are an expert life insurance analyst. Extract structured information from the following life insurance PDS text.

Focus ONLY on the LIFE COVER (death benefit) section. Ignore TPD, Trauma, and Income Protection.

Extract the following dimensions and return a JSON object. Be precise and quote directly from the PDS where possible. If information is not found, use null.

Return ONLY valid JSON, no other text.

{{
  "insurer": "<insurer name>",
  "product_name": "<product name>",
  "pds_version": "<version date from document>",
  "last_checked": "<today's date>",

  "life_cover": {{

    "what_triggers_payment": "<exact or near-exact quote: what event triggers the death benefit payment>",

    "terminal_illness": {{
      "definition": "<how terminal illness is defined — quote the life expectancy threshold>",
      "advance_payment": "<yes/no and any conditions — is the death benefit paid in advance on terminal illness diagnosis?>",
      "reduces_death_benefit": "<yes/no — does terminal illness advance payment reduce the remaining death benefit?>"
    }},

    "suicide_exclusion": {{
      "period": "<how many months/years is the suicide exclusion period>",
      "applies_from": "<does it apply from policy start, reinstatement, or increase date?>",
      "exact_wording": "<quote the suicide exclusion clause verbatim or near-verbatim>"
    }},

    "key_exclusions": [
      "<exclusion 1 — quote or close paraphrase>",
      "<exclusion 2>",
      "<exclusion 3>"
    ],

    "built_in_benefits": [
      {{
        "name": "<benefit name>",
        "description": "<plain English: what does this actually give the customer>",
        "any_catch": "<any condition, limit, or restriction customers might not expect — be blunt>"
      }}
    ],

    "optional_add_ons": [
      {{
        "name": "<option name>",
        "description": "<plain English description>",
        "extra_cost": "yes/no/not stated"
      }}
    ],

    "policy_expiry": {{
      "expiry_age": "<maximum age the policy can continue to>",
      "any_conditions": "<any conditions on renewal or continuation>"
    }},

    "sum_insured": {{
      "minimum": "<minimum sum insured if stated>",
      "maximum": "<maximum sum insured if stated>",
      "indexation": "<is automatic indexation built in? any opt-out option?>"
    }},

    "waiting_periods": "<any waiting periods before cover commences, other than suicide exclusion>",

    "duty_of_disclosure": "<plain English summary of what the customer must disclose and consequences of non-disclosure>",

    "reinstatement": "<conditions under which a lapsed policy can be reinstated>",

    "unique_features": [
      {{
        "feature": "<feature name>",
        "description": "<what it does — be specific>",
        "customer_angle": "<is this genuinely good for the customer, or does it look good but has catches?>"
      }}
    ],

    "potentially_tricky_clauses": [
      {{
        "clause": "<name or short description>",
        "exact_wording": "<quote from PDS>",
        "why_tricky": "<plain English: how could this disadvantage a customer who doesn't read carefully?>"
      }}
    ]
  }}
}}

PDS TEXT:
{pds_text}
"""

# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF using pdfplumber."""
    print(f"  Reading {pdf_path.name}...")
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages.append(f"[Page {i+1}]\n{text}")
    full_text = "\n\n".join(pages)
    print(f"  Extracted {len(full_text):,} characters across {len(pages)} pages.")
    return full_text


def find_life_cover_section(full_text: str) -> str:
    """
    Try to extract just the life cover section to reduce token usage.
    Falls back to full text if section boundaries can't be identified.
    """
    text_lower = full_text.lower()

    # Common section headers that signal life cover content
    start_markers = [
        "life cover",
        "death benefit",
        "life insurance benefit",
        "death cover",
        "what is life cover",
        "life benefit",
    ]
    # Common section headers that signal we've moved past life cover
    end_markers = [
        "total and permanent disability",
        "tpd cover",
        "tpd benefit",
        "trauma cover",
        "critical illness",
        "income protection",
        "income cover",
        "business expenses",
    ]

    start_pos = None
    for marker in start_markers:
        pos = text_lower.find(marker)
        if pos != -1:
            # Take a bit before the marker for context
            start_pos = max(0, pos - 200)
            break

    if start_pos is None:
        print("  Warning: Could not find life cover section — using full text.")
        return full_text

    # Find earliest end marker after start_pos
    end_pos = len(full_text)
    for marker in end_markers:
        pos = text_lower.find(marker, start_pos + 500)  # skip past our start
        if pos != -1 and pos < end_pos:
            end_pos = pos

    section = full_text[start_pos:end_pos]
    print(f"  Life cover section: {len(section):,} characters (from {start_pos:,} to {end_pos:,}).")

    # If section is too short, something went wrong — use more context
    if len(section) < 2000:
        print("  Section too short — using broader text window.")
        return full_text[start_pos:min(len(full_text), start_pos + 50000)]

    return section


def call_claude_api(insurer: str, pds_text: str) -> dict:
    """Send PDS text to Claude API and extract structured data."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = EXTRACTION_PROMPT.format(pds_text=pds_text)

    print(f"  Calling Claude API for {insurer} ({len(prompt):,} chars in prompt)...")

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    raw_response = message.content[0].text

    # Strip markdown code fences if Claude wrapped the JSON
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last lines (``` markers)
        cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        data = json.loads(cleaned)
        print(f"  Successfully parsed JSON response for {insurer}.")
        return data
    except json.JSONDecodeError as e:
        print(f"  ERROR: Could not parse JSON for {insurer}: {e}")
        print(f"  Raw response (first 500 chars): {raw_response[:500]}")
        # Return a stub so the rest of the script can continue
        return {
            "insurer": insurer,
            "error": "JSON parse failed",
            "raw_response": raw_response[:2000],
        }


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable not set.\n"
            "Run: export ANTHROPIC_API_KEY='your-key-here'"
        )

    print("=" * 60)
    print("PDS Extraction Script")
    print(f"Run date: {date.today()}")
    print("=" * 60)

    results = {}

    for insurer, config in PDFS.items():
        pdf_path = FOLDER / config["file"]
        print(f"\n[{insurer}] {config['product']} ({config['version']})")

        if not pdf_path.exists():
            print(f"  ERROR: File not found — {pdf_path}")
            results[insurer] = {"error": "PDF file not found", "insurer": insurer}
            continue

        # Step 1: Extract text
        full_text = extract_text_from_pdf(pdf_path)

        # Step 2: Narrow to life cover section (saves tokens)
        life_section = find_life_cover_section(full_text)

        # Step 3: Call Claude API
        extracted = call_claude_api(insurer, life_section)

        # Step 4: Merge in our known metadata
        extracted["_meta"] = {
            "insurer": insurer,
            "product": config["product"],
            "pds_version": config["version"],
            "pdf_file": config["file"],
            "extracted_on": str(date.today()),
            "tool": "PDSCompareTool v1",
        }

        results[insurer] = extracted

    # Save to JSON
    print(f"\nSaving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Done. Output: {OUTPUT_FILE}")

    # Quick sanity check
    print("\n--- Extraction summary ---")
    for insurer, data in results.items():
        if "error" in data:
            print(f"  {insurer}: ERROR — {data['error']}")
        elif "life_cover" in data:
            lc = data["life_cover"]
            n_exclusions = len(lc.get("key_exclusions", []))
            n_built_in = len(lc.get("built_in_benefits", []))
            n_tricky = len(lc.get("potentially_tricky_clauses", []))
            print(f"  {insurer}: OK — {n_exclusions} exclusions, {n_built_in} built-in benefits, {n_tricky} tricky clauses")
        else:
            print(f"  {insurer}: Unexpected structure — check pds_data.json")

    print("\nNext step: run app.py to view the dashboard.")


if __name__ == "__main__":
    main()
