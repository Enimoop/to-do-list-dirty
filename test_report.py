import json
import sys
from pathlib import Path

import yaml

YAML_PATH = Path("test_list.yaml")
JSON_AUTO_PATH = Path("result_test_auto.json")
JSON_SELENIUM_PATH = Path("result_test_selenium.json")


def load_test_list():
    if not YAML_PATH.exists():
        print(f"Fichier YAML introuvable: {YAML_PATH}", file=sys.stderr)
        sys.exit(1)

    with YAML_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    tests = data.get("tests", [])
    return tests


def load_json_results(path: Path, label: str):
    """
    Charge un fichier JSON de résultats et renvoie un dict
    {test_case_id: outcome}.
    """
    if not path.exists():
        print(f"Fichier JSON introuvable pour {label}: {path}", file=sys.stderr)
        return {}

    print(f"Lecture des tests {label} via {path.name}…")
    with path.open(encoding="utf-8") as f:
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


def detect_kind(entry):
    """
    Retourne l'un des 3 types internes :
    - 'manual'
    - 'auto-unittest'
    - 'auto-selenium'
    à partir du champ type du YAML.
    """
    raw_type = str(entry.get("type", "")).lower()

    if "manual" in raw_type or "manuel" in raw_type:
        return "manual"
    if "selenium" in raw_type:
        return "auto-selenium"
    return "auto-unittest"


def display_type_from_kind(kind: str) -> str:
    """
    Texte affiché dans la colonne "type".
    """
    if kind == "auto-unittest":
        return "auto"
    if kind == "auto-selenium":
        return "auto-selenium"
    return "manual"


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

    auto_results = load_json_results(JSON_AUTO_PATH, "auto-unittest")

    selenium_results = load_json_results(JSON_SELENIUM_PATH, "auto-selenium")

    total_tests = len(tests)
    count_passed = 0       # ✅
    count_failed = 0       # ❌
    count_not_found = 0    # 🕳
    count_manual = 0       # 🫱

    for entry in tests:
        tc_id = format_tc_id(entry)
        kind = detect_kind(entry)
        display_type = display_type_from_kind(kind)

        if kind == "manual":
            status = "🫱Manual test needed"
            count_manual += 1
        else:
            # auto-selenium
            if kind == "auto-selenium":
                outcome = selenium_results.get(tc_id)
            else:  # auto-unittest
                outcome = auto_results.get(tc_id)

            if outcome is None:
                status = "🕳Not found"
                count_not_found += 1
            else:
                status = status_from_outcome(outcome)
                if outcome == "success":
                    count_passed += 1
                else:
                    count_failed += 1

        print(f"{tc_id} | {display_type} | {status}")

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
