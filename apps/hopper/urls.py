from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_alt'),
    path('create/modal/', views.create_modal, name='create_modal'),
    path('create/', views.create_hopper, name='create_hopper'),
]
