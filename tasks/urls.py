from django.urls import path
from django.contrib.auth import views as auth_views

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
    
	path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", views.fc_logout, name="logout"),
    path("signup/", views.signup, name="signup"),
    path("fc/login/", views.fc_login, name="fc_login"),
	path("callback", views.fc_callback, name="fc_callback"),
	path("fc/logout/", views.fc_logout, name="fc_logout"),
	path("logout-callback", views.fc_logout_callback, name="fc_logout_callback"),
	
]