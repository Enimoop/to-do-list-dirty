from django.urls import path

from . import views

urlpatterns = [
	path('', views.index, name="list"),
	path('update_task/<str:pk>/', views.updateTask, name="update_task"),
	path('delete_task/<str:pk>/', views.deleteTask, name="delete"),
    path("watchlist/import/netflix/", views.add_10_netflix, name="import_netflix"),
    path("watchlist/import/prime/", views.add_10_prime, name="import_prime"),
    path("watchlist/import/apple/", views.add_10_apple, name="import_apple"),
    path("watchlist/clear/", views.clear_watchlist, name="clear_watchlist"),
    path("watchlist/delete/<int:pk>/", views.delete_watchlist_item, name="delete_watchlist_item"),
	
]