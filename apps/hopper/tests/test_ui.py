from unittest import skip

from apps.common.testing.constants import HopperData, Passwords
from apps.common.testing.steps import Steps
from apps.common.testing.ui.test_case import HopperGameUiTestCase, ServiceUserUiTestCase


@skip("UI-тесты отключены по запросу пользователя")
class HopperGameUiTest(HopperGameUiTestCase):
    # region === Позитивные сценарии ===

    def test_basic_jump_from_game_screen(self):
        """UI_P_3 Проверяет обычный прыжок через игровой интерфейс."""
        # Arrange
        Steps.step(message="Используем подготовленного хоппера в запущенном заезде")

        # Act
        Steps.step(message="Выполняем обычный прыжок")
        self.ui.perform_basic_jump()

        # Assert
        Steps.step(message="Проверяем дистанцию и рекорд в HUD")
        self.ui.assert_distance(expected_distance="10.0")
        self.ui.assert_record(expected_record="10.0")

    def test_long_jump_from_game_screen(self):
        """UI_P_4 Проверяет дальний прыжок через игровой интерфейс."""
        # Arrange
        Steps.step(message="Используем подготовленный игровой экран")

        # Act
        Steps.step(message="Выполняем дальний прыжок")
        self.ui.perform_long_jump()

        # Assert
        Steps.step(message="Проверяем дистанцию и рекорд в HUD")
        self.ui.assert_distance(expected_distance="30.0")
        self.ui.assert_record(expected_record="30.0")

    def test_reactor_jump_from_game_screen(self):
        """UI_P_5 Проверяет форсаж реактора через игровой интерфейс."""
        # Arrange
        Steps.step(message="Используем подготовленный игровой экран")

        # Act
        Steps.step(message="Выполняем прыжок с форсажем реактора")
        self.ui.perform_reactor_jump()

        # Assert
        Steps.step(message="Проверяем дистанцию, рекорд и энергию реактора")
        self.ui.assert_distance(expected_distance="45.0")
        self.ui.assert_record(expected_record="45.0")
        self.ui.assert_reactor_energy(expected_energy="50,0%")

    def test_record_updates_after_new_maximum(self):
        """UI_P_6 Проверяет обновление рекорда после прыжков."""
        # Arrange
        Steps.step(message="Используем подготовленный игровой экран")

        # Act
        Steps.step(message="Выполняем обычный и дальний прыжки")
        self.ui.perform_basic_jump()
        self.ui.perform_long_jump()

        # Assert
        Steps.step(message="Проверяем обновлённый рекорд")
        self.ui.assert_distance(expected_distance="40.0")
        self.ui.assert_record(expected_record="40.0")
        self.ui.assert_panel_distance(expected_distance="Дистанция: 40,0 м")

    def test_underground_actions_cycle(self):
        """UI_P_7 Проверяет погружение, бурение и возврат на поверхность."""
        # Arrange
        Steps.step(message="Используем подготовленный игровой экран")

        # Act
        Steps.step(message="Погружаемся под землю")
        self.ui.go_underground()

        Steps.step(message="Бурим вперёд")
        self.ui.drill_forward()

        Steps.step(message="Возвращаемся на поверхность")
        self.ui.return_to_surface()

        # Assert
        Steps.step(message="Проверяем положение, дистанцию и рекорд")
        self.ui.assert_location(expected_location="На поверхности")
        self.ui.assert_distance(expected_distance="40.0")
        self.ui.assert_record(expected_record="40.0")

    # endregion


@skip("UI-тесты отключены по запросу пользователя")
class HopperLeaderboardUiTest(ServiceUserUiTestCase):
    def setUp(self):
        super().setUp()
        Steps.step(message="Создаём соперника с минимальным рекордом")
        self.rival = Steps.create_user(username="rival-driver",
                                       password=Passwords.STRONG)
        self.rival_hopper = Steps.create_hopper(user=self.rival,
                                                name="Крот-соперник",
                                                mass_kg=HopperData.DEFAULT_MASS_KG,
                                                distance=10.0,
                                                best_distance=10.0,
                                                strength=95.0)

    # region === Позитивные сценарии ===

    def test_leaderboard_shows_other_user_record(self):
        """UI_P_8 Проверяет рекорд другого пользователя в турнирной таблице."""
        # Arrange
        Steps.step(message="Рекорд другого пользователя уже создан")

        # Act
        Steps.step(message="Входим под сервисной учёткой")
        self.login_as_service_user()

        # Assert
        Steps.step(message="Проверяем строку другого пользователя")
        self.ui.assert_leaderboard_entry(username=self.rival.username,
                                         hopper_name=self.rival_hopper.name,
                                         expected_record="10,0 м")

    # endregion


@skip("UI-тесты отключены по запросу пользователя")
class HopperGameOverUiTest(HopperGameUiTestCase):
    hopper_name = "Тяжеловес"
    hopper_mass_kg = 500.0

    def setUp(self):
        super().setUp()
        Steps.step(message="Тратим силу на четыре дальних прыжка")
        for _ in range(4):
            self.ui.perform_long_jump()

    # region === Негативные сценарии ===

    def test_game_over_modal_appears_when_strength_exhausted(self):
        """UI_N_1 Проверяет окно окончания сил и возврат в гараж."""
        # Arrange
        Steps.step(message="Используем заезд после четырёх дальних прыжков")

        # Act
        Steps.step(message="Выполняем обычные прыжки до исчерпания сил")
        self.ui.perform_basic_jumps_until_disabled(max_attempts=10)

        Steps.step(message="Проверяем окно окончания игры и блокировку кнопки")
        self.ui.assert_game_over()
        self.ui.assert_basic_jump_disabled()

        Steps.step(message="Возвращаемся в гараж по ссылке из окна")
        self.ui.return_to_garage_from_game_over()

        # Assert
        Steps.step(message="Проверяем возврат на дашборд")
        self.ui.assert_dashboard_url()
        self.ui.assert_on_dashboard()

    def test_long_jump_disabled_when_strength_low(self):
        """UI_N_2 Проверяет блокировку дальнего прыжка при нехватке силы."""
        # Arrange
        Steps.step(message="Используем заезд после четырёх дальних прыжков")

        # Act
        Steps.step(message="Выполняем обычные прыжки до низкой силы")
        for _ in range(3):
            self.ui.perform_basic_jump()

        # Assert
        Steps.step(message="Проверяем, что дальний прыжок заблокирован")
        self.ui.assert_strength(expected_strength="16,0%")
        self.ui.assert_basic_jump_enabled()
        self.ui.assert_long_jump_disabled()

    # endregion
