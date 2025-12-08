#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

YAML_PATH = Path("test_list.yaml")
JSON_AUTO_PATH = Path("result_test_auto.json")
JSON_SELENIUM_PATH = Path("result_test_selenium.json")
PDF_PATH = Path("delivery_note.pdf")


def load_test_list():
    if not YAML_PATH.exists():
        print(f"Fichier YAML introuvable: {YAML_PATH}", file=sys.stderr)
        sys.exit(1)

    with YAML_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("tests", [])


def load_json_results(path: Path):
    if not path.exists():
        return {}

    with path.open(encoding="utf-8") as f:
        raw = json.load(f)

    results = {}
    for entry in raw:
        tc_id = entry.get("test_case_id")
        outcome = entry.get("outcome")
        if tc_id:
            results[tc_id] = outcome
    return results


def format_tc_id(entry):
    if "test_case_id" in entry:
        return entry["test_case_id"]

    numero = entry.get("numero")
    if numero is None:
        return "TC???"
    return f"TC{int(numero):03d}"


def detect_kind(entry):
    raw_type = str(entry.get("type", "")).lower()

    if "manual" in raw_type or "manuel" in raw_type:
        return "manual"
    if "selenium" in raw_type:
        return "auto-selenium"
    if "axe" in raw_type or "access" in raw_type:
        return "auto-axe"
    return "auto-unittest"


def display_type_from_kind(kind: str) -> str:
    if kind == "auto-unittest":
        return "auto"
    if kind == "auto-selenium":
        return "auto-selenium"
    if kind == "auto-axe":
        return "auto-axe"
    return "manual"


def status_from_outcome(outcome):
    if outcome == "success":
        return "✅ Passed"
    elif outcome == "failure":
        return "❌ Failed"
    else:
        return f"❔ {outcome or 'Unknown'}"


def percent(part, total):
    if total == 0:
        return 0.0
    return round(part * 100.0 / total, 1)


def build_data_for_pdf():
    tests = load_test_list()
    auto_results = load_json_results(JSON_AUTO_PATH)
    selenium_results = load_json_results(JSON_SELENIUM_PATH)

    axe_json_path = Path("result_test_axe.json")
    axe_results = load_json_results(axe_json_path)

    rows = []

    total_tests = len(tests)
    count_passed = 0
    count_failed = 0
    count_not_found = 0
    count_manual = 0

    for entry in tests:
        tc_id = format_tc_id(entry)
        kind = detect_kind(entry)
        display_type = display_type_from_kind(kind)

        if kind == "manual":
            status = "🫱 Manual test needed"
            outcome = None
            count_manual += 1
        else:
            if kind == "auto-selenium":
                outcome = selenium_results.get(tc_id)
            elif kind == "auto-axe":
                outcome = axe_results.get(tc_id)
            else:
                outcome = auto_results.get(tc_id)

            if outcome is None:
                status = "🕳 Not found"
                count_not_found += 1
            else:
                status = status_from_outcome(outcome)
                if outcome == "success":
                    count_passed += 1
                else:
                    count_failed += 1

        rows.append((tc_id, display_type, status))

    stats = {
        "total": total_tests,
        "passed": count_passed,
        "failed": count_failed,
        "not_found": count_not_found,
        "manual": count_manual,
    }
    return rows, stats


def generate_pdf():
    rows, stats = build_data_for_pdf()

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        title="Bon de livraison des tests",
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Bon de livraison des tests", styles["Title"]))
    story.append(Spacer(1, 12))

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    story.append(Paragraph(f"Date d'exécution : {now}", styles["Normal"]))
    story.append(Spacer(1, 12))

    table_data = [("Test case", "Type", "Résultat")] + rows
    table = Table(table_data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 24))

    total = stats["total"]
    p_passed = percent(stats["passed"], total)
    p_failed = percent(stats["failed"], total)
    p_not_found = percent(stats["not_found"], total)
    p_manual = percent(stats["manual"], total)
    p_ok_plus_manual = percent(stats["passed"] + stats["manual"], total)

    summary_lines = [
        f"Nombre de tests : {total}",
        f"✅ Passed : {stats['passed']} ({p_passed}%)",
        f"❌ Failed : {stats['failed']} ({p_failed}%)",
        f"🕳 Not found : {stats['not_found']} ({p_not_found}%)",
        f"🫱 Tests manuels : {stats['manual']} ({p_manual}%)",
        f"✅ + 🫱 : {stats['passed'] + stats['manual']} ({p_ok_plus_manual}%)",
    ]
    for line in summary_lines:
        story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)
    print(f"PDF généré : {PDF_PATH}")


if __name__ == "__main__":
    generate_pdf()
