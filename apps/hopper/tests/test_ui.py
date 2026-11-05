from apps.common.testing.steps import Steps
from apps.common.testing.ui.test_case import PlaywrightLiveServerTestCase


class HopperGameUiTest(PlaywrightLiveServerTestCase):
    def setUp(self):
        super().setUp()
        self.user = Steps.create_user(
            username="ui-driver",
            password="StrongPass123",
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name="Крот-UI",
            mass_kg=200.0,
        )

    def test_basic_jump_from_game_screen(self):
        """Проверяет обычный прыжок через игровой интерфейс.

        Предусловия:
            Пользователь ui-driver и хоппер Крот-UI созданы в тестовой БД.
        Шаги:
            1. Войти в приложение через форму входа.
            2. Запустить заезд с дашборда.
            3. Нажать кнопку обычного прыжка.
        Ожидаемый результат:
            В HUD отображается дистанция 10.0 м и рекорд 10.0 м.
        """
        # Arrange
        Steps.step(message="Готовим пользователя и хоппера для UI-теста")

        # Act
        Steps.step(message="Авторизуемся через форму входа")
        self.ui.login(
            username="ui-driver",
            password="StrongPass123",
        )

        Steps.step(message="Запускаем заезд с дашборда")
        self.ui.start_race(hopper_name=self.hopper.name)

        Steps.step(message="Выполняем обычный прыжок")
        self.ui.perform_basic_jump()

        # Assert
        Steps.step(message="Проверяем дистанцию и рекорд в HUD")
        self.ui.assert_distance(expected_distance="10.0")
        self.ui.assert_record(expected_record="10.0")
