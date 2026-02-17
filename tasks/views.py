from __future__ import annotations

import random
import secrets
import hashlib
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User

from .forms import TaskForm
from .models import Task, WatchlistItem


TMDB_BASE = "https://api.themoviedb.org/3"

FC_AUTHORIZE = "/api/v1/authorize"
FC_TOKEN = "/api/v1/token"
FC_USERINFO = "/api/v1/userinfo"
FC_LOGOUT = "/api/v1/logout"

@login_required
def index(request):
    tasks = Task.objects.all().order_by("-priority", "id")
    form = TaskForm()

    watchlist_items = WatchlistItem.objects.filter(user=request.user).order_by("-created")

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect("/")

    context = {
        "tasks": tasks,
        "watchlist_items": watchlist_items,
        "form": form,
        "APP_VERSION": settings.APP_VERSION,
    }
    return render(request, "tasks/list.html", context)


def updateTask(request, pk):
    task = Task.objects.get(id=pk)
    form = TaskForm(instance=task)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("/")

    return render(request, "tasks/update_task.html", {"form": form})


def deleteTask(request, pk):
    item = Task.objects.get(id=pk)

    if request.method == "POST":
        item.delete()
        return redirect("/")

    return render(request, "tasks/delete.html", {"item": item})


def import_10(user, provider_code: str, provider_id: str):
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

            _, created = WatchlistItem.objects.get_or_create(
                user=user,                
                tmdb_id=tmdb_id,
                defaults={
                    "title": title,
                    "provider": provider_code,
                    "poster_path": s.get("poster_path") or "",
                    "vote_average": s.get("vote_average"),
                    "overview": s.get("overview") or "",
                },
            )

            if created:
                created_count += 1

    return created_count


@login_required
@require_POST
def add_10_netflix(request):
    import_10(request.user, "NETFLIX", settings.TMDB_NETFLIX_ID)
    return redirect("/")


@login_required
@require_POST
def add_10_prime(request):
    import_10(request.user, "PRIME", settings.TMDB_PRIME_ID)
    return redirect("/")


@login_required
@require_POST
def add_10_apple(request):
    import_10(request.user, "APPLE", settings.TMDB_APPLE_ID)
    return redirect("/")


@login_required
@require_POST
def clear_watchlist(request):
    WatchlistItem.objects.filter(user=request.user).delete() 
    return redirect("/")


@login_required
@require_POST
def delete_watchlist_item(request, pk):
    item = get_object_or_404(WatchlistItem, id=pk, user=request.user)
    item.delete()
    return redirect("/")


def signup(request):
    if request.user.is_authenticated:
        return redirect("list")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("list")
    else:
        form = UserCreationForm()

    return render(request, "auth/signup.html", {"form": form})

def fc_login(request):
    state = secrets.token_urlsafe(24)
    request.session["fc_state"] = state
    nonce = secrets.token_urlsafe(24)
    request.session["fc_nonce"] = nonce

    params = {
        "response_type": "code",
        "client_id": settings.FRANCECONNECT_CLIENT_ID,
        "redirect_uri": settings.FRANCECONNECT_REDIRECT_URI, 
        "scope": settings.FRANCECONNECT_SCOPE,
        "state": state,
        "nonce": nonce
    }

    url = settings.FRANCECONNECT_BASE_URL + FC_AUTHORIZE
    return redirect(f"{url}?{requests.compat.urlencode(params)}")


def fc_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not code or not state or state != request.session.get("fc_state"):
        return redirect("login")

    token_url = settings.FRANCECONNECT_BASE_URL + FC_TOKEN
    token_resp = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.FRANCECONNECT_REDIRECT_URI,
            "client_id": settings.FRANCECONNECT_CLIENT_ID,
            "client_secret": settings.FRANCECONNECT_CLIENT_SECRET,
        },
        timeout=15,
    )
    token_resp.raise_for_status()
    token_json = token_resp.json()

    access_token = token_json.get("access_token")
    id_token = token_json.get("id_token")
    if id_token:
        request.session["fc_id_token"] = id_token
    if not access_token:
        return redirect("login")

    userinfo_url = settings.FRANCECONNECT_BASE_URL + FC_USERINFO
    userinfo_resp = requests.get(
        userinfo_url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    userinfo_resp.raise_for_status()
    claims = userinfo_resp.json()

    sub = claims.get("sub")
    if not sub:
        return redirect("login")

    short = hashlib.sha256(sub.encode("utf-8")).hexdigest()[:12]
    username = f"fc_{short}"

    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": claims.get("email") or ""},
    )
    if created:
        user.set_unusable_password()
        user.save()

    login(request, user)
    return redirect("list")

def fc_logout_callback(request):
    return redirect("login")

@login_required
def fc_logout(request):
    id_token = request.session.get("fc_id_token")

    logout(request)

    if not id_token:
        return redirect("login")

    params = {
        "id_token_hint": id_token,
        "post_logout_redirect_uri": settings.FRANCECONNECT_LOGOUT_REDIRECT_URI,
    }

    logout_url = settings.FRANCECONNECT_BASE_URL + FC_LOGOUT + "?" + urlencode(params)
    return redirect(logout_url)