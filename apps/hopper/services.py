from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Hopper
from .domain.terra_hopper import TerraHopper


def start_race(hopper_id: int, user) -> Hopper:
    """
    Запускает новый заезд: сбрасывает сессию, сохраняя рекорд (best_distance).
    """
    with transaction.atomic():
        hopper_orm = get_object_or_404(
            Hopper.objects.select_for_update(),
            id=hopper_id,
            user=user
        )
        hopper_orm.distance = 0.0
        hopper_orm.strength = 100.0
        hopper_orm.reactor_energy = 100.0
        hopper_orm.location_state = "surface"
        hopper_orm.save()
        return hopper_orm


def compute_action_availability(hopper: Hopper) -> dict:
    """
    Динамическая блокировка кнопок: считается на бэкенде на основе
    location_state, strength и reactor_energy транспорта.
    """
    mass = hopper.mass_kg
    surface = hopper.location_state == "surface"
    underground = hopper.location_state == "underground"

    return {
        "basic_jump": (
            surface
            and hopper.strength >= 3.0 + mass / 100.0
        ),
        "long_jump": (
            surface
            and hopper.strength >= 10.0 + (mass / 100.0) * 2.0
        ),
        "long_reactor": (
            surface
            and hopper.strength >= 10.0 + (mass / 100.0) * 2.0
            and hopper.reactor_energy >= 50.0
        ),
        "go_underground": (
            surface
            and hopper.strength >= 3.0 * (mass / 100.0)
        ),
        "return_to_surface": (
            underground
            and hopper.strength >= 3.0 * (mass / 100.0)
        ),
        "drill_forward": (
            underground
            and hopper.strength >= 10.0 + (mass / 100.0) * 3.0
            and hopper.reactor_energy >= 50.0
        ),
    }


def is_game_over(hopper: Hopper) -> bool:
    """
    Игра окончена, если не выполнено ни одно действие:
    транспорт не может потратить ни силы, ни энергию ни на что.
    """
    return not any(compute_action_availability(hopper).values())


def create_hopper_for_user(user, name: str, mass_kg: float) -> Hopper:
    clean_name = name.strip() if name else ""
    if not clean_name:
        raise ValueError("Имя не может быть пустым.")

    try:
        mass_val = float(mass_kg)
    except (ValueError, TypeError):
        raise ValueError("Масса должна быть числом.")

    if not (100.0 <= mass_val <= 500.0):
        raise ValueError("Масса должна быть в диапазоне 100.0…500.0 кг.")

    return Hopper.objects.create(
        user=user,
        name=clean_name,
        mass_kg=mass_val,
        strength=100.0,
        reactor_energy=100.0,
        location_state="surface",
        distance=0.0,
        best_distance=0.0,
    )


def execute_hopper_action(hopper_id: int, user, action_type: str, use_reactor: bool = False) -> Hopper:
    with transaction.atomic():
        hopper_orm = get_object_or_404(
            Hopper.objects.select_for_update(),
            id=hopper_id,
            user=user
        )

        domain_hopper = TerraHopper(
            name=hopper_orm.name,
            mass_kg=hopper_orm.mass_kg,
            strength=hopper_orm.strength,
            reactor_energy=hopper_orm.reactor_energy,
            location_state=hopper_orm.location_state,
            distance=hopper_orm.distance,
            best_distance=hopper_orm.best_distance,
        )

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

        hopper_orm.strength = domain_hopper.strength
        hopper_orm.reactor_energy = domain_hopper.reactor_energy
        hopper_orm.location_state = domain_hopper.location_state
        hopper_orm.distance = domain_hopper.distance
        hopper_orm.best_distance = domain_hopper.best_distance
        hopper_orm.save()

        return hopper_orm
