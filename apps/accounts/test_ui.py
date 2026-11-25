from unittest import skip

from apps.common.testing.constants import Passwords
from apps.common.testing.steps import Steps
from apps.common.testing.ui.test_case import PlaywrightLiveServerTestCase, ServiceUserUiTestCase


@skip("UI-тесты отключены по запросу пользователя")
class RegistrationUiTest(PlaywrightLiveServerTestCase):
    # region === Позитивные сценарии ===

    def test_register_via_ui_opens_dashboard(self):
        """UI_P_1 Проверяет регистрацию пользователя через UI."""
        # Arrange
        Steps.step(message="Готовим данные для регистрации через UI")
        username = "ui-register"

        # Act
        Steps.step(message="Регистрируем пользователя через форму")
        self.ui.register(username=username,
                         password=Passwords.STRONG,
                         password_confirm=Passwords.STRONG)

        # Assert
        Steps.step(message="Проверяем, что открылся дашборд")
        self.ui.assert_dashboard_url()

    # endregion


@skip("UI-тесты отключены по запросу пользователя")
class LogoutLoginUiTest(ServiceUserUiTestCase):
    def setUp(self):
        super().setUp()
        Steps.step(message="Авторизуемся под сервисной учёткой")
        self.login_as_service_user()

    # region === Позитивные сценарии ===

    def test_logout_and_login_again_opens_dashboard(self):
        """UI_P_2 Проверяет выход из аккаунта и повторный вход."""
        # Arrange
        Steps.step(message="Используем авторизованную сервисную учётку")

        # Act
        Steps.step(message="Выходим из аккаунта и входим заново")
        self.ui.logout()
        self.login_as_service_user()

        # Assert
        Steps.step(message="Проверяем, что открылся дашборд")
        self.ui.assert_dashboard_url()

    # endregion
