import json
import sys
from pathlib import Path

import yaml


YAML_PATH = Path("test_list.yaml")
JSON_PATH = Path("result_test_auto.json")


def load_test_list():
    if not YAML_PATH.exists():
        print(f"Fichier YAML introuvable: {YAML_PATH}", file=sys.stderr)
        sys.exit(1)

    with YAML_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    tests = data.get("tests", [])
    return tests


def load_json_results():
    if not JSON_PATH.exists():
        print(f"Fichier JSON introuvable: {JSON_PATH}", file=sys.stderr)
        return {}

    print("Lecture des tests auto via result_test_auto.json…")
    with JSON_PATH.open(encoding="utf-8") as f:
        raw = json.load(f)

    results = {}
    for entry in raw:
        tc_id = entry.get("test_case_id")
        outcome = entry.get("outcome")
        if tc_id:
            results[tc_id] = outcome

    print("OK")
    return results


def format_tc_id(entry):
    """
    On génère un identifiant de type TC001 à partir du numero.
    Si un champ explicite 'test_case_id' existe dans le YAML, on le privilégie.
    """
    if "test_case_id" in entry:
        return entry["test_case_id"]

    numero = entry.get("numero")
    if numero is None:
        return "TC???"
    return f"TC{int(numero):03d}"


def detect_type(entry):
    """
    Retourne 'auto' ou 'manual' pour l'affichage à partir du champ type du YAML.
    """
    raw_type = str(entry.get("type", "")).lower()
    if "manual" in raw_type or "manuel" in raw_type:
        return "manual"
    return "auto"


def status_from_outcome(outcome):
    """
    Mappe l'outcome du JSON vers les emojis de statut.
    success -> ✅Passed
    autre (failure, error, skipped...) -> ❌Failed
    """
    if outcome == "success":
        return "✅Passed"
    else:
        return "❌Failed"


def percent(part, total):
    if total == 0:
        return 0.0
    return round(part * 100.0 / total, 1)


def main():
    tests = load_test_list()
    results = load_json_results()

    total_tests = len(tests)
    count_passed = 0       # ✅
    count_failed = 0       # ❌
    count_not_found = 0    # 🕳
    count_manual = 0       # 🫱

    for entry in tests:
        tc_id = format_tc_id(entry)
        test_type = detect_type(entry)

        if test_type == "manual":
            status = "🫱Manual test needed"
            count_manual += 1
        else:
            outcome = results.get(tc_id)
            if outcome is None:
                status = "🕳Not found"
                count_not_found += 1
            else:
                status = status_from_outcome(outcome)
                if outcome == "success":
                    count_passed += 1
                else:
                    count_failed += 1

        print(f"{tc_id} | {test_type} | {status}")

    print()
    print(f"Number of tests: {total_tests}")

    p_passed = percent(count_passed, total_tests)
    p_failed = percent(count_failed, total_tests)
    p_not_found = percent(count_not_found, total_tests)
    p_manual = percent(count_manual, total_tests)
    p_passed_plus_manual = percent(count_passed + count_manual, total_tests)

    print(f"✅Passed tests: {count_passed} ({p_passed}%)")
    print(f"❌Failed tests: {count_failed} ({p_failed}%)")
    print(f"🕳Not found tests: {count_not_found} ({p_not_found}%)")
    print(f"🫱Test to pass manually: {count_manual} ({p_manual}%)")
    print(f"✅Passed + 🫱Manual: {count_passed + count_manual} ({p_passed_plus_manual}%)")


if __name__ == "__main__":
    main()
