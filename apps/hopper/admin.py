from django.contrib import admin
from .models import Hopper


@admin.register(Hopper)
class HopperAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'mass_kg', 'strength', 'reactor_energy', 'location_state', 'distance', 'best_distance')
    search_fields = ('name', 'user__username')
