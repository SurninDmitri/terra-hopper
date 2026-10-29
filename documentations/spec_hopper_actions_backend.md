# ТЗ: Этап 4. Бэкенд действий транспорта и доменная логика (Hopper Actions Backend)

**Проект:** «Терра-Хоппер Онлайн» (Django + HTMX)

**Фокус этапа:** Перенос доменной модели `TerraHopper` из 1-й практики в Django-приложение, создание сервисного слоя для работы с БД, обработка HTTP/HTMX-запросов на выполнение действий и автоматическое обновление рекордов в турнирной таблице.

---

## 1. Архитектура и структура кода

Структура модуля `apps/hopper/`:

```
apps/hopper/
├── domain/
│   ├── __init__.py
│   ├── exceptions.py       # Кастомные исключения
│   └── terra_hopper.py     # Чистый Python-класс TerraHopper (доменная логика)
├── models.py               # ORM модель Hopper
├── services.py             # Сервисный слой (атомарное применение действий к БД)
├── views.py                # Эндпоинты для выполнения действий (HTMX)
├── urls.py                 # Маршруты
└── tests/
    └── test_actions.py     # Модульные и функциональные тесты
```

---

## 2. Доменная логика (`apps/hopper/domain/`)

### 2.1. Исключения (`exceptions.py`)

Все доменные ошибки наследуются от единого базового класса:

```python
class TerraHopperError(Exception):
    """Базовое исключение домена TerraHopper."""
    pass

class NoTransportError(TerraHopperError):
    """Вызывается, если транспорт не создан или не выбран."""
    pass

class InvalidLocationError(TerraHopperError):
    """Вызывается при попытке выполнить действие в недопустимой локации."""
    pass

class NotEnoughStrengthError(TerraHopperError):
    """Вызывается при нехватке силы механических узлов."""
    pass

class NotEnoughEnergyError(TerraHopperError):
    """Вызывается при нехватке энергии реактора."""
    pass
```

### 2.2. Чистый класс `TerraHopper` (`terra_hopper.py`)

Доменный класс инициализируется из ORM-модели или напрямую параметрами, рассчитывает физику действий и не зависит от Django ORM.

