from django.contrib import admin
from django.urls import path, include
from apps.accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('accounts/', include('apps.accounts.urls')),
    path('hopper/', include('apps.hopper.urls')),
]
