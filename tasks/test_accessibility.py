import json

from axe_selenium_python import Axe
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from tasks.models import Task
from tasks.tests import tc


class AccessibilityTests(LiveServerTestCase):
    """
    Tests d’accessibilité avec axe-core (mode simplifié).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        options = Options()

        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
        cls.driver.maximize_window()
        cls.driver.set_script_timeout(60)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def run_axe_on_url(self, url: str, label: str):
        """
        Ouvre une URL, lance axe, vérifie qu'il n'y a
        aucune violation d’accessibilité (mode simple).
        """
        print(f"[AXE] Analyse de {url}…")
        self.driver.get(url)

        axe = Axe(self.driver)
        axe.inject()

        try:
            results = axe.run(context="body")
        except TimeoutException as e:
            self.fail(f"Axe a mis trop de temps sur {url} (script timeout): {e.msg}")

        violations = results.get("violations", [])
        print(f"[AXE] {label} -> {len(violations)} violation(s)")

        with open(f"axe_{label}.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        self.assertEqual(
            len(violations),
            0,
            msg=f"Violations sur {url} : {violations}",
        )

    @tc("TC022")
    def test_home_is_wcag_level_a(self):
        """
        La page d’accueil doit être conforme (aucune violation axe).
        """
        url = f"{self.live_server_url}/"
        self.run_axe_on_url(url, "home")

    @tc("TC023")
    def test_update_page_is_wcag_level_a(self):
        """
        La page d’édition d’une tâche doit être conforme.
        """
        task = Task.objects.create(title="Tâche pour a11y", complete=False)
        url = f"{self.live_server_url}/update_task/{task.id}/"
        self.run_axe_on_url(url, "update")

    @tc("TC024")
    def test_delete_page_is_wcag_level_a(self):
        """
        La page de suppression d’une tâche doit être conforme.
        """
        task = Task.objects.create(title="Tâche pour suppression", complete=False)
        url = f"{self.live_server_url}/delete_task/{task.id}/"
        self.run_axe_on_url(url, "delete")
