"""
app.py
------
Streamlit dashboard: Know Your Life Cover
Reads pds_data.json (produced by extract_pds.py) and displays structured comparison.

Usage:
    streamlit run app.py
"""

import json
import streamlit as st
from pathlib import Path
from datetime import date

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Know Your Life Cover",
    page_icon="🛡️",
    layout="wide",
)

FOLDER = Path(__file__).parent
DATA_FILE = FOLDER / "pds_data.json"

INSURERS = ["TAL", "AIA", "Zurich"]
INSURER_COLORS = {"TAL": "#003057", "AIA": "#E4002B", "Zurich": "#0066CC"}

# ── Know Your Rights content (hardcoded from LICOP March 2025 + other sources) ─

KNOW_YOUR_RIGHTS = {
    "claims_timeframes": {
        "title": "How long can an insurer take to decide your claim?",
        "items": [
            ("Initial response", "Insurer must acknowledge your claim within **10 business days** of receiving it (LICOP 5.13)"),
            ("Decision — straightforward claims", "Decision within **10 business days** of receiving all required information"),
            ("Decision — complex claims", "Decision within **30 business days** — and they must tell you it's complex and why"),
            ("If they need more info", "Must tell you **within 10 business days** exactly what they need"),
            ("Maximum extension", "They can request more time, but must explain why in writing"),
        ]
    },
    "if_declined": {
        "title": "If your claim is declined",
        "items": [
            ("Written reasons", "Insurer must give you written reasons for any decline — vague explanations are not acceptable"),
            ("Show Cause letter", "Before a final decline, insurer must give you a chance to respond (Show Cause). You have at least **20 business days** to reply"),
            ("Internal review", "You have the right to request an internal review — a different assessor must look at it"),
            ("AFCA", "If still unsatisfied, escalate free to the **Australian Financial Complaints Authority (AFCA)**. Binding on the insurer. Life insurance claims up to **$1 million** covered."),
        ]
    },
    "assessor_rules": {
        "title": "Rules on how your claim is assessed",
        "items": [
            ("No incentive to decline", "Claims assessors **cannot be incentivised** (via bonuses or KPIs) to decline or minimise claims (LICOP 5.46) — this is a hard rule"),
            ("Surveillance", "Insurers can investigate claims, but surveillance must be **reasonable and proportionate**. They cannot surveil your medical appointments or places of worship"),
            ("Genetic testing", "Insurers **cannot ask for genetic test results** or use them against you"),
            ("Mental health — no blanket exclusions", "Life insurers cannot apply blanket exclusions for mental health conditions — each case assessed individually"),
        ]
    },
    "cooling_off": {
        "title": "Changing your mind",
        "items": [
            ("Cooling-off period", "You have **30 days** from policy issue to cancel and get a full refund (as long as you haven't claimed)"),
            ("Cancellation", "You can cancel your policy at any time — no penalties for cancellation itself"),
        ]
    },
    "legal_protections": {
        "title": "Laws that protect you",
        "items": [
            ("Insurance Contracts Act 1984", "Insurer must act with **utmost good faith** — this cuts both ways. They cannot use technicalities to avoid paying legitimate claims"),
            ("DDO (Design & Distribution Obligations)", "Since October 2021, insurers must ensure their products are distributed to the right customers. If a product was mis-sold to you, the insurer may be liable"),
            ("LICOP (Life Insurance Code of Practice)", "Industry code — all major insurers are signatories. Sets minimum standards above the law. **Life Code Compliance Committee (Life CCC)** can publicly name and sanction breaches"),
            ("ASIC oversight", "ASIC enforces conduct obligations. You can report systemic issues at moneysmart.gov.au"),
            ("AFCA (external dispute resolution)", "Free, independent, binding on insurers. Start at afca.org.au — no cost to you"),
        ]
    },
    "pre_existing": {
        "title": "Pre-existing conditions",
        "items": [
            ("Duty to disclose", "When you apply, you must honestly answer all questions asked. You do NOT need to volunteer information not asked for (since 2021 law change for consumer insurance — but check your specific policy type)"),
            ("Non-disclosure consequences", "If you didn't disclose something material, insurer may reduce or void your claim — but they must show the non-disclosure actually affected their decision to insure you"),
            ("Standard exclusions", "Some conditions may be excluded from your cover — these should be stated clearly in your policy schedule"),
        ]
    },
}

# ── Feature-aligned benefit rows for the Side-by-Side Compare tab ─────────────
# Each entry: (category label, {insurer: benefit_name_in_json})
# None means the feature is not included for that insurer.

BENEFIT_ROWS = [
    ("Funeral / immediate advance", {
        "TAL":    "Advanced Payment Benefit",
        "AIA":    "Final Expenses",
        "Zurich": "Advancement for Funeral Expenses",
    }),
    ("Inflation protection", {
        "TAL":    "Inflation Protection Benefit",
        "AIA":    "Benefit Indexation",
        "Zurich": "Inflation Protection",
    }),
    ("Increase cover without health assessment", {
        "TAL":    "Guaranteed Future Insurability Benefit",
        "AIA":    "Guaranteed Future Insurability",
        "Zurich": "Future Insurability",
    }),
    ("Financial planning reimbursement after claim", {
        "TAL":    "Financial Planning Benefit",
        "AIA":    "Financial Planning Reimbursement",
        "Zurich": "Financial Planning Advice Reimbursement",
    }),
    ("Family accommodation support", {
        "TAL":    "Long Distance Accommodation Benefit",
        "AIA":    "Accommodation Benefit",
        "Zurich": None,
    }),
    ("Grief / counselling support", {
        "TAL":    "Grief Support Benefit",
        "AIA":    "Counselling Benefit",
        "Zurich": None,
    }),
    ("Pause premiums / cover suspension", {
        "TAL":    None,
        "AIA":    "Premium and Cover Pause Benefit",
        "Zurich": "Cover Suspension",
    }),
    ("Child death benefit", {
        "TAL":    None,
        "AIA":    "Complimentary Family Final Expenses",
        "Zurich": None,
    }),
    ("Interim accidental death cover (application period)", {
        "TAL":    None,
        "AIA":    "Complimentary Interim Accidental Death Cover",
        "Zurich": None,
    }),
    ("Claim protector (health events pool)", {
        "TAL":    None,
        "AIA":    None,
        "Zurich": "Claim Protector",
    }),
    ("Guaranteed policy upgrade", {
        "TAL":    None,
        "AIA":    None,
        "Zurich": "Guaranteed Upgrade of Benefits",
    }),
    ("Premium freeze (fix premium, benefit reduces)", {
        "TAL":    "Premium Freeze Benefit",
        "AIA":    None,
        "Zurich": None,
    }),
    ("Repatriation benefit (death overseas)", {
        "TAL":    "Repatriation Benefit",
        "AIA":    None,
        "Zurich": None,
    }),
]

