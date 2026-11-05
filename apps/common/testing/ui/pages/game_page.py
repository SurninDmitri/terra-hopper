from django.urls import reverse

from apps.common.testing.ui.base_page import BasePage


class GamePage(BasePage):
    """Игровой экран с картой, HUD и панелью действий."""

    def __init__(self, page, base_url: str):
        super().__init__(page=page, base_url=base_url)
        self.game_panel = self.find_by_css(
            selector="#game-panel",
            description="Панель состояния и управления",
        )
        self.distance_value = self.find_by_css(
            selector="#hud-distance",
            description="Значение дистанции в HUD",
        )
        self.record_value = self.find_by_css(
            selector="#hud-record",
            description="Значение рекорда в HUD",
        )
        self.strength_value = self.find_by_css(
            selector="#panel-strength-value",
            description="Значение силы в панели состояния",
        )
        self.reactor_energy_value = self.find_by_css(
            selector="#panel-reactor-energy-value",
            description="Значение энергии реактора в панели состояния",
        )
        self.location_value = self.find_by_css(
            selector="#panel-location",
            description="Положение хоппера в панели состояния",
        )
        self.panel_distance_value = self.find_by_css(
            selector="#panel-distance",
            description="Дистанция в панели состояния",
        )
        self.back_to_garage_link = self.find_by_role(
            role="link",
            name="Назад в гараж",
            description="Ссылка возврата в гараж",
        )
        self.game_over_modal = self.find_by_css(
            selector="#game-over-modal",
            description="Модальное окно окончания игры",
        )
        self.return_to_garage_link = self.find_by_role(
            role="link",
            name="Вернуться в гараж",
            description="Ссылка возврата в гараж из окна окончания игры",
        )
        self.basic_jump_button = self.find_by_role(
            role="button",
            name="Обычный прыжок (+10м)",
            description="Кнопка обычного прыжка",
        )
        self.long_jump_button = self.find_by_role(
            role="button",
            name="Дальний прыжок (+30м)",
            description="Кнопка дальнего прыжка",
        )
        self.reactor_jump_button = self.find_by_role(
            role="button",
            name="Форсаж реактора (+45м)",
            description="Кнопка форсажа реактора",
        )
        self.go_underground_button = self.find_by_role(
            role="button",
            name="Погружение под землю",
            description="Кнопка погружения",
        )
        self.return_to_surface_button = self.find_by_role(
            role="button",
            name="Выйти на поверхность",
            description="Кнопка возврата на поверхность",
        )
        self.drill_forward_button = self.find_by_role(
            role="button",
            name="Подземное бурение (+40м)",
            description="Кнопка бурения",
        )

    def open(self, hopper_id: int) -> None:
        self.page.goto(
            url=f"{self.base_url}{reverse('hopper:game', args=[hopper_id])}",
            wait_until="domcontentloaded",
        )

    def assert_distance(self, expected_distance: str) -> None:
        self.distance_value.assert_text(expected_text=expected_distance)

    def assert_record(self, expected_record: str) -> None:
        self.record_value.assert_text(expected_text=expected_record)

    def assert_strength(self, expected_strength: str) -> None:
        self.strength_value.assert_text(expected_text=expected_strength)

    def assert_reactor_energy(self, expected_energy: str) -> None:
        self.reactor_energy_value.assert_text(expected_text=expected_energy)

    def assert_location(self, expected_location: str) -> None:
        self.location_value.assert_contains_text(expected_text=expected_location)

    def assert_panel_distance(self, expected_distance: str) -> None:
        self.panel_distance_value.assert_contains_text(
            expected_text=expected_distance,
        )

    def assert_basic_jump_enabled(self) -> None:
        self.basic_jump_button.assert_enabled()

    def assert_basic_jump_disabled(self) -> None:
        self.basic_jump_button.assert_disabled()

    def assert_long_jump_disabled(self) -> None:
        self.long_jump_button.assert_disabled()

    def assert_game_over(self) -> None:
        self.game_over_modal.assert_visible()
        self.game_over_modal.assert_contains_text(expected_text="Игра окончена")
        self.game_over_modal.assert_contains_text(
            expected_text="Силы транспорта исчерпаны",
        )
        self.return_to_garage_link.assert_visible()
