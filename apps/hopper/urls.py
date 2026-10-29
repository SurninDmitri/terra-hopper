from django.urls import path
from . import views

app_name = "hopper"

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_alt'),
    path('create/modal/', views.create_modal, name='create_modal'),
    path('create/', views.create_hopper, name='create_hopper'),
    path('<int:hopper_id>/game/', views.hopper_game_view, name='game'),
    path('<int:hopper_id>/state/', views.hopper_state_api_view, name='state_api'),
    path('<int:hopper_id>/action/', views.hopper_action_view, name='action'),
]