# ── Flag display constants for the My Situation rule engine ───────────────────

FLAG_ICON   = {"red": "🔴", "green": "🟢", "yellow": "🟡"}
FLAG_BG     = {"red": "#fff5f5", "green": "#f0fff4", "yellow": "#fffbf0"}
FLAG_BORDER = {"red": "#e53e3e", "green": "#38a169", "yellow": "#d69e2e"}

# Shared caption style used across Overview panels
WARN_STYLE = "font-size:0.85em;color:#555;margin-top:6px;"

# ── Data loading ───────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    if not DATA_FILE.exists():
        return None
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

# ── Helpers ────────────────────────────────────────────────────────────────────

def safe_get(data: dict, *keys, default="Not stated"):
    """Safely traverse a nested dict, returning default if any key is missing."""
    val = data
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, None)
        else:
            return default
        if val is None:
            return default
    return val if val not in (None, "", [], {}) else default


def lc(data: dict, insurer: str) -> dict:
    """Return the life_cover sub-dict for an insurer."""
    return data.get(insurer, {}).get("life_cover", {})


def badge(insurer: str) -> str:
    """Return an HTML colour badge for an insurer name."""
    color = INSURER_COLORS.get(insurer, "#666")
    return (
        f'<span style="background:{color};color:white;padding:2px 10px;'
        f'border-radius:4px;font-weight:bold;">{insurer}</span>'
    )


def metric_box(color: str, value: str, unit: str, label: str) -> str:
    """Return an HTML coloured metric box with consistent height and font sizes."""
    return (
        f"<div style='text-align:center;background:{color};color:white;"
        f"border-radius:8px;padding:14px 4px;min-height:90px;"
        f"display:flex;flex-direction:column;justify-content:center;'>"
        f"<div style='font-size:1.9em;font-weight:bold;line-height:1.1;'>{value}</div>"
        f"<div style='font-size:0.82em;margin-top:2px;'>{unit}</div>"
        f"<div style='font-size:0.78em;margin-top:8px;font-weight:bold;'>{label}</div>"
        f"</div>"
    )


def benefit_lookup(data: dict, insurer: str) -> dict:
    """Return a name-keyed dict of built-in benefit records for an insurer."""
    benefits = lc(data, insurer).get("built_in_benefits", [])
    return {b["name"]: b for b in benefits if isinstance(b, dict)}


def cell_html(lookups: dict, insurer: str, benefit_name: str, bg: str) -> str:
    """Return an HTML table cell for a benefit row in the Built-in Benefits table."""
    if benefit_name is None:
        return (
            f"<td style='padding:10px 12px;vertical-align:top;background:{bg};"
            f"border-bottom:1px solid #e5e5e5;font-size:0.85em;color:#aaa;'>"
            f"Not included</td>"
        )
    b = lookups[insurer].get(benefit_name)
    if not b:
        return (
            f"<td style='padding:10px 12px;vertical-align:top;background:{bg};"
            f"border-bottom:1px solid #e5e5e5;font-size:0.85em;color:#aaa;'>"
            f"Not included</td>"
        )
    name  = b.get("name", "—")
    desc  = b.get("description", "")
    catch = b.get("any_catch", "")
    has_catch = catch and catch.lower() not in ("none", "n/a", "not stated", "")
    catch_block = (
        f"<div style='font-size:0.82em;color:#b85c00;background:#fff3e0;"
        f"border-left:3px solid #f0a500;padding:3px 7px;margin-top:5px;'>"
        f"⚠️ {catch}</div>"
    ) if has_catch else ""
    return (
        f"<td style='padding:10px 12px;vertical-align:top;background:{bg};"
        f"border-bottom:1px solid #e5e5e5;'>"
        f"<div style='font-size:0.88em;font-weight:600;margin-bottom:3px;'>{name}</div>"
        f"<div style='font-size:0.84em;color:#444;line-height:1.45;'>{desc}</div>"
        f"{catch_block}"
        f"</td>"
    )


def insurer_header_div(insurer: str) -> str:
    """Return a coloured insurer header div for use above content sections."""
    color = INSURER_COLORS.get(insurer, "#666")
    return (
        f"<div style='background:{color};color:white;padding:5px 14px;"
        f"border-radius:4px;font-weight:bold;font-size:1em;"
        f"margin-bottom:10px;display:inline-block;'>{insurer}</div>"
    )


# ── Main app ───────────────────────────────────────────────────────────────────

