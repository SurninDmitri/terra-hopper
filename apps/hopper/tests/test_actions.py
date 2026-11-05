from django.http import Http404
from django.test import Client, TestCase
from django.urls import reverse

from apps.common.testing.steps import Steps
from apps.hopper.domain.exceptions import (
    InvalidLocationError,
    NotEnoughEnergyError,
    NotEnoughStrengthError,
)


class HopperActionsServiceTest(TestCase):
    def setUp(self):
        self.user = Steps.create_user(
            username="testdriver",
            password="password",
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name="Крот-1",
            mass_kg=200.0,
        )

    # region === Позитивные сценарии ===

    def test_basic_jump_success(self):
        """Проверяет обычный прыжок на поверхности.

        Предусловия:
            Хоппер на поверхности, сила 100, дистанция 0.
        Шаги:
            1. Выполнить обычный прыжок.
        Ожидаемый результат:
            distance=10.0, strength=95.0, best_distance=10.0.
        """
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
        """Проверяет длинный прыжок с форсажем реактора.

        Предусловия:
            Хоппер на поверхности, сила и энергия по 100.
        Шаги:
            1. Выполнить длинный прыжок с use_reactor=True.
        Ожидаемый результат:
            distance=45.0, strength=86.0, reactor_energy=50.0.
        """
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
        """Проверяет переход хоппера под землю.

        Предусловия:
            Хоппер на поверхности, сила 100.
        Шаги:
            1. Выполнить go_underground.
        Ожидаемый результат:
            location_state=underground, strength=94.0.
        """
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
        """Проверяет возвращение хоппера на поверхность.

        Предусловия:
            Хоппер под землёй, сила 100.
        Шаги:
            1. Выполнить return_to_surface.
        Ожидаемый результат:
            location_state=surface, strength=94.0.
        """
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
        """Проверяет бурение вперёд под землёй.

        Предусловия:
            Хоппер под землёй, сила 94, энергия 100.
        Шаги:
            1. Выполнить drill_forward.
        Ожидаемый результат:
            distance=40.0, strength=78.0, reactor_energy=50.0.
        """
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
        """Проверяет восстановление ресурсов при пересечении 100 м.

        Предусловия:
            Хоппер на дистанции 95 м, сила и энергия по 20.
        Шаги:
            1. Выполнить обычный прыжок через отметку 100 м.
        Ожидаемый результат:
            distance=105.0, strength=50.0, reactor_energy=55.0.
        """
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
        """Проверяет запрет бурения на поверхности.

        Предусловия:
            Хоппер на поверхности.
        Шаги:
            1. Попытаться выполнить drill_forward.
        Ожидаемый результат:
            Выброшено InvalidLocationError, состояние не изменилось.
        """
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
        """Проверяет запрет форсажа при недостатке энергии.

        Предусловия:
            Энергия реактора равна 30.
        Шаги:
            1. Попытаться выполнить long_jump с форсажем.
        Ожидаемый результат:
            Выброшено NotEnoughEnergyError, состояние не изменилось.
        """
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
        """Проверяет запрет обычного прыжка под землёй.

        Предусловия:
            Хоппер находится под землёй.
        Шаги:
            1. Попытаться выполнить basic_jump.
        Ожидаемый результат:
            Выброшено InvalidLocationError, состояние не изменилось.
        """
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
        """Проверяет запрет прыжка при недостатке силы.

        Предусловия:
            Сила хоппера равна 1.
        Шаги:
            1. Попытаться выполнить basic_jump.
        Ожидаемый результат:
            Выброшено NotEnoughStrengthError, состояние не изменилось.
        """
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
        """Проверяет запрет повторного погружения под землю.

        Предусловия:
            Хоппер уже находится под землёй.
        Шаги:
            1. Попытаться повторно выполнить go_underground.
        Ожидаемый результат:
            Выброшено InvalidLocationError, состояние не изменилось.
        """
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
        """Проверяет ошибку при неизвестном типе действия.

        Предусловия:
            Хоппер существует.
        Шаги:
            1. Попытаться выполнить действие teleport.
        Ожидаемый результат:
            Выброшено ValueError, состояние не изменилось.
        """
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
        """Проверяет запрет действия с чужим хоппером.

        Предусловия:
            Хоппер принадлежит пользователю testdriver.
        Шаги:
            1. Попытаться выполнить действие от имени другого пользователя.
        Ожидаемый результат:
            Выброшено Http404, состояние хоппера не изменилось.
        """
        # Arrange
        Steps.step(message="Создаём второго пользователя")
        other_user = Steps.create_user(
            username="other",
            password="password",
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
            username="testdriver",
            password="password",
        )
        Steps.login(
            client=self.client,
            username="testdriver",
            password="password",
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name="Крот-1",
            mass_kg=200.0,
        )

    # region === Позитивные сценарии ===

    def test_action_view_success_htmx(self):
        """Проверяет успешный HTMX-ответ на действие с карточкой хоппера.

        Предусловия:
            Пользователь авторизован, хоппер на поверхности.
        Шаги:
            1. Выполнить basic_jump с заголовком HX-Request.
        Ожидаемый результат:
            Статус 200, карточка обновлена, дистанция и сила изменены.
        """
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
        self.assertEqual(first=response.status_code, second=200)
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
        """Проверяет HTMX-ошибку при недопустимом действии.

        Предусловия:
            Пользователь авторизован, хоппер на поверхности.
        Шаги:
            1. Выполнить drill_forward с заголовком HX-Request.
        Ожидаемый результат:
            Статус 400, ошибка показана в блоке hopper-error.
        """
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
        self.assertEqual(first=response.status_code, second=400)
        self.assertContains(
            response=response,
            text="Подземное бурение невозможно на поверхности",
            status_code=400,
        )
        self.assertEqual(
            first=response.headers.get("HX-Retarget"),
            second=f"#hopper-error-{self.hopper.id}",
        )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)

    def test_action_view_error_json(self):
        """Проверяет JSON-ошибку при недопустимом действии.

        Предусловия:
            Пользователь авторизован, хоппер на поверхности.
        Шаги:
            1. Выполнить drill_forward без HTMX-заголовка.
        Ожидаемый результат:
            Статус 400, JSON содержит текст ошибки.
        """
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
        self.assertEqual(first=response.status_code, second=400)
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
        """Проверяет редирект на вход для анонимного действия.

        Предусловия:
            Пользователь вышел из системы.
        Шаги:
            1. Отправить действие без авторизации.
        Ожидаемый результат:
            Статус 302, редирект на страницу входа.
        """
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
        self.assertEqual(first=response.status_code, second=302)
        self.assertIn(member=reverse("login"), container=response.url)

    def test_action_view_get_not_allowed(self):
        """Проверяет запрет GET-запроса к эндпоинту действия.

        Предусловия:
            Пользователь авторизован.
        Шаги:
            1. Выполнить GET-запрос к эндпоинту действия.
        Ожидаемый результат:
            Статус 405.
        """
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
        self.assertEqual(first=response.status_code, second=405)

    # endregion
