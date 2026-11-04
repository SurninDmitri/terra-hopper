from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from apps.accounts import views


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health', health_check, name='health'),
    path('health/', health_check),
    path('', views.index, name='index'),
    path('accounts/', include('apps.accounts.urls')),
    path('hopper/', include('apps.hopper.urls')),
]
