from django.urls import reverse

from apps.common.testing.ui.base_element import BaseElement
from apps.common.testing.ui.base_page import BasePage


class DashboardPage(BasePage):
    """Дашборд с гаражом и турнирной таблицей."""

    def __init__(self, page, base_url: str):
        super().__init__(
            page=page,
            base_url=base_url,
            path=reverse("hopper:dashboard"),
        )
        self.title = self.find_by_role(
            role="heading",
            name="Гараж",
            description="Заголовок гаража",
        )
        self.logout_link = self.find_by_role(
            role="link",
            name="Выйти",
            description="Ссылка выхода из аккаунта",
        )
        self.garage_list = self.find_by_css(
            selector="#garage-list",
            description="Список транспорта",
        )
        self.leaderboard = self.find_by_css(
            selector="#leaderboard",
            description="Турнирная таблица",
        )
        self.create_hopper_button = self.find_by_role(
            role="button",
            name="+ Создать транспорт",
            description="Кнопка создания транспорта",
        )
        self.modal_name_input = self.find_by_css(
            selector="#modal input[name='name']",
            description="Поле имени транспорта",
        )
        self.modal_mass_input = self.find_by_css(
            selector="#modal input[name='mass_kg']",
            description="Поле массы транспорта",
        )
        self.modal_submit_button = self.find_by_css(
            selector="#modal button[type='submit']",
            description="Кнопка создания в модальном окне",
        )

    def hopper_card(self, hopper_name: str) -> BaseElement:
        locator = self.page.locator("#garage-list > div").filter(
            has=self.page.get_by_role(
                role="heading",
                name=hopper_name,
                exact=True,
            ),
        )
        return BaseElement(
            locator=locator,
            description=f"Карточка транспорта {hopper_name}",
        )

    def start_race_button(self, hopper_name: str) -> BaseElement:
        card = self.hopper_card(hopper_name=hopper_name)
        return BaseElement(
            locator=card.locator.get_by_role("link", name="Запустить заезд"),
            description=f"Кнопка запуска заезда для {hopper_name}",
        )

    def assert_hopper_visible(self, hopper_name: str) -> None:
        self.hopper_card(hopper_name=hopper_name).assert_visible()

    def assert_hopper_missing(self, hopper_name: str) -> None:
        self.hopper_card(hopper_name=hopper_name).assert_count(expected_count=0)

    def leaderboard_row(self, username: str, hopper_name: str) -> BaseElement:
        locator = (
            self.leaderboard.locator.get_by_role("row")
            .filter(has_text=username)
            .filter(has_text=hopper_name)
        )
        return BaseElement(
            locator=locator,
            description=f"Строка турнирной таблицы {username} / {hopper_name}",
        )

    def assert_leaderboard_entry(
        self,
        username: str,
        hopper_name: str,
        expected_record: str,
    ) -> None:
        row = self.leaderboard_row(username=username, hopper_name=hopper_name)
        row.assert_visible()
        row.assert_contains_text(expected_text=expected_record)
