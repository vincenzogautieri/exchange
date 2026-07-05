"""app URL configuration."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.loginView, name='login'),
    path('register/', views.registerView, name='register'),
    path('logout/', views.logoutView, name='logout'),
    path('profit/', views.profit, name='profit'),
    path('orderBook/', views.orderBook, name='orderBook'),
]
