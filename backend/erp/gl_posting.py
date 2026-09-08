"""Demo GL helpers: journal entries, trial balance, invoice/payment auto-post.

In-memory only (ERP-Demo sandbox). Idempotent via source + source_id.
"""

from __future__ import annotations

from datetime import date
from typing import Any

# Slim COA codes from seeds/master.py
ACCT_CASH = "1100"
ACCT_AR = "1200"
ACCT_VAT = "2200"
ACCT_REVENUE = "4100"


def _coa_map(chart: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(a.get("code")): a for a in chart}


def _next_id(entries: list[dict[str, Any]], prefix: str = "gl") -> str:
    n = len(entries) + 1
    existing = {e.get("id") for e in entries}
    while f"{prefix}-{n:03d}" in existing:
        n += 1
    return f"{prefix}-{n:03d}"


def find_by_source(
    entries: list[dict[str, Any]], source: str, source_id: str
) -> dict[str, Any] | None:
    for e in entries:
        if e.get("source") == source and e.get("source_id") == source_id:
            return e
    return None


def create_manual_journal(
    entries: list[dict[str, Any]],
    *,
    memo: str,
    lines: list[dict[str, Any]],
    chart: list[dict[str, Any]] | None = None,
    posted_date: str | None = None,
    ref: str | None = None,
) -> dict[str, Any]:
    """Create a balanced manual journal entry (Dr must equal Cr)."""
    if not memo or not str(memo).strip():
        raise ValueError("memo_required")
    if not isinstance(lines, list) or len(lines) < 2:
        raise ValueError("need_at_least_two_lines")

    coa = _coa_map(chart or [])
    cleaned: list[dict[str, Any]] = []
    sum_dr = 0.0
    sum_cr = 0.0
    for raw in lines:
        if not isinstance(raw, dict):
            continue
        code = str(raw.get("account") or raw.get("code") or "").strip()
        if not code:
            raise ValueError("account_required")
        debit = float(raw.get("debit") or 0)
        credit = float(raw.get("credit") or 0)
        if debit < 0 or credit < 0:
            raise ValueError("amounts_must_be_non_negative")
        if debit > 0 and credit > 0:
            raise ValueError("line_cannot_have_both_debit_and_credit")
        if debit == 0 and credit == 0:
            continue
        acct = coa.get(code) or {}
        cleaned.append(
            {
                "account": code,
                "debit": round(debit, 2),
                "credit": round(credit, 2),
                "name": acct.get("name") or raw.get("name") or code,
            }
        )
        sum_dr += debit
        sum_cr += credit

    if len(cleaned) < 2:
        raise ValueError("need_at_least_two_lines")
    if abs(sum_dr - sum_cr) > 0.02:
        raise ValueError(f"unbalanced_entry:debit={round(sum_dr,2)}_credit={round(sum_cr,2)}")

    entry_id = _next_id(entries)
    day = posted_date or date.today().isoformat()
    entry = {
        "id": entry_id,
        "date": day,
        "memo": str(memo).strip(),
        "source": "manual",
        "source_id": entry_id,
        "ref": (ref or f"MJ-{entry_id}").strip(),
        "lines": cleaned,
    }
    entries.append(entry)
    return entry


def post_invoice_issue(
    entries: list[dict[str, Any]],
    invoice: dict[str, Any],
    *,
    posted_date: str | None = None,
) -> dict[str, Any]:
    """Dr AR / Cr Revenue (+ VAT). No-op if already posted for this invoice."""
    inv_id = str(invoice.get("id") or "")
    existing = find_by_source(entries, "invoice_issue", inv_id)
    if existing:
        return existing

    subtotal = float(invoice.get("subtotal") or 0)
    vat = float(invoice.get("vat") or round(subtotal * 0.07, 2))
    total = float(invoice.get("total") or round(subtotal + vat, 2))
    # Prefer balancing lines: AR = revenue + vat
    if abs(total - (subtotal + vat)) > 0.02:
        total = round(subtotal + vat, 2)

    day = posted_date or invoice.get("issue_date") or date.today().isoformat()
    number = invoice.get("number") or inv_id
    entry = {
        "id": _next_id(entries),
        "date": day,
        "memo": f"Issue invoice {number}",
        "source": "invoice_issue",
        "source_id": inv_id,
        "ref": number,
        "lines": [
            {"account": ACCT_AR, "debit": total, "credit": 0, "name": "Accounts receivable"},
            {"account": ACCT_REVENUE, "debit": 0, "credit": subtotal, "name": "Sales revenue"},
            {"account": ACCT_VAT, "debit": 0, "credit": vat, "name": "VAT payable"},
        ],
    }
    entries.append(entry)
    invoice["gl_issue_id"] = entry["id"]
    invoice["posted"] = True
    return entry


