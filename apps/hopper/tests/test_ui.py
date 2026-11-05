from apps.common.testing.constants import HopperData
from apps.common.testing.steps import Steps
from apps.common.testing.ui.test_case import ServiceUserUiTestCase


class HopperGameUiTest(ServiceUserUiTestCase):
    def setUp(self):
        super().setUp()
        self.hopper = Steps.create_hopper(
            user=self.service_user,
            name=HopperData.DEFAULT_NAME,
            mass_kg=HopperData.DEFAULT_MASS_KG,
        )

    def test_basic_jump_from_game_screen(self):
        """UI_P_3 Проверяет обычный прыжок через игровой интерфейс."""
        # Arrange
        Steps.step(message="Готовим пользователя и хоппера для UI-теста")

        # Act
        Steps.step(message="Авторизуемся через форму входа")
        self.login_as_service_user()

        Steps.step(message="Запускаем заезд с дашборда")
        self.ui.start_race(hopper_name=self.hopper.name)

        Steps.step(message="Выполняем обычный прыжок")
        self.ui.perform_basic_jump()

        # Assert
        Steps.step(message="Проверяем дистанцию и рекорд в HUD")
        self.ui.assert_distance(expected_distance="10.0")
        self.ui.assert_record(expected_record="10.0")
