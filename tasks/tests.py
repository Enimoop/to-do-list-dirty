# Create your tests here.
from django.test import TestCase
from django.urls import reverse

from tasks.models import Task


class UrlTests(TestCase):
    def setUp(self):
        self.task = Task.objects.create(title="Test task")

    def test_home_page(self):
        """La page d'accueil / doit répondre 200"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_update_task_page(self):
        """La page /update_task/<ID>/ doit répondre 200"""
        url = f"/update_task/{self.task.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_task_page(self):
        """La page /delete_task/<ID>/ doit répondre 200"""
        url = f"/delete_task/{self.task.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
