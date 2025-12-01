import json
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from tasks.models import Task


def tc(case_id):
    def decorator(func):
        setattr(func, "test_case_id", case_id)
        return func
    return decorator

class UrlTests(TestCase):
    def setUp(self):
        self.task = Task.objects.create(title="Test task", complete=False)

    # ---------- INDEX (/) ----------
    @tc("TC001")
    def test_home_page_get(self):
        """GET / doit répondre 200 et contenir la version"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("APP_VERSION", response.context)
        self.assertEqual(response.context["APP_VERSION"], settings.APP_VERSION)

    @tc("TC002")
    def test_home_page_post_creates_task_and_redirects(self):
        """POST / doit créer une tâche et redirect"""
        response = self.client.post("/", data={"title": "New task", "complete": False})
        self.assertEqual(response.status_code, 302) 
        self.assertTrue(Task.objects.filter(title="New task").exists())

    @tc("TC003")
    def test_home_page_post_invalid_form_redirects_without_creating(self):
        """POST / invalide (title vide) ne crée rien"""
        count_before = Task.objects.count()
        response = self.client.post("/", data={"title": "", "complete": False})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), count_before)

    # ---------- UPDATE (/update_task/ID/) ----------
    @tc("TC004")
    def test_update_task_get(self):
        """GET update_task doit répondre 200"""
        url = f"/update_task/{self.task.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @tc("TC005")
    def test_update_task_post_updates_and_redirects(self):
        """POST update_task modifie la tâche et redirect"""
        url = f"/update_task/{self.task.id}/"
        response = self.client.post(url, data={"title": "Updated", "complete": True})
        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated")
        self.assertTrue(self.task.complete)

    # ---------- DELETE (/delete_task/ID/) ----------
    @tc("TC006")
    def test_delete_task_get(self):
        """GET delete_task doit répondre 200"""
        url = f"/delete_task/{self.task.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @tc("TC007")
    def test_delete_task_post_deletes_and_redirects(self):
        """POST delete_task supprime la tâche et redirect"""
        url = f"/delete_task/{self.task.id}/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    @tc('TCO19')
    def test_home_page_post_creates_priority_task_when_flag_set(self):
        """
        POST / avec priority=on doit créer une tâche avec priority=True.
        """
        response = self.client.post("/", data={"title": "Urgent", "priority": "on"})
        self.assertEqual(response.status_code, 302)

        task = Task.objects.get(title="Urgent")
        self.assertTrue(
            getattr(task, "priority", None),
            "La tâche créée avec priority=on devrait avoir priority=True"
        )

    @tc('TCO20')
    def test_update_task_can_change_priority(self):
        """
        POST /update_task/<id>/ doit permettre de changer priority.
        """
        task = Task.objects.create(title="To update", priority=False)
        url = f"/update_task/{task.id}/"

        response = self.client.post(url, data={"title": "To update", "priority": "on"})
        self.assertEqual(response.status_code, 302)

        task.refresh_from_db()
        self.assertTrue(task.priority)

    @tc('TCO21')
    def test_index_orders_tasks_with_priority_first(self):
        """
        Les tâches prioritaires doivent apparaître en premier sur la home.
        """
        t1 = Task.objects.create(title="Low 1", priority=False)
        t2 = Task.objects.create(title="High 1", priority=True)
        t3 = Task.objects.create(title="Low 2", priority=False)
        t4 = Task.objects.create(title="High 2", priority=True)

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        tasks_in_context = list(response.context["tasks"])

        priorities = [t.priority for t in tasks_in_context]
        self.assertEqual(
            priorities,
            sorted(priorities, reverse=True),
            "Les tâches prioritaires devraient être en haut de la liste."
        )


class ImportDatasetTests(TestCase):
    @tc("TC008")
    def test_import_real_dataset_json(self):
        """Teste que l'import utilise bien le vrai fichier dataset.json du projet."""
        
        dataset_path = Path(settings.BASE_DIR) / "dataset.json"
        self.assertTrue(dataset_path.exists(), "dataset.json manquant !")

        call_command("import_dataset", path=str(dataset_path))

        data = json.loads(dataset_path.read_text(encoding="utf-8"))

        self.assertEqual(Task.objects.count(), len(data))

        for row in data:
            title = row["title"]
            complete = row["complete"]
            self.assertTrue(Task.objects.filter(title=title, complete=complete).exists())


class TaskPriorityModelTests(TestCase):
    @tc("TC018")
    def test_task_has_priority_field_default_false(self):
        task = Task.objects.create(title="Normal task")

        self.assertTrue(
            hasattr(task, "priority"),
            "Le modèle Task doit avoir un champ 'priority'.",
        )

        self.assertIs(
            task.priority,
            False,
            "Le champ priority devrait être False par défaut.",
        )

