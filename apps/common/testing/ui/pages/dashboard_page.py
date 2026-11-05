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
        self.garage_list = self.find_by_css(
            selector="#garage-list",
            description="Список транспорта",
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
