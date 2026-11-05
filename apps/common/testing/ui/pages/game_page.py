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
