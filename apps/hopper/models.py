from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Hopper(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hoppers",
        verbose_name="Владелец"
    )
    name = models.CharField(max_length=255, verbose_name="Имя транспорта")
    mass_kg = models.FloatField(verbose_name="Масса (кг)")
    strength = models.FloatField(default=100.0, verbose_name="Запас силы (%)")
    reactor_energy = models.FloatField(default=100.0, verbose_name="Энергия реактора (%)")
    location_state = models.CharField(
        max_length=20,
        choices=[("surface", "На поверхности"), ("underground", "Под землей")],
        default="surface",
        verbose_name="Положение"
    )
    distance = models.FloatField(default=0.0, verbose_name="Пройденная дистанция (м)")
    best_distance = models.FloatField(default=0.0, verbose_name="Рекордная дистанция (м)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def clean(self):
        super().clean()
        name = self.name.strip() if self.name else ''
        if not name:
            raise ValidationError({"name": "Имя не может быть пустым."})
        if not (100.0 <= self.mass_kg <= 500.0):
            raise ValidationError({"mass_kg": "Масса должна быть в диапазоне 100.0…500.0 кг."})
        if not (0.0 <= self.strength <= 100.0):
            raise ValidationError({"strength": "Сила должна быть в диапазоне 0…100."})
        if not (0.0 <= self.reactor_energy <= 100.0):
            raise ValidationError({"reactor_energy": "Энергия реактора должна быть в диапазоне 0…100."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