```python
from .exceptions import (
    InvalidLocationError,
    NotEnoughStrengthError,
    NotEnoughEnergyError,
)

class TerraHopper:
    def __init__(
        self,
        name: str,
        mass_kg: float,
        strength: float = 100.0,
        reactor_energy: float = 100.0,
        location_state: str = "surface",
        distance: float = 0.0,
        best_distance: float = 0.0,
    ) -> None:
        name_clean = name.strip() if name else ""
        if not name_clean:
            raise ValueError("Имя не может быть пустым.")
        if not (100.0 <= mass_kg <= 500.0):
            raise ValueError("Масса должна быть в диапазоне 100.0…500.0 кг.")
        if not (0.0 <= strength <= 100.0):
            raise ValueError("Сила должна быть в диапазоне 0…100.")
        if not (0.0 <= reactor_energy <= 100.0):
            raise ValueError("Энергия реактора должна быть в диапазоне 0…100.")

        self.name = name_clean
        self.mass_kg = mass_kg
        self.strength = strength
        self.reactor_energy = reactor_energy
        self.location_state = location_state
        self.distance = distance
        self.best_distance = max(best_distance, distance)

    def _check_and_update_recovery(self, old_distance: float) -> None:
        """
        Проверяет пересечение новых отметок кратных 100 м.
        На каждую новую отметку 100 м начисляет пассивное восстановление.
        """
        old_marks = int(old_distance // 100)
        new_marks = int(self.distance // 100)

        if new_marks > old_marks:
            count = new_marks - old_marks
            recovery_val = 45.0 - (self.mass_kg / 10.0) * 0.5
            for _ in range(count):
                self.strength = min(100.0, self.strength + recovery_val)
                self.reactor_energy = min(100.0, self.reactor_energy + recovery_val)

        if self.distance > self.best_distance:
            self.best_distance = self.distance

    def basic_jump(self) -> None:
        if self.location_state == "underground":
            raise InvalidLocationError("Прыжок невозможен: транспорт находится под землей.")
        
        required_strength = 3.0 + (self.mass_kg / 100.0)
        if self.strength < required_strength:
            raise NotEnoughStrengthError("Не достаточно силы для выполнения обычного прыжка.")

        old_dist = self.distance
        self.strength -= required_strength
        self.distance += 10.0
        self._check_and_update_recovery(old_dist)

    def long_jump(self, use_reactor: bool = False) -> None:
        if self.location_state == "underground":
            raise InvalidLocationError("Дальний прыжок невозможен: транспорт находится под землей.")

        required_strength = 10.0 + (self.mass_kg / 100.0) * 2.0
        if self.strength < required_strength:
            raise NotEnoughStrengthError("Недостаточно силы для выполнения дальнего прыжка.")

        if use_reactor:
            if self.reactor_energy < 50.0:
                raise NotEnoughEnergyError("Недостаточно энергии реактора для форсажа (требуется 50.0).")
            
            old_dist = self.distance
            self.strength -= required_strength
            self.reactor_energy -= 50.0
            self.distance += 45.0
            self._check_and_update_recovery(old_dist)
        else:
            old_dist = self.distance
            self.strength -= required_strength
            self.distance += 30.0
            self._check_and_update_recovery(old_dist)

    def go_underground(self) -> None:
        if self.location_state == "underground":
            raise InvalidLocationError("Транспорт уже находится под землей.")

        required_strength = 3.0 * (self.mass_kg / 100.0)
        if self.strength < required_strength:
            raise NotEnoughStrengthError("Недостаточно силы для погружения под землю.")

        self.strength -= required_strength
        self.location_state = "underground"

    def return_to_surface(self) -> None:
        if self.location_state == "surface":
            raise InvalidLocationError("Транспорт уже находится на поверхности.")

        required_strength = 3.0 * (self.mass_kg / 100.0)
        if self.strength < required_strength:
            raise NotEnoughStrengthError("Недостаточно силы для возвращения на поверхность.")

        self.strength -= required_strength
        self.location_state = "surface"

    def drill_forward(self) -> None:
        if self.location_state == "surface":
            raise InvalidLocationError("Подземное бурение невозможно на поверхности. Сначала погрузитесь.")

        required_strength = 10.0 + (self.mass_kg / 100.0) * 3.0
        if self.strength < required_strength:
            raise NotEnoughStrengthError("Недостаточно силы для подземного бурения.")

        if self.reactor_energy < 50.0:
            raise NotEnoughEnergyError("Недостаточно энергии реактора для запуска буров (требуется 50.0).")

        old_dist = self.distance
        self.strength -= required_strength
        self.reactor_energy -= 50.0
        self.distance += 40.0
        self._check_and_update_recovery(old_dist)
```

---

## 3. Сервисный слой (`apps/hopper/services.py`)

Сервисный слой отвечает за загрузку ORM-модели, конвертацию в доменный объект, выполнение действия и атомарное сохранение результатов обратно в PostgreSQL.

