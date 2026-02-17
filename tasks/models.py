from django.db import models
from django.contrib.auth.models import User

PROVIDER_CHOICES = [
    ("NETFLIX", "Netflix"),
    ("PRIME", "Amazon Prime"),
    ("APPLE", "Apple TV"),
]


# Create your models here.
class Task(models.Model):
	title = models.CharField(max_length=200)
	complete = models.BooleanField(default=False)
	created = models.DateTimeField(auto_now_add=True)
	priority = models.BooleanField(default=False)


	def __str__(self) -> str:
		return self.title

class WatchlistItem(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist_items")

    tmdb_id = models.IntegerField()
    title = models.CharField(max_length=255)

    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
    )

    poster_path = models.CharField(max_length=255, blank=True, default="")
    vote_average = models.FloatField(null=True, blank=True)
    overview = models.TextField(blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "tmdb_id"], name="uniq_user_tmdb"),
        ]

    def __str__(self):
        return self.title