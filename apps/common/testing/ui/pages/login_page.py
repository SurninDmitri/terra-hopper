from django.urls import reverse

from apps.common.testing.ui.base_page import BasePage


class LoginPage(BasePage):
    """Страница входа в приложение."""

    def __init__(self, page, base_url: str):
        super().__init__(
            page=page,
            base_url=base_url,
            path=reverse("login"),
        )
        self.username_input = self.find_by_css(
            selector="input[name='username']",
            description="Поле имени пользователя",
        )
        self.password_input = self.find_by_css(
            selector="input[name='password']",
            description="Поле пароля",
        )
        self.submit_button = self.find_by_role(
            role="button",
            name="Войти",
            description="Кнопка входа",
        )
