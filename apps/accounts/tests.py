from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apps.common.testing.steps import Steps


class AccountsViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    # region === Позитивные сценарии ===

    def test_register_success_sets_jwt_cookies_and_redirects(self):
        """Проверяет успешную регистрацию и установку JWT-cookie.

        Предусловия:
            Пользователь с именем newuser отсутствует.
        Шаги:
            1. Отправить форму регистрации с корректными данными.
        Ожидаемый результат:
            Пользователь создан, выполнен редирект на дашборд,
            access_token и refresh_token установлены как HttpOnly.
        """
        # Arrange
        Steps.step(message="Готовим данные для регистрации")

        # Act
        Steps.step(message="Регистрируем нового пользователя")
        response = Steps.register(
            client=self.client,
            username="newuser",
            password="StrongPass123",
            password_confirm="StrongPass123",
        )

        # Assert
        Steps.step(message="Проверяем редирект, пользователя и JWT-cookie")
        self.assertRedirects(
            response=response,
            expected_url=reverse("hopper:dashboard"),
        )
        self.assertTrue(
            User.objects.filter(username="newuser").exists(),
        )

        access_token = response.cookies.get("access_token")
        refresh_token = response.cookies.get("refresh_token")
        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)
        self.assertTrue(access_token["httponly"])
        self.assertEqual(first=access_token["samesite"], second="Lax")
        self.assertTrue(refresh_token["httponly"])

    def test_login_success_sets_jwt_cookies_and_redirects(self):
        """Проверяет успешный вход и установку JWT-cookie.

        Предусловия:
            Пользователь driver существует.
        Шаги:
            1. Отправить форму входа с корректным паролем.
        Ожидаемый результат:
            Выполнен редирект на дашборд, JWT-cookie установлены.
        """
        # Arrange
        Steps.step(message="Создаём пользователя driver")
        Steps.create_user(username="driver", password="StrongPass123")

        # Act
        Steps.step(message="Входим под пользователем driver")
        response = Steps.login_user(
            client=self.client,
            username="driver",
            password="StrongPass123",
        )

        # Assert
        Steps.step(message="Проверяем редирект и JWT-cookie")
        self.assertRedirects(
            response=response,
            expected_url=reverse("hopper:dashboard"),
        )
        self.assertIsNotNone(response.cookies.get("access_token"))
        self.assertIsNotNone(response.cookies.get("refresh_token"))

    def test_logout_deletes_cookies_and_redirects(self):
        """Проверяет выход из аккаунта и удаление JWT-cookie.

        Предусловия:
            Пользователь driver вошёл в систему.
        Шаги:
            1. Выполнить выход.
        Ожидаемый результат:
            Редирект на страницу входа, cookie очищены.
        """
        # Arrange
        Steps.step(message="Создаём и авторизуем пользователя driver")
        Steps.create_user(username="driver", password="StrongPass123")
        Steps.login_user(
            client=self.client,
            username="driver",
            password="StrongPass123",
        )

        # Act
        Steps.step(message="Выполняем выход")
        response = Steps.logout_user(client=self.client)

        # Assert
        Steps.step(message="Проверяем редирект и очистку cookie")
        self.assertRedirects(
            response=response,
            expected_url=reverse("login"),
        )
        self.assertEqual(first=response.cookies["access_token"].value, second="")
        self.assertEqual(first=response.cookies["refresh_token"].value, second="")

    def test_index_redirects_to_login_when_anonymous(self):
        """Проверяет редирект анонимного пользователя на страницу входа.

        Предусловия:
            Пользователь не авторизован.
        Шаги:
            1. Открыть главную страницу.
        Ожидаемый результат:
            Редирект на страницу входа.
        """
        # Arrange
        Steps.step(message="Проверяем, что пользователь анонимен")

        # Act
        Steps.step(message="Открываем главную страницу")
        response = Steps.get_index(client=self.client)

        # Assert
        Steps.step(message="Проверяем редирект на страницу входа")
        self.assertRedirects(
            response=response,
            expected_url=reverse("login"),
        )

    def test_index_redirects_to_dashboard_when_authenticated(self):
        """Проверяет редирект авторизованного пользователя на дашборд.

        Предусловия:
            Пользователь driver авторизован.
        Шаги:
            1. Открыть главную страницу.
        Ожидаемый результат:
            Редирект на дашборд.
        """
        # Arrange
        Steps.step(message="Создаём и авторизуем пользователя driver")
        Steps.create_user(username="driver", password="StrongPass123")
        Steps.login(
            client=self.client,
            username="driver",
            password="StrongPass123",
        )

        # Act
        Steps.step(message="Открываем главную страницу")
        response = Steps.get_index(client=self.client)

        # Assert
        Steps.step(message="Проверяем редирект на дашборд")
        self.assertRedirects(
            response=response,
            expected_url=reverse("hopper:dashboard"),
        )

    # endregion

    # region === Негативные сценарии ===

    def test_register_password_mismatch_shows_error(self):
        """Проверяет ошибку регистрации при несовпадении паролей.

        Предусловия:
            Пользователь с именем newuser отсутствует.
        Шаги:
            1. Отправить форму с разными паролями.
        Ожидаемый результат:
            Статус 200, показана ошибка, пользователь не создан.
        """
        # Arrange
        Steps.step(message="Готовим данные с несовпадающими паролями")

        # Act
        Steps.step(message="Пытаемся зарегистрировать пользователя")
        response = Steps.register(
            client=self.client,
            username="newuser",
            password="StrongPass123",
            password_confirm="OtherPass456",
        )

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие пользователя")
        self.assertEqual(first=response.status_code, second=200)
        self.assertContains(
            response=response,
            text="Пароли не совпадают",
        )
        self.assertFalse(
            User.objects.filter(username="newuser").exists(),
        )

    def test_register_duplicate_username_shows_error(self):
        """Проверяет ошибку регистрации при занятом имени пользователя.

        Предусловия:
            Пользователь taken уже существует.
        Шаги:
            1. Попытаться зарегистрировать пользователя с именем taken.
        Ожидаемый результат:
            Статус 200, показано сообщение о существующем пользователе.
        """
        # Arrange
        Steps.step(message="Создаём пользователя taken")
        Steps.create_user(username="taken", password="StrongPass123")

        # Act
        Steps.step(message="Пытаемся зарегистрировать повторное имя")
        response = Steps.register(
            client=self.client,
            username="taken",
            password="StrongPass123",
            password_confirm="StrongPass123",
        )

        # Assert
        Steps.step(message="Проверяем сообщение об ошибке")
        self.assertEqual(first=response.status_code, second=200)
        self.assertContains(
            response=response,
            text="уже существует",
        )

    def test_login_wrong_password_shows_error(self):
        """Проверяет ошибку входа при неверном пароле.

        Предусловия:
            Пользователь driver существует.
        Шаги:
            1. Отправить форму входа с неверным паролем.
        Ожидаемый результат:
            Статус 200, форма содержит ошибки.
        """
        # Arrange
        Steps.step(message="Создаём пользователя driver")
        Steps.create_user(username="driver", password="StrongPass123")

        # Act
        Steps.step(message="Пытаемся войти с неверным паролем")
        response = Steps.login_user(
            client=self.client,
            username="driver",
            password="wrong",
        )

        # Assert
        Steps.step(message="Проверяем ошибки формы")
        self.assertEqual(first=response.status_code, second=200)
        self.assertIn(member="form", container=response.context)
        self.assertTrue(response.context["form"].errors)

    # endregion


class JWTMiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Steps.create_user(
            username="driver",
            password="StrongPass123",
        )

    def test_access_token_in_cookie_authenticates_request(self):
        """Проверяет аутентификацию запроса по access_token в cookie.

        Предусловия:
            Пользователь driver существует.
        Шаги:
            1. Выполнить запрос с access_token в cookie.
        Ожидаемый результат:
            Пользователь распознан, редирект на дашборд.
        """
        # Arrange
        Steps.step(message="Создаём access_token для пользователя")
        access_token = Steps.create_access_token(user=self.user)

        # Act
        Steps.step(message="Открываем главную страницу с токеном в cookie")
        response = Steps.get_index(
            client=self.client,
            HTTP_COOKIE=f"access_token={access_token}",
        )

        # Assert
        Steps.step(message="Проверяем редирект на дашборд")
        self.assertRedirects(
            response=response,
            expected_url=reverse("hopper:dashboard"),
        )
