from django.http import Http404
from django.test import Client, TestCase
from django.urls import reverse

from apps.common.testing.constants import HopperData, HttpStatus, Passwords, Users
from apps.common.testing.steps import Steps
from apps.hopper.domain.exceptions import (
    InvalidLocationError,
    NotEnoughEnergyError,
    NotEnoughStrengthError,
)


class HopperActionsServiceTest(TestCase):
    def setUp(self):
        self.user = Steps.create_user(
            username=Users.TEST_DRIVER,
            password=Passwords.DEFAULT,
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name=HopperData.DEFAULT_NAME,
            mass_kg=HopperData.DEFAULT_MASS_KG,
        )

    # region === Позитивные сценарии ===

    def test_basic_jump_success(self):
        """BE_P_6 Проверяет обычный прыжок на поверхности."""
        # Arrange
        Steps.step(message="Хоппер готов к обычному прыжку")

        # Act
        Steps.step(message="Выполняем обычный прыжок")
        updated_hopper = Steps.perform_action(
            hopper_id=self.hopper.id,
            user=self.user,
            action_type="basic_jump",
        )

        # Assert
        Steps.step(message="Проверяем дистанцию, силу и рекорд")
        self.assertEqual(first=updated_hopper.distance, second=10.0)
        self.assertEqual(first=updated_hopper.strength, second=95.0)
        self.assertEqual(first=updated_hopper.best_distance, second=10.0)

    def test_long_jump_with_reactor_success(self):
        """BE_P_7 Проверяет длинный прыжок с форсажем реактора."""
        # Arrange
        Steps.step(message="Хоппер готов к прыжку с форсажем")

        # Act
        Steps.step(message="Выполняем длинный прыжок с форсажем")
        updated_hopper = Steps.perform_action(
            hopper_id=self.hopper.id,
            user=self.user,
            action_type="long_jump",
            use_reactor=True,
        )

        # Assert
        Steps.step(message="Проверяем дистанцию, силу и энергию")
        self.assertEqual(first=updated_hopper.distance, second=45.0)
        self.assertEqual(first=updated_hopper.strength, second=86.0)
        self.assertEqual(first=updated_hopper.reactor_energy, second=50.0)
        self.assertEqual(first=updated_hopper.best_distance, second=45.0)

    def test_go_underground_success(self):
        """BE_P_8 Проверяет переход хоппера под землю."""
        # Arrange
        Steps.step(message="Хоппер готов к погружению")

        # Act
        Steps.step(message="Уходим под землю")
        updated_hopper = Steps.perform_action(
            hopper_id=self.hopper.id,
            user=self.user,
            action_type="go_underground",
        )

        # Assert
        Steps.step(message="Проверяем положение и силу")
        self.assertEqual(first=updated_hopper.location_state, second="underground")
        self.assertEqual(first=updated_hopper.strength, second=94.0)

    def test_return_to_surface_success(self):
        """BE_P_9 Проверяет возвращение хоппера на поверхность."""
        # Arrange
        Steps.step(message="Переводим хоппера под землю")
        Steps.update_hopper(
            hopper=self.hopper,
            location_state="underground",
            strength=100.0,
        )

        # Act
        Steps.step(message="Возвращаемся на поверхность")
        updated_hopper = Steps.perform_action(
            hopper_id=self.hopper.id,
            user=self.user,
            action_type="return_to_surface",
        )

        # Assert
        Steps.step(message="Проверяем положение и силу")
        self.assertEqual(first=updated_hopper.location_state, second="surface")
        self.assertEqual(first=updated_hopper.strength, second=94.0)

    def test_drill_forward_success(self):
        """BE_P_10 Проверяет бурение вперёд под землёй."""
        # Arrange
        Steps.step(message="Погружаем хоппера под землю")
        Steps.perform_action(
            hopper_id=self.hopper.id,
            user=self.user,
            action_type="go_underground",
        )

        # Act
        Steps.step(message="Бурим вперёд")
        updated_hopper = Steps.perform_action(
            hopper_id=self.hopper.id,
            user=self.user,
            action_type="drill_forward",
        )

        # Assert
        Steps.step(message="Проверяем дистанцию, силу и энергию")
        self.assertEqual(first=updated_hopper.distance, second=40.0)
        self.assertEqual(first=updated_hopper.strength, second=78.0)
        self.assertEqual(first=updated_hopper.reactor_energy, second=50.0)
        self.assertEqual(first=updated_hopper.best_distance, second=40.0)

    def test_recovery_on_100m_marks(self):
        """BE_P_11 Проверяет восстановление ресурсов при пересечении 100 м."""
        # Arrange
        Steps.step(message="Ставим хоппера перед отметкой 100 м")
        Steps.update_hopper(
            hopper=self.hopper,
            distance=95.0,
            best_distance=95.0,
            strength=20.0,
            reactor_energy=20.0,
        )

        # Act
        Steps.step(message="Выполняем прыжок через отметку 100 м")
        updated_hopper = Steps.perform_action(
            hopper_id=self.hopper.id,
            user=self.user,
            action_type="basic_jump",
        )

        # Assert
        Steps.step(message="Проверяем восстановление ресурсов")
        self.assertEqual(first=updated_hopper.distance, second=105.0)
        self.assertEqual(first=updated_hopper.strength, second=50.0)
        self.assertEqual(first=updated_hopper.reactor_energy, second=55.0)
        self.assertEqual(first=updated_hopper.best_distance, second=105.0)

    # endregion

    # region === Негативные сценарии ===

    def test_drill_forward_on_surface_raises_error(self):
        """BE_N_5 Проверяет запрет бурения на поверхности."""
        # Arrange
        Steps.step(message="Хоппер находится на поверхности")

        # Act
        Steps.step(message="Пытаемся бурить на поверхности")

        # Assert
        with self.assertRaises(InvalidLocationError) as context:
            Steps.perform_action(
                hopper_id=self.hopper.id,
                user=self.user,
                action_type="drill_forward",
            )
        self.assertIn(
            member="Подземное бурение невозможно на поверхности",
            container=str(context.exception),
        )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)
        self.assertEqual(first=updated_hopper.location_state, second="surface")

    def test_not_enough_energy_for_reactor_jump(self):
        """BE_N_6 Проверяет запрет форсажа при недостатке энергии."""
        # Arrange
        Steps.step(message="Снижаем энергию реактора до 30")
        Steps.update_hopper(
            hopper=self.hopper,
            reactor_energy=30.0,
        )

        # Act
        Steps.step(message="Пытаемся выполнить форсаж")

        # Assert
        with self.assertRaises(NotEnoughEnergyError) as context:
            Steps.perform_action(
                hopper_id=self.hopper.id,
                user=self.user,
                action_type="long_jump",
                use_reactor=True,
            )
        self.assertIn(
            member="Недостаточно энергии реактора для форсажа",
            container=str(context.exception),
        )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)
        self.assertEqual(first=updated_hopper.reactor_energy, second=30.0)

    def test_basic_jump_underground_raises(self):
        """BE_N_7 Проверяет запрет обычного прыжка под землёй."""
        # Arrange
        Steps.step(message="Переводим хоппера под землю")
        Steps.update_hopper(
            hopper=self.hopper,
            location_state="underground",
        )

        # Act
        Steps.step(message="Пытаемся прыгнуть под землёй")

        # Assert
        with self.assertRaises(InvalidLocationError):
            Steps.perform_action(
                hopper_id=self.hopper.id,
                user=self.user,
                action_type="basic_jump",
            )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)
        self.assertEqual(first=updated_hopper.location_state, second="underground")

    def test_not_enough_strength_for_basic_jump(self):
        """BE_N_8 Проверяет запрет прыжка при недостатке силы."""
        # Arrange
        Steps.step(message="Снижаем силу до 1")
        Steps.update_hopper(
            hopper=self.hopper,
            strength=1.0,
        )

        # Act
        Steps.step(message="Пытаемся выполнить обычный прыжок")

        # Assert
        with self.assertRaises(NotEnoughStrengthError):
            Steps.perform_action(
                hopper_id=self.hopper.id,
                user=self.user,
                action_type="basic_jump",
            )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)
        self.assertEqual(first=updated_hopper.strength, second=1.0)

    def test_go_underground_twice_raises(self):
        """BE_N_9 Проверяет запрет повторного погружения под землю."""
        # Arrange
        Steps.step(message="Погружаем хоппера под землю")
        first_result = Steps.perform_action(
            hopper_id=self.hopper.id,
            user=self.user,
            action_type="go_underground",
        )

        # Act
        Steps.step(message="Пытаемся погрузиться повторно")

        # Assert
        with self.assertRaises(InvalidLocationError):
            Steps.perform_action(
                hopper_id=self.hopper.id,
                user=self.user,
                action_type="go_underground",
            )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.location_state, second="underground")
        self.assertEqual(first=updated_hopper.strength, second=first_result.strength)

    def test_unknown_action_raises(self):
        """BE_N_10 Проверяет ошибку при неизвестном типе действия."""
        # Arrange
        Steps.step(message="Готовим неизвестное действие")

        # Act
        Steps.step(message="Пытаемся выполнить teleport")

        # Assert
        with self.assertRaises(ValueError) as context:
            Steps.perform_action(
                hopper_id=self.hopper.id,
                user=self.user,
                action_type="teleport",
            )
        self.assertIn(
            member="Неизвестное действие",
            container=str(context.exception),
        )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)
        self.assertEqual(first=updated_hopper.strength, second=100.0)

    def test_action_on_other_users_hopper_raises_http404(self):
        """BE_N_11 Проверяет запрет действия с чужим хоппером."""
        # Arrange
        Steps.step(message="Создаём второго пользователя")
        other_user = Steps.create_user(
            username="other",
            password=Passwords.DEFAULT,
        )

        # Act
        Steps.step(message="Пытаемся управлять чужим хоппером")

        # Assert
        with self.assertRaises(Http404):
            Steps.perform_action(
                hopper_id=self.hopper.id,
                user=other_user,
                action_type="basic_jump",
            )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)
        self.assertEqual(first=updated_hopper.strength, second=100.0)

    # endregion


class HopperActionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Steps.create_user(
            username=Users.TEST_DRIVER,
            password=Passwords.DEFAULT,
        )
        Steps.login(
            client=self.client,
            username=Users.TEST_DRIVER,
            password=Passwords.DEFAULT,
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name=HopperData.DEFAULT_NAME,
            mass_kg=HopperData.DEFAULT_MASS_KG,
        )

    # region === Позитивные сценарии ===

    def test_action_view_success_htmx(self):
        """BE_P_12 Проверяет успешный HTMX-ответ на действие с карточкой хоппера."""
        # Arrange
        Steps.step(message="Готовим HTMX-запрос на обычный прыжок")

        # Act
        Steps.step(message="Выполняем действие через view")
        response = Steps.post_action(
            client=self.client,
            hopper_id=self.hopper.id,
            action_type="basic_jump",
            headers={"HX-Request": "true"},
        )

        # Assert
        Steps.step(message="Проверяем карточку и состояние хоппера")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertContains(
            response=response,
            text=f"hopper-card-{self.hopper.id}",
        )
        self.assertNotContains(
            response=response,
            text="bg-red-50",
        )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=10.0)
        self.assertEqual(first=updated_hopper.strength, second=95.0)

    # endregion

    # region === Негативные сценарии ===

    def test_action_view_error_htmx_returns_400(self):
        """BE_N_12 Проверяет HTMX-ошибку при недопустимом действии."""
        # Arrange
        Steps.step(message="Готовим HTMX-запрос на бурение")

        # Act
        Steps.step(message="Пытаемся бурить на поверхности")
        response = Steps.post_action(
            client=self.client,
            hopper_id=self.hopper.id,
            action_type="drill_forward",
            headers={"HX-Request": "true"},
        )

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertContains(
            response=response,
            text="Подземное бурение невозможно на поверхности",
            status_code=HttpStatus.BAD_REQUEST,
        )
        self.assertEqual(
            first=response.headers.get("HX-Retarget"),
            second=f"#hopper-error-{self.hopper.id}",
        )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)

    def test_action_view_error_json(self):
        """BE_N_13 Проверяет JSON-ошибку при недопустимом действии."""
        # Arrange
        Steps.step(message="Готовим обычный запрос на бурение")

        # Act
        Steps.step(message="Пытаемся бурить на поверхности")
        response = Steps.post_action(
            client=self.client,
            hopper_id=self.hopper.id,
            action_type="drill_forward",
        )

        # Assert
        Steps.step(message="Проверяем JSON-ошибку")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertJSONEqual(
            raw=response.content,
            expected_data={
                "error": (
                    "Подземное бурение невозможно на поверхности. "
                    "Сначала погрузитесь."
                ),
            },
        )

    def test_action_view_requires_login(self):
        """BE_N_14 Проверяет редирект на вход для анонимного действия."""
        # Arrange
        Steps.step(message="Выполняем выход из системы")
        Steps.logout_session(client=self.client)

        # Act
        Steps.step(message="Отправляем действие анонимно")
        response = Steps.post_action(
            client=self.client,
            hopper_id=self.hopper.id,
            action_type="basic_jump",
        )

        # Assert
        Steps.step(message="Проверяем редирект на вход")
        self.assertEqual(first=response.status_code, second=HttpStatus.FOUND)
        self.assertIn(member=reverse("login"), container=response.url)

    def test_action_view_get_not_allowed(self):
        """BE_N_15 Проверяет запрет GET-запроса к эндпоинту действия."""
        # Arrange
        Steps.step(message="Готовим GET-запрос к действию")

        # Act
        Steps.step(message="Отправляем GET-запрос")
        response = Steps.get_action(
            client=self.client,
            hopper_id=self.hopper.id,
        )

        # Assert
        Steps.step(message="Проверяем статус 405")
        self.assertEqual(
            first=response.status_code,
            second=HttpStatus.METHOD_NOT_ALLOWED,
        )

    # endregion
