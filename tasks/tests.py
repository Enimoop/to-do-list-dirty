import json
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from tasks.models import Task


class UrlTests(TestCase):
    def setUp(self):
        self.task = Task.objects.create(title="Test task", complete=False)

    # ---------- INDEX (/) ----------
    def test_home_page_get(self):
        """GET / doit répondre 200 et contenir la version"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("APP_VERSION", response.context)
        self.assertEqual(response.context["APP_VERSION"], settings.APP_VERSION)

    def test_home_page_post_creates_task_and_redirects(self):
        """POST / doit créer une tâche et redirect"""
        response = self.client.post("/", data={"title": "New task", "complete": False})
        self.assertEqual(response.status_code, 302) 
        self.assertTrue(Task.objects.filter(title="New task").exists())

    def test_home_page_post_invalid_form_redirects_without_creating(self):
        """POST / invalide (title vide) ne crée rien"""
        count_before = Task.objects.count()
        response = self.client.post("/", data={"title": "", "complete": False})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), count_before)

    # ---------- UPDATE (/update_task/ID/) ----------
    def test_update_task_get(self):
        """GET update_task doit répondre 200"""
        url = f"/update_task/{self.task.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_task_post_updates_and_redirects(self):
        """POST update_task modifie la tâche et redirect"""
        url = f"/update_task/{self.task.id}/"
        response = self.client.post(url, data={"title": "Updated", "complete": True})
        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated")
        self.assertTrue(self.task.complete)

    # ---------- DELETE (/delete_task/ID/) ----------
    def test_delete_task_get(self):
        """GET delete_task doit répondre 200"""
        url = f"/delete_task/{self.task.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_task_post_deletes_and_redirects(self):
        """POST delete_task supprime la tâche et redirect"""
        url = f"/delete_task/{self.task.id}/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

class ImportDatasetTests(TestCase):
    def test_import_real_dataset_json(self):
        """Teste que l'import utilise bien le vrai fichier dataset.json du projet."""
        
        dataset_path = Path(settings.BASE_DIR) / "dataset.json"
        self.assertTrue(dataset_path.exists(), "dataset.json manquant !")

        call_command("import_dataset", path=str(dataset_path))

        import json
        data = json.loads(dataset_path.read_text(encoding="utf-8"))

        self.assertEqual(Task.objects.count(), len(data))

        for row in data:
            title = row["title"]
            complete = row["complete"]
            self.assertTrue(Task.objects.filter(title=title, complete=complete).exists())