def main():
    st.title("🛡️ Know Your Life Cover")
    st.caption(
        "TAL Accelerated Protection · AIA Priority Protection · Zurich Active — "
        "Life cover (death benefit) only. For information purposes only — always verify with the current PDS."
    )

    data = load_data()

    if data is None:
        st.error(
            "**pds_data.json not found.**\n\n"
            "Run `python3 extract_pds.py` first to extract PDS data."
        )
        st.stop()

    # Warn if any insurer data failed to extract
    errors = [ins for ins in INSURERS if "error" in data.get(ins, {})]
    if errors:
        st.warning(f"Extraction errors for: {', '.join(errors)}. Some data may be missing.")

    # PDS version banner
    with st.expander("📋 PDS versions used in this comparison", expanded=False):
        cols = st.columns(3)
        for i, ins in enumerate(INSURERS):
            meta = data.get(ins, {}).get("_meta", {})
            with cols[i]:
                st.markdown(f"**{ins}**")
                st.markdown(f"Product: {meta.get('product', '—')}")
                st.markdown(f"PDS version: {meta.get('pds_version', '—')}")
                st.markdown(f"Extracted: {meta.get('extracted_on', '—')}")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_overview, tab_situation, tab_compare, tab_tricky, tab_rights, tab_disclaimer = st.tabs([
        "📖 Overview",
        "🙋 My Situation",
        "⚖️ Side-by-Side Compare",
        "⚠️ Watch Out For",
        "🛡️ Know Your Rights",
        "📌 Disclaimer",
    ])

    # ── TAB 1: Overview ────────────────────────────────────────────────────────
    with tab_overview:
        st.subheader("What actually differs between these three policies?")
        st.markdown(
            "All three pay a lump sum on death. The differences are in the details — "
            "and some of those details matter a lot."
        )

        st.markdown("---")
        st.markdown("### Key differences at a glance")

        diff_col1, diff_col2, diff_col3 = st.columns(3)

        with diff_col1:
            st.markdown("#### Terminal illness threshold")
            st.markdown("*How long do you have to live to qualify for early payout?*")
            st.markdown("")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(metric_box("#003057", "12", "months", "TAL"), unsafe_allow_html=True)
            with c2:
                st.markdown(metric_box("#E4002B", "24", "months", "AIA"), unsafe_allow_html=True)
            with c3:
                st.markdown(metric_box("#0066CC", "24", "months", "Zurich"), unsafe_allow_html=True)
            st.markdown(
                f"<div style='{WARN_STYLE}'>"
                "⚠️ If you're diagnosed with <strong>18 months to live</strong>, "
                "AIA and Zurich pay your full benefit now. TAL does not — "
                "you would need to wait until you have less than 12 months remaining "
                "(unless you are already on palliative care)."
                "</div>", unsafe_allow_html=True
            )

        with diff_col2:
            st.markdown("#### Funeral advance payment")
            st.markdown("*Immediate cash released while the full death claim is processed.*")
            st.markdown("")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(metric_box("#003057", "$25k", "max advance", "TAL"), unsafe_allow_html=True)
            with c2:
                st.markdown(metric_box("#E4002B", "$25k", "max advance", "AIA"), unsafe_allow_html=True)
            with c3:
                st.markdown(metric_box("#0066CC", "$15k", "max advance", "Zurich"), unsafe_allow_html=True)
            st.markdown(
                f"<div style='{WARN_STYLE}'>"
                "⚠️ Zurich advances <strong>$10,000 less</strong> than TAL and AIA at the time of death — "
                "when families most need immediate cash for funeral and estate costs. "
                "Also: TAL's advance is <strong>Accident-only in the first 3 years</strong>. "
                "If you die from illness in year 1 or 2, TAL's advance is not available."
                "</div>", unsafe_allow_html=True
            )

        with diff_col3:
            st.markdown("#### Family accommodation support")
            st.markdown("*$250/day reimbursement when family travels 100+ km to be with you.*")
            st.markdown("")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(metric_box("#003057", "14", "days max", "TAL"), unsafe_allow_html=True)
            with c2:
                st.markdown(metric_box("#E4002B", "30", "days max", "AIA"), unsafe_allow_html=True)
            with c3:
                st.markdown(metric_box("#0066CC", "✗", "not included", "Zurich"), unsafe_allow_html=True)
            st.markdown(
                f"<div style='{WARN_STYLE}'>"
                "⚠️ TAL and AIA both pay $250/day when a family member has to travel and stay near you "
                "in hospital. AIA covers more than twice as many days as TAL. "
                "Zurich <strong>does not offer this benefit at all</strong>."
                "</div>", unsafe_allow_html=True
            )

        st.markdown("---")
        st.info(
            "**Zurich Active — structural note:** "
            "Unlike TAL and AIA, Zurich combines health events (trauma) and death cover in one shared pool. "
            "Health event claims reduce the remaining death benefit sum insured. "
            "Without the optional Additional Death Cover, the death benefit payable may be less than the original sum insured. "
            "See the **Watch Out For** tab for full details."
        )

        st.markdown("---")
        st.markdown("### Policy summaries")

        for ins in INSURERS:
            ins_data = data.get(ins, {})
            life     = lc(data, ins)
            meta     = ins_data.get("_meta", {})
            color    = INSURER_COLORS[ins]

            st.markdown("---")
            st.markdown(
                f"<span style='background:{color};color:white;padding:3px 14px;"
                f"border-radius:4px;font-weight:bold;font-size:1.1em;'>{ins}</span> "
                f"<span style='font-size:1.05em;font-weight:600;'> {meta.get('product', '')}</span>",
                unsafe_allow_html=True
            )
            st.markdown("")

            col1, col2 = st.columns(2)

            with col1:
                ti     = life.get("terminal_illness", {})
                ti_def = ti.get("definition", "") if isinstance(ti, dict) else str(ti)
                threshold = (
                    "12 months" if "12 months" in ti_def
                    else "24 months" if "24 months" in ti_def
                    else "—"
                )
                st.markdown(f"**Terminal illness threshold:** {threshold}")
                st.markdown(f"**Advance payment:** {ti.get('advance_payment', '—') if isinstance(ti, dict) else '—'}")
                st.markdown("")

                sui = life.get("suicide_exclusion", {})
                st.markdown(
                    f"**Suicide exclusion:** "
                    f"{sui.get('period', '—') if isinstance(sui, dict) else str(sui)} "
                    f"from policy start / reinstatement / increase date"
                )
                st.markdown("")

                expiry = life.get("policy_expiry", {})
                st.markdown(f"**Policy expires:** {expiry.get('expiry_age', '—') if isinstance(expiry, dict) else str(expiry)}")

            with col2:
                st.markdown("**Key exclusions (beyond suicide):**")
                exclusions = life.get("key_exclusions", [])
                for ex in (exclusions[1:] if exclusions else []):
                    st.markdown(f"- {ex}")

                si = life.get("sum_insured", {})
                if isinstance(si, dict) and si.get("minimum") and si.get("minimum") != "Not stated":
                    st.markdown(f"**Min sum insured:** {si.get('minimum')}")
                if isinstance(si, dict) and si.get("maximum") and si.get("maximum") != "Not stated":
                    st.markdown(f"**Max sum insured:** {si.get('maximum')}")

    # ── TAB 2: My Situation ────────────────────────────────────────────────────
    with tab_situation:
        st.subheader("🙋 What does this mean for my situation?")
        st.markdown(
            "Answer a few questions about yourself. This tool will show you which policy terms "
            "are most relevant to your situation — so you can walk into any conversation with an "
            "adviser already knowing what to ask.\n\n"
            "_This is not financial advice. It shows you information from the PDS that is relevant "
            "to the details you provide._"
        )

        st.markdown("---")

        with st.form("situation_form"):
            st.markdown("#### About you")
            age = st.slider("Your age", min_value=18, max_value=75, value=40)

            col_q1, col_q2 = st.columns(2)
            with col_q1:
                has_dependants = st.radio(
                    "Do you have dependants who rely on your income?",
                    ["Yes", "No"], horizontal=True
                )
                has_children = st.radio(
                    "Do you have children aged 2–17?",
                    ["Yes", "No"], horizontal=True
                )
                far_from_hospital = st.radio(
                    "Do you live more than 100 km from a major city hospital?",
                    ["Yes", "No"], horizontal=True
                )
            with col_q2:
                pre_existing = st.radio(
                    "Do you have any pre-existing health conditions?",
                    ["Yes", "No", "Prefer not to say"], horizontal=False
                )
                financial_stress = st.radio(
                    "Could financial hardship ever make it difficult to keep paying premiums?",
                    ["Yes", "No"], horizontal=True
                )
                replacing_policy = st.radio(
                    "Are you replacing an existing life insurance policy?",
                    ["Yes", "No"], horizontal=True
                )

            st.markdown("#### Your cover plans")
            col_q3, col_q4 = st.columns(2)
            with col_q3:
                tpd_plan = st.radio(
                    "Are you planning to also take out TPD or trauma cover?",
                    ["Yes — linked to life cover", "Yes — as standalone", "No", "Not sure"],
                    horizontal=False
                )
            with col_q4:
                terminal_concern = st.radio(
                    "Are you concerned about terminal illness risk "
                    "(e.g. family history of cancer or other serious illness)?",
                    ["Yes", "No"], horizontal=True
                )

            submitted = st.form_submit_button("Show what's relevant to me", type="primary")

        if submitted:
            # ── Rule engine ───────────────────────────────────────────────────
            # flag types: "red" = potential disadvantage, "green" = works in your favour,
            #             "yellow" = worth checking
            flags = {"TAL": [], "AIA": [], "Zurich": []}

            def add(insurers, ftype, title, detail):
                for ins in insurers:
                    flags[ins].append((ftype, title, detail))

            # Age-based rules
            if age >= 55:
                add(["AIA"], "red",
                    "Guaranteed Future Insurability ends at age 55",
                    "You are at or past the age where AIA allows you to increase cover without "
                    "health evidence. Life events from now on (new mortgage, salary increase) "
                    "will require medical underwriting to increase your sum insured. "
                    "TAL and Zurich do not have a stated age cutoff for this feature.")

            if age >= 60:
                add(["Zurich"], "yellow",
                    "Inflation protection stops at age 64 — approaching soon",
                    "Zurich stops automatically increasing your cover at age 64. "
                    "The real value of your cover will start declining from then, "
                    "entering the years when the probability of claiming is highest. "
                    "TAL and AIA do not have a comparable age cutoff.")

            if age >= 64:
                add(["Zurich"], "red",
                    "Inflation protection has already stopped",
                    "At your age, Zurich is no longer increasing your cover each year. "
                    "The real value of your cover is already eroding relative to inflation. "
                    "TAL and AIA do not impose this cutoff.")

            if age >= 65:
                add(["Zurich"], "red",
                    "Health events cover ends at age 70 — approaching",
                    "Zurich's health events cover (heart attack, cancer, stroke and others) "
                    "ends at the policy anniversary when you turn 70. "
                    "After that, only death and terminal illness cover remains. "
                    "Given your current age, this cutoff is within the next 5 years.")

            # Terminal illness
            if terminal_concern == "Yes":
                add(["TAL"], "red",
                    "TAL's terminal illness threshold is 12 months — half of AIA and Zurich",
                    "TAL only pays the terminal illness benefit if your life expectancy is "
                    "less than 12 months (or you require palliative care). "
                    "AIA and Zurich pay at 24 months. "
                    "If you are diagnosed and given 13–23 months to live, AIA and Zurich pay "
                    "your full benefit immediately. TAL does not — you must deteriorate further first.")
                add(["AIA", "Zurich"], "green",
                    "24-month terminal illness threshold",
                    "If diagnosed with a terminal illness and given up to 24 months to live, "
                    "you can access your full sum insured now — giving you time to plan your "
                    "finances and make decisions while you are still well enough to act.")

            # Dependants + accommodation
            if has_dependants == "Yes" and far_from_hospital == "Yes":
                add(["Zurich"], "red",
                    "No family accommodation benefit",
                    "If you are hospitalised more than 100 km from home, Zurich does not "
                    "reimburse your family's travel and accommodation costs. "
                    "TAL reimburses $250/day for up to 14 days. "
                    "AIA reimburses $250/day for up to 30 days.")
                add(["TAL"], "yellow",
                    "Family accommodation covered — 14 days",
                    "TAL reimburses $250/day (up to $3,500 total) for an immediate family "
                    "member's accommodation if you are bed-confined more than 100 km from home. "
                    "This applies once the terminal illness or full benefit is paid. "
                    "AIA's equivalent benefit covers 30 days ($7,500 maximum).")
                add(["AIA"], "green",
                    "Family accommodation covered — up to 30 days",
                    "AIA reimburses $250/day for up to 30 days ($7,500 maximum) when a family "
                    "member travels and stays near you in hospital. This is the most generous "
                    "accommodation benefit of the three insurers.")

            elif has_dependants == "Yes":
                add(["Zurich"], "yellow",
                    "No family accommodation benefit",
                    "If you were ever hospitalised far from home, Zurich provides no "
                    "reimbursement for your family's travel and accommodation. TAL covers "
                    "14 days and AIA covers 30 days at $250/day.")

            # Children
            if has_children == "Yes":
                add(["AIA"], "green",
                    "Complimentary child death benefit — $20,000",
                    "AIA pays the lower of $20,000 or 10% of your sum insured if a child "
                    "aged 2–17 passes away or is diagnosed with terminal illness. "
                    "This does not reduce your own sum insured. "
                    "TAL and Zurich do not include this benefit.")
                add(["TAL", "Zurich"], "yellow",
                    "No child death benefit included",
                    "Unlike AIA, this policy does not include a built-in benefit for the "
                    "death or terminal illness of a child aged 2–17. "
                    "AIA provides up to $20,000 at no extra cost.")

            # Pre-existing conditions
            if pre_existing in ("Yes", "Prefer not to say"):
                add(["TAL", "AIA", "Zurich"], "red",
                    "Non-disclosure risk — your medical history will be checked at claim time",
                    "When you make a claim, all three insurers will review your complete "
                    "medical records — GP notes, Medicare records, pharmacy history. "
                    "If anything relates to your claim and was not disclosed at application, "
                    "they can reduce or decline the claim. This applies even when non-disclosure "
                    "was unintentional — for example, forgetting an older GP consultation or "
                    "not considering a historical symptom relevant. "
                    "Before applying, obtain a summary of your medical records from your GP "
                    "and disclose anything you are unsure about.")
                add(["TAL"], "yellow",
                    "Individual exclusions may be added to your Policy Schedule",
                    "TAL may add specific exclusions based on your health history — for example, "
                    "'no cover for cardiac events' or 'no cover for spinal conditions'. "
                    "These appear in your Policy Schedule, not the PDS. Read your Schedule "
                    "carefully when it arrives — the exclusion may cover the exact condition "
                    "you were most concerned about.")

            # TPD / linked cover
            if tpd_plan == "Yes — linked to life cover":
                add(["AIA"], "red",
                    "Linked TPD payments reduce your life cover sum insured",
                    "If your TPD cover is linked to your AIA life cover, any TPD payout "
                    "reduces the remaining life cover by the same amount. "
                    "Example: $1M life cover + $500k linked TPD. You claim TPD — $500k paid. "
                    "Your remaining life cover is now $500k, not $1M. Your family receives "
                    "less when you die. This is listed as a 'limitation', not an exclusion — "
                    "easy to miss when reading the benefits section.")
                add(["AIA"], "yellow",
                    "Consider standalone TPD instead",
                    "AIA allows TPD to be held as standalone (not linked to life cover). "
                    "Standalone TPD has its own sum insured and does not reduce the life cover "
                    "when paid. The premium is higher but the protection is independent. "
                    "Ask your adviser to quote both structures.")

            if tpd_plan in ("Yes — linked to life cover", "Not sure"):
                add(["Zurich"], "red",
                    "Health event claims erode your death benefit — no protection for death cover",
                    "Zurich Active combines health events and death cover in one shared pool. "
                    "Every health event claim (heart attack, cancer, stroke) reduces the maximum "
                    "death benefit available. The 'claim protector' only protects future health "
                    "event claims — not the death benefit. "
                    "Without the optional Additional Death Cover, your family could receive "
                    "significantly less than you intended when you die.")

            # Financial stress
            if financial_stress == "Yes":
                add(["AIA"], "green",
                    "Premium and Cover Pause Benefit — pause up to 12 months",
                    "If you experience financial hardship, AIA allows you to pause both "
                    "premiums and cover for 3, 6 or 12 months (subject to approval). "
                    "The policy does not lapse. Note: no claims can be made during the pause.")
                add(["Zurich"], "green",
                    "Cover Suspension — pause up to 12 months total",
                    "Zurich allows you to formally suspend cover for a period, stopping premiums "
                    "without the policy lapsing. Up to 12 months total over the life of the policy. "
                    "Note: no claims can be made during suspension.")
                add(["TAL"], "yellow",
                    "No formal premium pause benefit",
                    "TAL does not include a built-in premium pause option equivalent to AIA or Zurich. "
                    "If you cannot pay premiums, the policy will lapse. Contact TAL early — "
                    "they may have financial hardship arrangements available, but these are "
                    "not guaranteed as a built-in policy feature.")
                add(["TAL", "AIA", "Zurich"], "red",
                    "If your policy lapses and you reinstate, the 13-month suicide exclusion restarts",
                    "A lapse followed by reinstatement resets the 13-month exclusion period for "
                    "all three insurers. If you are experiencing mental health difficulties alongside "
                    "financial stress, this is particularly important to be aware of.")

            # Replacing existing policy
            if replacing_policy == "Yes":
                add(["TAL", "AIA", "Zurich"], "green",
                    "Suicide exclusion waiver may apply",
                    "All three insurers will waive the 13-month suicide exclusion on the "
                    "amount of cover you are replacing, provided the existing policy has been "
                    "in force for at least 13 consecutive months without lapsing. "
                    "Make sure your adviser documents this properly — the waiver must be "
                    "applied at the time the new policy is issued.")

            # Early years restriction — applies to all customers
            add(["TAL"], "yellow",
                "The $25,000 advance is Accident-only in the first 3 years",
                "TAL's Advanced Payment Benefit (the immediate $25,000 released on death) "
                "is restricted to Accidental death only for the first 3 years of the policy. "
                "If you die from illness in year 1 or 2, your family cannot access the advance "
                "while the full claim is being assessed. AIA and Zurich do not have this restriction.")

            # ── Display results ────────────────────────────────────────────────
            st.markdown("---")
            st.markdown("### What's relevant to your situation")
            st.markdown(
                "_The flags below are drawn directly from PDS terms. "
                "🔴 = a policy term that could work against you · "
                "🟢 = a feature that works in your favour · "
                "🟡 = worth asking about before you sign_"
            )
            st.markdown("")

            res_cols = st.columns(3)
            for col, ins in zip(res_cols, INSURERS):
                color = INSURER_COLORS[ins]
                with col:
                    st.markdown(
                        f"<div style='background:{color};color:white;padding:7px 14px;"
                        f"border-radius:4px;font-weight:bold;font-size:1em;"
                        f"margin-bottom:12px;'>{ins}</div>",
                        unsafe_allow_html=True
                    )
                    ins_flags = flags.get(ins, [])
                    if not ins_flags:
                        st.markdown(
                            "<div style='font-size:0.87em;color:#666;font-style:italic;'>"
                            "No specific flags for your situation based on the details provided."
                            "</div>", unsafe_allow_html=True
                        )
                    else:
                        for ftype, title, detail in ins_flags:
                            st.markdown(
                                f"<div style='background:{FLAG_BG[ftype]};"
                                f"border-left:4px solid {FLAG_BORDER[ftype]};"
                                f"padding:10px 12px;border-radius:4px;margin-bottom:10px;'>"
                                f"<div style='font-weight:600;font-size:0.88em;margin-bottom:4px;'>"
                                f"{FLAG_ICON[ftype]} {title}</div>"
                                f"<div style='font-size:0.82em;color:#444;line-height:1.5;'>"
                                f"{detail}</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )

            st.markdown("---")
            st.caption(
                "These flags are based on the PDS versions listed in the Disclaimer tab. "
                "Policy terms change — always verify with the current PDS before making any decision. "
                "This tool does not constitute financial advice."
            )

    # ── TAB 3: Side-by-Side Compare ────────────────────────────────────────────
    with tab_compare:
        st.subheader("Side-by-Side Comparison")

        compare_rows = [
            ("What triggers payment",                     lambda life: safe_get(life, "what_triggers_payment")),
            ("Terminal illness — threshold",               lambda life: safe_get(life, "terminal_illness", "definition")),
            ("Terminal illness — advance payment",         lambda life: safe_get(life, "terminal_illness", "advance_payment")),
            ("Terminal illness — reduces death benefit?",  lambda life: safe_get(life, "terminal_illness", "reduces_death_benefit")),
            ("Suicide exclusion period",                   lambda life: safe_get(life, "suicide_exclusion", "period")),
            ("Suicide exclusion — applies from",           lambda life: safe_get(life, "suicide_exclusion", "applies_from")),
            ("Waiting periods (other than suicide)",       lambda life: safe_get(life, "waiting_periods")),
            ("Policy expiry age",                          lambda life: safe_get(life, "policy_expiry", "expiry_age")),
            ("Minimum sum insured",                        lambda life: safe_get(life, "sum_insured", "minimum")),
            ("Maximum sum insured",                        lambda life: safe_get(life, "sum_insured", "maximum")),
            ("Automatic indexation",                       lambda life: safe_get(life, "sum_insured", "indexation")),
            ("Duty of disclosure",                         lambda life: safe_get(life, "duty_of_disclosure")),
            ("Reinstatement conditions",                   lambda life: safe_get(life, "reinstatement")),
        ]

        col_w_feature = "22%"

        header_cells = "".join(
            f"<th style='background:{INSURER_COLORS[ins]};color:white;padding:10px 12px;"
            f"font-weight:bold;font-size:0.95em;text-align:left;'>{ins}</th>"
            for ins in INSURERS
        )
        header_row = (
            f"<tr>"
            f"<th style='background:#f0f0f0;padding:10px 12px;font-size:0.95em;text-align:left;"
            f"width:{col_w_feature};'>Feature</th>"
            f"{header_cells}"
            f"</tr>"
        )

        data_rows_html = ""
        for i, (label, extractor) in enumerate(compare_rows):
            bg    = "#ffffff" if i % 2 == 0 else "#f9f9f9"
            cells = "".join(
                f"<td style='padding:10px 12px;vertical-align:top;font-size:0.88em;"
                f"line-height:1.5;border-bottom:1px solid #e5e5e5;'>"
                f"{extractor(lc(data, ins))}</td>"
                for ins in INSURERS
            )
            data_rows_html += (
                f"<tr style='background:{bg};'>"
                f"<td style='padding:10px 12px;vertical-align:top;font-weight:600;"
                f"font-size:0.88em;color:#333;border-bottom:1px solid #e5e5e5;"
                f"width:{col_w_feature};'>{label}</td>"
                f"{cells}"
                f"</tr>"
            )

        table_html = (
            "<div style='overflow-x:auto;'>"
            "<table style='width:100%;border-collapse:collapse;table-layout:fixed;"
            "font-family:sans-serif;'>"
            f"<thead>{header_row}</thead>"
            f"<tbody>{data_rows_html}</tbody>"
            "</table></div>"
        )
        st.markdown(table_html, unsafe_allow_html=True)

        # ── Built-in benefits ──────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("Built-in Benefits")
        st.markdown("*Included in the base premium — no extra cost. Each row shows the same feature across all three insurers.*")
        st.markdown("")

        lookups = {ins: benefit_lookup(data, ins) for ins in INSURERS}

        header_cells = "".join(
            f"<th style='background:{INSURER_COLORS[ins]};color:white;padding:10px 12px;"
            f"font-weight:bold;font-size:0.92em;text-align:left;width:27%;'>{ins}</th>"
            for ins in INSURERS
        )
        ben_header = (
            "<tr>"
            "<th style='background:#f0f0f0;padding:10px 12px;font-size:0.92em;"
            "text-align:left;width:19%;'>Feature</th>"
            f"{header_cells}"
            "</tr>"
        )

        ben_rows_html = ""
        for i, (label, insurer_map) in enumerate(BENEFIT_ROWS):
            bg = "#ffffff" if i % 2 == 0 else "#f9f9f9"
            cells = "".join(cell_html(lookups, ins, insurer_map.get(ins), bg) for ins in INSURERS)
            ben_rows_html += (
                f"<tr>"
                f"<td style='padding:10px 12px;vertical-align:top;font-weight:600;"
                f"font-size:0.86em;color:#333;border-bottom:1px solid #e5e5e5;"
                f"background:{bg};'>{label}</td>"
                f"{cells}</tr>"
            )

        ben_table = (
            "<div style='overflow-x:auto;'>"
            "<table style='width:100%;border-collapse:collapse;table-layout:fixed;"
            "font-family:sans-serif;'>"
            f"<thead>{ben_header}</thead>"
            f"<tbody>{ben_rows_html}</tbody>"
            "</table></div>"
        )
        st.markdown(ben_table, unsafe_allow_html=True)

        # ── Optional add-ons ───────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("Optional Add-ons")
        st.markdown("*Available at additional cost.*")
        st.markdown("")

        add_cols = st.columns(3)
        for col, ins in zip(add_cols, INSURERS):
            life    = lc(data, ins)
            options = life.get("optional_add_ons", [])
            color   = INSURER_COLORS[ins]
            with col:
                st.markdown(
                    f"<div style='background:{color};color:white;padding:6px 12px;"
                    f"border-radius:4px;font-weight:bold;font-size:1em;"
                    f"margin-bottom:10px;'>{ins}</div>",
                    unsafe_allow_html=True
                )
                if options and isinstance(options, list):
                    for o in options:
                        if isinstance(o, dict):
                            st.markdown(f"**{o.get('name', '—')}**")
                            st.markdown(
                                f"<div style='font-size:0.87em;color:#333;margin-bottom:10px;'>"
                                f"{o.get('description', '')}</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(f"- {o}")
                else:
                    st.markdown("*None identified.*")

    # ── TAB 4: Watch Out For ───────────────────────────────────────────────────
    with tab_tricky:
        st.subheader("⚠️ Watch Out For")
        st.markdown(
            "These are policy terms that customers may not be aware of before purchasing. "
            "All clauses described here are contained in the publicly available PDS for each product. "
            "This section is intended to help customers read those documents more informed."
        )

        st.markdown("---")
        st.markdown("### Policy terms worth understanding before you sign")
        st.markdown(
            "Not all policy terms carry equal weight at claim time. "
            "These three are the ones most likely to result in a customer's expectations "
            "not matching the policy outcome."
        )

        with st.expander("🔴  AIA — Linked benefit payments reduce your death cover sum insured", expanded=False):
            st.markdown(
                "**What customers may expect:** I bought \\$1 million life cover. My family gets \\$1 million when I die.\n\n"
                "**What the PDS says:** If your TPD or trauma cover is *linked* to your life cover "
                "(rather than standalone), any claim paid on those benefits reduces your remaining life cover "
                "sum insured by the same amount. This is stated in the AIA Priority Protection PDS under "
                "'Limitations and exclusions — Life Cover'.\n\n"
                "**Example:** \\$1M life cover + \\$500k TPD, linked. You claim TPD — "
                "\\$500k is paid. Your remaining life cover sum insured is now \\$500k, not \\$1M. "
                "When you die, your family receives \\$500k.\n\n"
                "**Why this is easy to miss:** The reduction is documented under 'limitations', not 'exclusions'. "
                "Customers reading the benefits section may not connect this to their overall death cover position.\n\n"
                "**What to ask:** Ask your adviser to structure TPD and trauma as *standalone* "
                "(not linked to life cover). Each benefit then has its own independent sum insured."
            )

        with st.expander("🔴  All three insurers — Your full medical history is assessed at claim time"):
            st.markdown(
                "**What customers may expect:** I answered the health questions honestly when I applied. I'm covered.\n\n"
                "**What the PDS says:** All three insurers state that when assessing a claim, they may obtain "
                "information including medical, Medicare, pharmaceutical benefits and private health records. "
                "If information that was material to the insurer's decision was not disclosed at application, "
                "the insurer may reduce or decline the claim, or void the policy.\n\n"
                "**Why customers may be affected:** Many declined claims on this basis do not involve "
                "deliberate non-disclosure. The customer may have forgotten an older GP consultation, "
                "or did not consider a historical symptom relevant. The legal standard is whether "
                "a reasonable person in their position would have known to disclose it.\n\n"
                "**What all three PDSs say:** If the duty to take reasonable care not to make a misrepresentation "
                "is breached, the insurer may void the policy, change the terms, "
                "or reduce the benefit paid.\n\n"
                "**What to do:** Before completing your application, consider obtaining a summary of your "
                "medical records from your GP. Disclose anything you are unsure about. Read the completed "
                "form yourself before signing."
            )

        with st.expander("🟠  TAL — Individual exclusions are added to your Policy Schedule, not the PDS"):
            st.markdown(
                "**What customers may expect:** I read the PDS. I know what is and isn't covered.\n\n"
                "**What the PDS says:** TAL (and all three insurers) can add individual exclusions "
                "to your Policy Schedule at underwriting, based on your health history. "
                "These exclusions are specific to you and are not in the PDS — they are in the "
                "Policy Schedule issued to you after your application is approved.\n\n"
                "**Why this matters:** The Policy Schedule is issued after approval, "
                "sometimes weeks later. The exclusion may apply to the specific condition "
                "the customer was most concerned about when they applied.\n\n"
                "**What to do:** Read your Policy Schedule in full when it arrives. "
                "If you have an exclusion you wish to query, contact the insurer — "
                "particularly if you have since recovered from the condition or can provide "
                "supporting medical evidence."
            )

        st.markdown("---")
        st.markdown("### Policy terms by insurer")

        any_tricky = False
        for ins in INSURERS:
            life   = lc(data, ins)
            tricky = life.get("potentially_tricky_clauses", [])
            if tricky and isinstance(tricky, list):
                any_tricky = True
                st.markdown("---")
                st.markdown(f"### {ins}")
                for item in tricky:
                    if isinstance(item, dict):
                        clause_label = item.get("clause", "Clause").replace("$", "\\$")
                        with st.expander(f"⚠️ {clause_label}"):
                            if item.get("exact_wording"):
                                st.markdown("**PDS wording:**")
                                st.markdown(
                                    f"<div style='font-size:0.88em;color:#444;line-height:1.6;"
                                    f"background:#f7f7f7;padding:10px 14px;border-radius:4px;"
                                    f"margin-bottom:8px;'>{item['exact_wording']}</div>",
                                    unsafe_allow_html=True
                                )
                            st.markdown("**Why this matters:**")
                            st.markdown(
                                f"<div style='font-size:0.88em;color:#444;line-height:1.6;'>"
                                f"{item.get('why_tricky', '—')}</div>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(f"- {item}")

        if not any_tricky:
            st.info(
                "No potentially tricky clauses were identified in this extraction. "
                "This may mean the PDSs are genuinely straightforward, or it may mean the relevant sections "
                "weren't captured. Always read the full PDS."
            )

        st.markdown("---")
        st.subheader("Unique Features — What Does Each Insurer Offer That Others Don't?")

        for ins in INSURERS:
            life   = lc(data, ins)
            unique = life.get("unique_features", [])
            color  = INSURER_COLORS[ins]
            st.markdown(insurer_header_div(ins), unsafe_allow_html=True)
            if unique and isinstance(unique, list):
                for u in unique:
                    if isinstance(u, dict):
                        feature = u.get("feature", "—")
                        description = u.get("description", "")
                        angle = u.get("customer_angle", "")
                        angle_html = (
                            f"<div style='color:#666;margin-top:4px;font-style:italic;'>{angle}</div>"
                            if angle else ""
                        )
                        st.markdown(
                            f"<div style='padding:8px 12px;border-left:3px solid {color};"
                            f"margin-bottom:8px;'>"
                            f"<div style='font-weight:600;margin-bottom:3px;'>{feature}</div>"
                            f"<div style='color:#333;line-height:1.5;'>{description}</div>"
                            f"{angle_html}"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(f"- {u}")
            else:
                st.markdown("*No unique features identified.*")
            st.markdown("")

    # ── TAB 5: Know Your Rights ────────────────────────────────────────────────
    with tab_rights:
        st.subheader("🛡️ Know Your Rights")
        st.markdown(
            "This section is not about any single insurer. It's about the **protections that exist for you "
            "under Australian law and industry codes — regardless of which insurer you choose.**"
        )
        st.caption(
            "Sources: Life Insurance Code of Practice (March 2025, Version 2), "
            "Insurance Contracts Act 1984, ASIC DDO obligations, AFCA."
        )

        for _, section in KNOW_YOUR_RIGHTS.items():
            st.markdown("---")
            st.markdown(f"### {section['title']}")
            for label, content in section["items"]:
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown(f"**{label}**")
                with col2:
                    st.markdown(content)

        st.markdown("---")
        st.markdown("### Where to go if things go wrong")
        st.markdown("""
| Step | Who | What they do |
|------|-----|-------------|
| 1 | **Your insurer's IDR team** | Internal Dispute Resolution — free, must respond within set timeframes |
| 2 | **AFCA** | afca.org.au — free, independent, binding on insurer. Up to $1M for life claims |
| 3 | **ASIC** | moneysmart.gov.au — report systemic conduct issues |
| 4 | **Life CCC** | lifeccc.org.au — report LICOP breaches; can publicly sanction insurers |
| 5 | **Legal advice** | Law firm specialising in insurance disputes, or Legal Aid |
""")

    # ── TAB 6: Disclaimer ──────────────────────────────────────────────────────
    with tab_disclaimer:
        st.subheader("📌 Important Disclaimer")

        st.error(
            "**This tool is for information and educational purposes only. "
            "It is not financial advice, legal advice, or a substitute for reading the full PDS.**"
        )

        pds_table_rows = "\n".join(
            f"| {ins} | {data.get(ins, {}).get('_meta', {}).get('product', '—')} | "
            f"{data.get(ins, {}).get('_meta', {}).get('pds_version', '—')} | "
            f"{data.get(ins, {}).get('_meta', {}).get('extracted_on', '—')} |"
            for ins in INSURERS
        )
        st.markdown(
            "### PDS versions used\n\n"
            "| Insurer | Product | PDS Version | Extracted |\n"
            "|---------|---------|-------------|-----------|\n"
            + pds_table_rows
        )

        st.markdown("""
### What this tool does and does not do

**Does:**
- Summarises key life cover features from publicly available PDS documents
- Highlights clauses that customers might find surprising
- Explains rights under LICOP, Australian law, and AFCA

**Does not:**
- Provide personalised financial advice
- Replace reading the full PDS
- Account for changes after the PDS dates shown above
- Cover TPD, Trauma, or Income Protection (life cover only in this version)
- Include pricing or premium comparison

### Data accuracy and interpretation

The structured data in this tool was extracted from the PDS documents listed above and reflects the author's interpretation of those documents at the time of extraction.

Two limitations apply:

1. **PDS versions change.** Insurers periodically release updated PDS documents. Information in this tool may not reflect the current version of a product. Always download the current PDS directly from the insurer's website before making any decision.

2. **Interpretation may not be perfect.** Life insurance policy wording is complex. While every effort has been made to represent each clause accurately, some nuance may have been lost in summarisation. Do not rely on this tool as a definitive legal or contractual interpretation. If a clause is material to your situation, read the original wording in the PDS.

This tool is a working prototype built to demonstrate the application of insurance domain expertise to a customer transparency problem. It has not been independently audited or reviewed by the insurers named.

### Always verify

Before purchasing any policy:
1. Download the current PDS directly from the insurer's website
2. Read the sections relevant to your situation
3. Consider speaking with a licensed financial adviser

### About this tool

**Know Your Life Cover** is built by Amy Wang — actuary and life insurance professional — as a demonstration of applying domain expertise to build consumer transparency tools. Not affiliated with TAL, AIA, or Zurich.
""")

        st.markdown(f"*Page last refreshed: {date.today()}*")


if __name__ == "__main__":
    main()