def post_invoice_payment(
    entries: list[dict[str, Any]],
    invoice: dict[str, Any],
    *,
    receipt: dict[str, Any] | None = None,
    paid_date: str | None = None,
) -> dict[str, Any]:
    """Dr Cash / Cr AR. No-op if already posted for this invoice payment."""
    inv_id = str(invoice.get("id") or "")
    existing = find_by_source(entries, "invoice_payment", inv_id)
    if existing:
        return existing

    total = float(
        (receipt or {}).get("amount")
        or invoice.get("total")
        or 0
    )
    day = (
        paid_date
        or (receipt or {}).get("paid_date")
        or invoice.get("issue_date")
        or date.today().isoformat()
    )
    number = invoice.get("number") or inv_id
    rcpt_no = (receipt or {}).get("number") or ""
    memo = f"Payment {rcpt_no} for {number}".strip() if rcpt_no else f"Payment for {number}"
    entry = {
        "id": _next_id(entries),
        "date": day,
        "memo": memo,
        "source": "invoice_payment",
        "source_id": inv_id,
        "ref": rcpt_no or number,
        "lines": [
            {"account": ACCT_CASH, "debit": total, "credit": 0, "name": "Cash"},
            {"account": ACCT_AR, "debit": 0, "credit": total, "name": "Accounts receivable"},
        ],
    }
    entries.append(entry)
    invoice["gl_payment_id"] = entry["id"]
    if receipt is not None:
        receipt["gl_id"] = entry["id"]
    return entry


def ensure_invoice_trail(
    entries: list[dict[str, Any]],
    invoice: dict[str, Any],
    receipt: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Post issue (+ payment if paid/receipt) and return created/found entries."""
    out = [post_invoice_issue(entries, invoice)]
    status = (invoice.get("status") or "").lower()
    if status == "paid" or receipt is not None:
        out.append(post_invoice_payment(entries, invoice, receipt=receipt))
    return out


def trial_balance(
    entries: list[dict[str, Any]], chart: list[dict[str, Any]]
) -> dict[str, Any]:
    totals: dict[str, dict[str, float]] = {}
    for e in entries:
        for line in e.get("lines") or []:
            code = str(line.get("account") or "")
            row = totals.setdefault(code, {"debit": 0.0, "credit": 0.0})
            row["debit"] += float(line.get("debit") or 0)
            row["credit"] += float(line.get("credit") or 0)

    coa = _coa_map(chart)
    items = []
    for code in sorted(totals.keys()):
        d = round(totals[code]["debit"], 2)
        c = round(totals[code]["credit"], 2)
        acct = coa.get(code) or {}
        items.append(
            {
                "account": code,
                "name": acct.get("name") or code,
                "name_th": acct.get("name_th") or "",
                "type": acct.get("type") or "",
                "debit": d,
                "credit": c,
                "balance": round(d - c, 2),
            }
        )
    sum_d = round(sum(i["debit"] for i in items), 2)
    sum_c = round(sum(i["credit"] for i in items), 2)
    return {
        "items": items,
        "total_debit": sum_d,
        "total_credit": sum_c,
        "balanced": abs(sum_d - sum_c) < 0.02,
        "entry_count": len(entries),
    }


def general_ledger(
    entries: list[dict[str, Any]], chart: list[dict[str, Any]]
) -> dict[str, Any]:
    coa = _coa_map(chart)
    by_acct: dict[str, list[dict[str, Any]]] = {}
    for e in sorted(entries, key=lambda x: (x.get("date") or "", x.get("id") or "")):
        for line in e.get("lines") or []:
            code = str(line.get("account") or "")
            by_acct.setdefault(code, []).append(
                {
                    "date": e.get("date"),
                    "journal_id": e.get("id"),
                    "memo": e.get("memo"),
                    "source": e.get("source"),
                    "ref": e.get("ref"),
                    "debit": float(line.get("debit") or 0),
                    "credit": float(line.get("credit") or 0),
                }
            )

    accounts = []
    for code in sorted(by_acct.keys()):
        lines = by_acct[code]
        acct = coa.get(code) or {}
        running = 0.0
        enriched = []
        for ln in lines:
            running = round(running + ln["debit"] - ln["credit"], 2)
            enriched.append({**ln, "balance": running})
        accounts.append(
            {
                "account": code,
                "name": acct.get("name") or code,
                "name_th": acct.get("name_th") or "",
                "type": acct.get("type") or "",
                "lines": enriched,
                "debit": round(sum(x["debit"] for x in enriched), 2),
                "credit": round(sum(x["credit"] for x in enriched), 2),
                "balance": running,
            }
        )
    return {"accounts": accounts, "entry_count": len(entries)}
