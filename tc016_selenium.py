import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

from tc017_selenium import RESULT_JSON

options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

BASE_URL = "http://127.0.0.1:8000/"
TEST_CASE_ID = "TC016"


def count_tasks(driver):
    task_elements = driver.find_elements(By.CSS_SELECTOR, "#task-list .item-row")
    return len(task_elements)


def create_task(driver, title):
    title_input = driver.find_element(By.NAME, "title")
    title_input.clear()
    title_input.send_keys(title)
    title_input.send_keys(Keys.RETURN)
    time.sleep(0.5)


def delete_first_task(driver):
    delete_links = driver.find_elements(By.LINK_TEXT, "Delete")
    if not delete_links:
        return False

    delete_links[0].click()
    time.sleep(0.3)

    confirm_buttons = driver.find_elements(
        By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"
    )
    if confirm_buttons:
        confirm_buttons[0].click()
        time.sleep(0.5)
        return True

    return False


def run_tc016():
    """
    Exécute le test E2E TC016 et renvoie 'success' ou 'failure'.
    """
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()

    try:
        driver.get(BASE_URL)
        time.sleep(1)

        initial_count = count_tasks(driver)
        print(f"Nombre initial de tâches : {initial_count}")

        for i in range(10):
            create_task(driver, f"Tâche_Selenium_{i+1}")

        driver.get(BASE_URL)
        time.sleep(1)
        after_create_count = count_tasks(driver)
        print(f"Nombre après création : {after_create_count}")

        deleted = 0
        while deleted < 10:
            driver.get(BASE_URL)
            time.sleep(0.5)
            if not delete_first_task(driver):
                print("Impossible de supprimer une tâche supplémentaire.")
                break
            deleted += 1

        driver.get(BASE_URL)
        time.sleep(1)
        final_count = count_tasks(driver)
        print(f"Nombre final de tâches : {final_count}")

        if final_count == initial_count and deleted == 10:
            print("✅ TC016 E2E : PASSED")
            return "success"
        else:
            print("❌ TC016 E2E : FAILED")
            return "failure"

    except Exception as e:
        print(f"❌ Erreur pendant le test TC016 : {e}")
        return "failure"
    finally:
        time.sleep(2)
        driver.quit()

def write_result_json(outcome: str):
    """
    Ajoute / met à jour TC016 dans result_test_selenium.json
    sans effacer les autres tests.
    """
    results = []
    if RESULT_JSON.exists():
        try:
            results = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
        except Exception:
            results = []

    results = [r for r in results if r.get("test_case_id") != TEST_CASE_ID]

    results.append(
        {
            "test_case_id": TEST_CASE_ID,
            "name": "TC016 - CRUD 10 tâches via UI",
            "outcome": outcome,
        }
    )

    RESULT_JSON.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("result_test_selenium.json updated with TC016.")


if __name__ == "__main__":
    outcome = run_tc016()
    write_result_json(outcome)