```python
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Hopper
from .domain.terra_hopper import TerraHopper

def execute_hopper_action(hopper_id: int, user, action_type: str, use_reactor: bool = False) -> Hopper:
    """
    Выполняет указанное действие над транспортом пользователя в рамках одной транзакции.
    
    Поддерживаемые action_type:
    - 'basic_jump'
    - 'long_jump'
    - 'go_underground'
    - 'return_to_surface'
    - 'drill_forward'
    """
    with transaction.atomic():
        # Блокировка строки записи для предотвращения race condition
        hopper_orm = get_object_or_404(
            Hopper.objects.select_for_update(), 
            id=hopper_id, 
            user=user
        )

        # Воссоздаем доменный объект из ORM
        domain_hopper = TerraHopper(
            name=hopper_orm.name,
            mass_kg=hopper_orm.mass_kg,
            strength=hopper_orm.strength,
            reactor_energy=hopper_orm.reactor_energy,
            location_state=hopper_orm.location_state,
            distance=hopper_orm.distance,
            best_distance=hopper_orm.best_distance,
        )

        # Делегирование действия доменной модели
        if action_type == "basic_jump":
            domain_hopper.basic_jump()
        elif action_type == "long_jump":
            domain_hopper.long_jump(use_reactor=use_reactor)
        elif action_type == "go_underground":
            domain_hopper.go_underground()
        elif action_type == "return_to_surface":
            domain_hopper.return_to_surface()
        elif action_type == "drill_forward":
            domain_hopper.drill_forward()
        else:
            raise ValueError(f"Неизвестное действие: {action_type}")

        # Синхронизация изменений с ORM и сохранение в БД
        hopper_orm.strength = domain_hopper.strength
        hopper_orm.reactor_energy = domain_hopper.reactor_energy
        hopper_orm.location_state = domain_hopper.location_state
        hopper_orm.distance = domain_hopper.distance
        hopper_orm.best_distance = domain_hopper.best_distance
        hopper_orm.save()

        return hopper_orm
```

---

## 4. Представления и маршруты (HTTP/HTMX)

### 4.1. `apps/hopper/views.py`

```python
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .services import execute_hopper_action
from .domain.exceptions import TerraHopperError

@login_required
@require_POST
def hopper_action_view(request, hopper_id: int):
    action_type = request.POST.get("action_type")
    use_reactor = request.POST.get("use_reactor") == "true"

    try:
        updated_hopper = execute_hopper_action(
            hopper_id=hopper_id,
            user=request.user,
            action_type=action_type,
            use_reactor=use_reactor
        )
    except TerraHopperError as e:
        # При ошибке возвращаем сообщение об ошибке для HTMX-уведомления (тоста/блока ошибок)
        if request.headers.get("HX-Request"):
            return render(
                request,
                "hopper/partials/action_error.html",
                {"error_message": str(e)},
                status=400
            )
        return JsonResponse({"error": str(e)}, status=400)

    # При успешном выполнении возвращаем обновленный HTML-фрагмент карточки транспорта
    if request.headers.get("HX-Request"):
        return render(
            request,
            "hopper/partials/hopper_card.html",
            {"hopper": updated_hopper}
        )
    
    return JsonResponse({"status": "ok"})
```

### 4.2. `apps/hopper/urls.py`

```python
from django.urls import path
from . import views

app_name = "hopper"

urlpatterns = [
    path("<int:hopper_id>/action/", views.hopper_action_view, name="action"),
]
```

---

## 5. Сводная таблица правил, исключений и текстов ошибок

| Действие | Условие вызова | Формула расхода / Эффект | Проверяемые исключения и тексты ошибок |
|---|---|---|---|
| `basic_jump` | `location_state == "surface"` | `strength -= 3.0 + (mass / 100)`<br>`distance += 10.0` | 1. `InvalidLocationError`: *"Прыжок невозможен: транспорт находится под землей."*<br>2. `NotEnoughStrengthError`: *"Не достаточно силы для выполнения обычного прыжка."* |
| `long_jump` (без реактора) | `location_state == "surface"` | `strength -= 10.0 + (mass / 100) * 2`<br>`distance += 30.0` | 1. `InvalidLocationError`: *"Дальний прыжок невозможен: транспорт находится под землей."*<br>2. `NotEnoughStrengthError`: *"Недостаточно силы для выполнения дальнего прыжка."* |
| `long_jump` (с реактором) | `location_state == "surface"` | `strength -= 10.0 + (mass / 100) * 2`<br>`reactor_energy -= 50.0`<br>`distance += 45.0` | 1. `InvalidLocationError`: *"Дальний прыжок невозможен: транспорт находится под землей."*<br>2. `NotEnoughStrengthError`: *"Недостаточно силы для выполнения дальнего прыжка."*<br>3. `NotEnoughEnergyError`: *"Недостаточно энергии реактора для форсажа (требуется 50.0)."* |
| `go_underground` | `location_state == "surface"` | `strength -= 3.0 * (mass / 100)`<br>`location_state = "underground"` | 1. `InvalidLocationError`: *"Транспорт уже находится под землей."*<br>2. `NotEnoughStrengthError`: *"Недостаточно силы для погружения под землю."* |
| `return_to_surface` | `location_state == "underground"` | `strength -= 3.0 * (mass / 100)`<br>`location_state = "surface"` | 1. `InvalidLocationError`: *"Транспорт уже находится на поверхности."*<br>2. `NotEnoughStrengthError`: *"Недостаточно силы для возвращения на поверхность."* |
| `drill_forward` | `location_state == "underground"` | `strength -= 10.0 + (mass / 100) * 3`<br>`reactor_energy -= 50.0`<br>`distance += 40.0` | 1. `InvalidLocationError`: *"Подземное бурение невозможно на поверхности. Сначала погрузитесь."*<br>2. `NotEnoughStrengthError`: *"Недостаточно силы для подземного бурения."*<br>3. `NotEnoughEnergyError`: *"Недостаточно энергии реактора для запуска буров (требуется 50.0)."* |

