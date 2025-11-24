import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tasks.models import Task


class Command(BaseCommand):
    help = "Import tasks from a JSON dataset file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default=str(Path(settings.BASE_DIR) / "dataset.json"),
            help="Path to the dataset.json file",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])

        if not path.exists():
            raise CommandError(f"Dataset file not found: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON file: {e}") from e

        if not isinstance(data, list):
            raise CommandError("dataset.json must contain a list of tasks")

        created = 0
        for row in data:
            title = row.get("title")
            complete = bool(row.get("complete", False))

            if not title:
                continue

            Task.objects.create(title=title, complete=complete)
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {created} task(s)."))
