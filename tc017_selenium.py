import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "http://127.0.0.1:8000/"
TEST_CASE_ID = "TC017"
RESULT_JSON = Path("result_test_selenium.json")


def create_task(driver, title: str) -> None:
    """
    Crée une tâche via le formulaire (input name='title').
    """
    title_input = driver.find_element(By.NAME, "title")
    title_input.clear()
    title_input.send_keys(title)
    title_input.send_keys(Keys.RETURN)
    time.sleep(0.5)


def get_last_task_id(driver) -> str | None:
    """
    Récupère le data-task-id de la dernière tâche dans #task-list.
    """
    rows = driver.find_elements(By.CSS_SELECTOR, "#task-list .item-row")
    if not rows:
        return None
    last_row = rows[-1]
    return last_row.get_attribute("data-task-id")


def is_task_present_by_id(driver, task_id: str) -> bool:
    """
    Vérifie si une tâche avec un data-task-id donné existe encore.
    """
    selector = f'div.item-row[data-task-id="{task_id}"]'
    elements = driver.find_elements(By.CSS_SELECTOR, selector)
    return len(elements) > 0


def delete_task_by_id(driver, task_id: str) -> bool:
    """
    Supprime la tâche identifiée par son data-task-id.

    - On cherche .item-row[data-task-id="..."]
    - On clique sur le lien data-role="delete-task-button"
    - On confirme sur la page de delete
    """
    selector = f'div.item-row[data-task-id="{task_id}"]'
    rows = driver.find_elements(By.CSS_SELECTOR, selector)
    if not rows:
        return False

    row = rows[0]

    delete_buttons = row.find_elements(
        By.CSS_SELECTOR, 'a[data-role="delete-task-button"]'
    )
    if not delete_buttons:
        return False

    delete_buttons[0].click()
    time.sleep(0.3)

    confirm_buttons = driver.find_elements(
        By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"
    )
    if confirm_buttons:
        confirm_buttons[0].click()
        time.sleep(0.5)
        return True

    return False


def run_tc017():
    """
    TC017 - Impact croisé (version ID) :

    - Créer une tâche A
    - Récupérer son ID
    - Créer une tâche B
    - Récupérer son ID
    - Supprimer B par son ID
    - Vérifier que:
        * A (ID A) est toujours présente
        * B (ID B) n'est plus présente
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


    title_a = "E2E_Impact_A"
    title_b = "E2E_Impact_B"

    try:
        driver.get(BASE_URL)
        time.sleep(1)

        create_task(driver, title_a)
        driver.get(BASE_URL)
        time.sleep(0.5)
        task_a_id = get_last_task_id(driver)
        if not task_a_id:
            print("❌ TC017: impossible de récupérer l'ID de la tâche A.")
            return "failure"

        print(f"ID de la tâche A : {task_a_id}")

        create_task(driver, title_b)
        driver.get(BASE_URL)
        time.sleep(0.5)
        task_b_id = get_last_task_id(driver)
        if not task_b_id:
            print("❌ TC017: impossible de récupérer l'ID de la tâche B.")
            return "failure"

        print(f"ID de la tâche B : {task_b_id}")

        if not delete_task_by_id(driver, task_b_id):
            print("❌ TC017: impossible de supprimer la tâche B.")
            return "failure"

        driver.get(BASE_URL)
        time.sleep(0.5)
        a_still_there = is_task_present_by_id(driver, task_a_id)
        b_still_there = is_task_present_by_id(driver, task_b_id)

        print(f"Présence de A (id={task_a_id}) après suppression de B : {a_still_there}")
        print(f"Présence de B (id={task_b_id}) après suppression      : {b_still_there}")

        if a_still_there and not b_still_there:
            print("✅ TC017 E2E impacts croisés : PASSED")
            return "success"
        else:
            print("❌ TC017 E2E impacts croisés : FAILED")
            return "failure"

    except Exception as e:
        print(f"❌ Erreur pendant le test TC017 : {e}")
        return "failure"
    finally:
        time.sleep(2)
        driver.quit()


def write_result_json(outcome: str):
    """
    Ajoute / met à jour TC017 dans result_test_selenium.json
    SANS supprimer les autres tests existants.
    """
    results = []

    if RESULT_JSON.exists():
        try:
            existing = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
            if isinstance(existing, list):
                results = existing
        except Exception:
            pass

    results = [r for r in results if r.get("test_case_id") != TEST_CASE_ID]

    results.append(
        {
            "test_case_id": TEST_CASE_ID,
            "name": "TC017 - Impact croisé: suppression de B ne supprime pas A",
            "outcome": outcome,
        }
    )

    RESULT_JSON.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )



if __name__ == "__main__":
    outcome = run_tc017()
    write_result_json(outcome)