---

## 6. Чек-лист проверки и Юнит-тесты

### 6.1. Чек-лист проверки
1. [ ] Класс `TerraHopper` и доменные исключения реализованы в `apps/hopper/domain/`.
2. [ ] Вызовы методов `basic_jump`, `long_jump`, `go_underground`, `return_to_surface`, `drill_forward` вызывают `_check_and_update_recovery` и корректно обновляют `best_distance`.
3. [ ] Функция `execute_hopper_action` выполняет блокировку записи (`select_for_update`) в рамках `transaction.atomic()`.
4. [ ] Обработка POST-запроса на `/hopper/<id>/action/` возвращает `400 Bad Request` со строчным описанием ошибки из ТЗ при недопустимом действии.
5. [ ] Написан комплекс юнит-тестов в `apps/hopper/tests/test_actions.py`.

### 6.2. Модуль юнит-тестов (`apps/hopper/tests/test_actions.py`)

```python
import pytest
from django.contrib.auth import get_user_model
from apps.hopper.models import Hopper
from apps.hopper.services import execute_hopper_action
from apps.hopper.domain.exceptions import (
    InvalidLocationError,
    NotEnoughStrengthError,
    NotEnoughEnergyError,
)

User = get_user_model()

@pytest.mark.django_db
class TestHopperActionsBackend:

    def setup_method(self):
        self.user = User.objects.create_user(username="testdriver", password="password")
        self.hopper = Hopper.objects.create(
            user=self.user,
            name="Крот-1",
            mass_kg=200.0,
            strength=100.0,
            reactor_energy=100.0,
            location_state="surface",
            distance=0.0,
            best_distance=0.0,
        )

    def test_basic_jump_success(self):
        # Arrange & Act
        updated = execute_hopper_action(self.hopper.id, self.user, "basic_jump")
        
        # Assert
        assert updated.distance == 10.0
        assert updated.strength == 95.0
        assert updated.best_distance == 10.0

    def test_long_jump_with_reactor_success(self):
        # Act
        updated = execute_hopper_action(self.hopper.id, self.user, "long_jump", use_reactor=True)
        
        # Assert
        assert updated.distance == 45.0
        assert updated.strength == 86.0
        assert updated.reactor_energy == 50.0
        assert updated.best_distance == 45.0

    def test_drill_forward_on_surface_raises_error(self):
        # Act & Assert
        with pytest.raises(InvalidLocationError) as exc_info:
            execute_hopper_action(self.hopper.id, self.user, "drill_forward")
        assert "Подземное бурение невозможно на поверхности" in str(exc_info.value)

    def test_not_enough_energy_for_reactor_jump(self):
        # Arrange
        self.hopper.reactor_energy = 30.0
        self.hopper.save()

        # Act & Assert
        with pytest.raises(NotEnoughEnergyError) as exc_info:
            execute_hopper_action(self.hopper.id, self.user, "long_jump", use_reactor=True)
        assert "Недостаточно энергии реактора для форсажа" in str(exc_info.value)
```