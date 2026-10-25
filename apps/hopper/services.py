from .models import Hopper


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
