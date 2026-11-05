from __future__ import annotations

from django.urls import reverse
from playwright.sync_api import Page

from apps.common.testing.steps import logged_method
from apps.common.testing.ui.pages import (
    DashboardPage,
    GamePage,
    LoginPage,
    RegisterPage,
)


class StepsUI:
    """Фасад для UI-действий автотестов."""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.login_page = LoginPage(page=page, base_url=base_url)
        self.dashboard_page = DashboardPage(page=page, base_url=base_url)
        self.game_page = GamePage(page=page, base_url=base_url)
        self.register_page = RegisterPage(page=page, base_url=base_url)

    @logged_method
    def login(self, username: str, password: str) -> None:
        self.login_page.open()
        self.login_page.username_input.fill(text=username)
        self.login_page.password_input.fill(text=password)
        self.login_page.submit_button.click()
        self.dashboard_page.title.assert_visible()

    @logged_method
    def open_register(self) -> None:
        self.register_page.open()

    @logged_method
    def register(
        self,
        username: str,
        password: str,
        password_confirm: str,
    ) -> None:
        self.open_register()
        self.register_page.username_input.fill(text=username)
        self.register_page.password_input.fill(text=password)
        self.register_page.password_confirm_input.fill(text=password_confirm)
        self.register_page.submit_button.click()

    @logged_method
    def logout(self) -> None:
        self.dashboard_page.logout_link.click()
        self.assert_login_url()

    @logged_method
    def open_dashboard(self) -> None:
        self.dashboard_page.open()
        self.dashboard_page.title.assert_visible()

    @logged_method
    def create_hopper(self, name: str, mass_kg: float) -> None:
        self._wait_for_htmx()
        self.dashboard_page.create_hopper_button.click()
        self.dashboard_page.modal_name_input.fill(text=name)
        self.dashboard_page.modal_mass_input.fill(text=str(mass_kg))
        self.dashboard_page.modal_submit_button.click()
        self.dashboard_page.assert_hopper_visible(hopper_name=name)

    @logged_method
    def start_race(self, hopper_name: str) -> None:
        self.dashboard_page.start_race_button(hopper_name=hopper_name).click()
        self.game_page.game_panel.assert_visible()

    @logged_method
    def open_game(self, hopper_id: int) -> None:
        self.game_page.open(hopper_id=hopper_id)
        self.game_page.game_panel.assert_visible()

    def _wait_for_htmx(self) -> None:
        self.page.wait_for_function("() => window.htmx !== undefined")

    @logged_method
    def perform_basic_jump(self) -> None:
        self._wait_for_htmx()
        self.game_page.basic_jump_button.click()

    @logged_method
    def perform_long_jump(self) -> None:
        self._wait_for_htmx()
        self.game_page.long_jump_button.click()

    @logged_method
    def perform_reactor_jump(self) -> None:
        self._wait_for_htmx()
        self.game_page.reactor_jump_button.click()

    @logged_method
    def go_underground(self) -> None:
        self._wait_for_htmx()
        self.game_page.go_underground_button.click()

    @logged_method
    def return_to_surface(self) -> None:
        self._wait_for_htmx()
        self.game_page.return_to_surface_button.click()

    @logged_method
    def drill_forward(self) -> None:
        self._wait_for_htmx()
        self.game_page.drill_forward_button.click()

    @logged_method
    def assert_distance(self, expected_distance: str) -> None:
        self.game_page.assert_distance(expected_distance=expected_distance)

    @logged_method
    def assert_record(self, expected_record: str) -> None:
        self.game_page.assert_record(expected_record=expected_record)

    @logged_method
    def assert_on_dashboard(self) -> None:
        self.dashboard_page.title.assert_visible()

    @logged_method
    def assert_dashboard_url(self) -> None:
        self.dashboard_page.assert_url_contains(
            expected=reverse("hopper:dashboard"),
        )

    @logged_method
    def assert_login_url(self) -> None:
        self.login_page.assert_url_contains(
            expected=reverse("login"),
        )

    @logged_method
    def assert_on_game_screen(self) -> None:
        self.game_page.game_panel.assert_visible()
