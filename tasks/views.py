from django.conf import settings
from django.shortcuts import redirect, render

import random

import requests
from django.views.decorators.http import require_POST

from .forms import TaskForm
from .models import Task
from .models import WatchlistItem


from django.shortcuts import render, redirect
from django.conf import settings

from .models import Task, WatchlistItem
from .forms import TaskForm

def index(request):
    tasks = Task.objects.all().order_by('-priority', 'id')

    watchlist_items = WatchlistItem.objects.all().order_by('-created')

    form = TaskForm()

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect('/')

    context = {
        'tasks': tasks,
        'watchlist_items': watchlist_items,
        'form': form,
        'APP_VERSION': settings.APP_VERSION,
    }
    return render(request, 'tasks/list.html', context)

def updateTask(request,pk):
	task = Task.objects.get(id=pk)
	form = TaskForm(instance=task)

	if request.method == "POST":
		form = TaskForm(request.POST,instance=task)
		if form.is_valid():
			form.save()
			return redirect('/')


	context = {'form':form}
	return render(request, 'tasks/update_task.html',context)

def deleteTask(request,pk):
	item = Task.objects.get(id=pk)

	if request.method == "POST":
		item.delete()
		return redirect('/')

	context = {'item':item}
	return render(request, 'tasks/delete.html', context)


TMDB_BASE = "https://api.themoviedb.org/3"


def import_10(provider_code: str, provider_id: str):
    created_count = 0
    tried_pages = set()

    if not provider_id:
        return 0

    while created_count < 10 and len(tried_pages) < 30:
        page = random.randint(1, 50) 
        if page in tried_pages:
            continue
        tried_pages.add(page)

        params = {
            "api_key": settings.TMDB_API_KEY,
            "with_watch_providers": provider_id,
            "watch_region": settings.TMDB_REGION,
            "with_watch_monetization_types": "flatrate",
            "page": page,
        }

        r = requests.get(f"{TMDB_BASE}/discover/tv", params=params, timeout=15)
        r.raise_for_status()
        results = r.json().get("results") or []

        if not results:
            continue

        random.shuffle(results)

        for s in results:
            if created_count >= 10:
                break

            tmdb_id = s.get("id")
            title = s.get("name") or s.get("original_name") or "Sans titre"
            if not tmdb_id:
                continue

            obj, created = WatchlistItem.objects.get_or_create(
                provider=provider_code,
                tmdb_id=tmdb_id,
                defaults={
                    "title": title,
                    "poster_path": s.get("poster_path") or "",
                    "vote_average": s.get("vote_average"),
                    "overview": s.get("overview") or "",
                },
            )

            if created:
                created_count += 1

    return created_count

@require_POST
def add_10_netflix(request):
    import_10("NETFLIX", settings.TMDB_NETFLIX_ID)
    return redirect("/")


@require_POST
def add_10_prime(request):
    import_10("PRIME", settings.TMDB_PRIME_ID)
    return redirect("/")


@require_POST
def add_10_apple(request):
    import_10("APPLE", settings.TMDB_APPLE_ID)
    return redirect("/")

@require_POST
def clear_watchlist(request):
    WatchlistItem.objects.all().delete()
    return redirect("/")

from django.shortcuts import get_object_or_404

@require_POST
def delete_watchlist_item(request, pk):
    item = get_object_or_404(WatchlistItem, id=pk)
    item.delete()
    return redirect("/")