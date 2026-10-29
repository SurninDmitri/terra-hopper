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
