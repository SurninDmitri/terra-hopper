from django.urls import reverse

from apps.common.testing.cases import AuthenticatedHopperTestCase, HopperTestCase
from apps.common.testing.constants import HttpStatus, Passwords
from apps.common.testing.steps import Steps


class HopperActionsViewTest(AuthenticatedHopperTestCase):
    # region === Позитивные сценарии ===

    def test_basic_jump_success(self):
        """BE_P_6 Проверяет обычный прыжок на поверхности."""
        # Arrange
        Steps.step(message=f"Хоппер {self.hopper_name} готов к обычному прыжку")

        # Act
        Steps.step(message="Выполняем обычный прыжок")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем статус, дистанцию, силу, рекорд и игровую панель")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=10.0,
                                  expected_strength=95.0,
                                  expected_best_distance=10.0)
        self.assertTemplateUsed(response=response,
                                template_name="hopper/partials/game_panel.html")
        self.assertContains(response=response, text="Дистанция: 10,0")
        trigger = response.headers.get("HX-Trigger")
        self.assertIsNotNone(trigger)
        self.assertIn(member="updateMap", container=trigger)
        self.assertIn(member='"distance": 10.0', container=trigger)

    def test_long_jump_success(self):
        """BE_P_25 Проверяет дальний прыжок без форсажа реактора."""
        # Arrange
        Steps.step(message="Хоппер готов к дальнему прыжку без форсажа")

        # Act
        Steps.step(message="Выполняем дальний прыжок")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="long_jump")

        # Assert
        Steps.step(message="Проверяем дистанцию, силу, рекорд и сохранение энергии")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=30.0,
                                  expected_strength=86.0,
                                  expected_reactor_energy=100.0,
                                  expected_best_distance=30.0)

    def test_long_jump_with_reactor_success(self):
        """BE_P_7 Проверяет длинный прыжок с форсажем реактора."""
        # Arrange
        Steps.step(message="Хоппер готов к прыжку с форсажем")

        # Act
        Steps.step(message="Выполняем длинный прыжок с форсажем")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="long_jump",
                                          use_reactor=True)

        # Assert
        Steps.step(message="Проверяем дистанцию, силу и энергию")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=45.0,
                                  expected_strength=86.0,
                                  expected_reactor_energy=50.0,
                                  expected_best_distance=45.0)

    def test_go_underground_success(self):
        """BE_P_8 Проверяет переход хоппера под землю."""
        # Arrange
        Steps.step(message="Хоппер готов к погружению")

        # Act
        Steps.step(message="Уходим под землю")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="go_underground")

        # Assert
        Steps.step(message="Проверяем положение и силу")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_location_state="underground",
                                  expected_strength=94.0)
        self.assertContains(response=response, text="Выйти на поверхность")
        trigger = response.headers.get("HX-Trigger")
        self.assertIn(member='"location_state": "underground"', container=trigger)

    def test_return_to_surface_success(self):
        """BE_P_9 Проверяет возвращение хоппера на поверхность."""
        # Arrange
        Steps.step(message="Переводим хоппера под землю")
        Steps.update_hopper(hopper=self.hopper,
                            location_state="underground",
                            strength=100.0)

        # Act
        Steps.step(message="Возвращаемся на поверхность")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="return_to_surface")

        # Assert
        Steps.step(message="Проверяем положение и силу")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_location_state="surface",
                                  expected_strength=94.0)

    def test_drill_forward_success(self):
        """BE_P_10 Проверяет бурение вперёд под землёй."""
        # Arrange
        Steps.step(message="Погружаем хоппера под землю")
        Steps.post_game_action(client=self.client,
                               hopper_id=self.hopper.id,
                               action_type="go_underground")

        # Act
        Steps.step(message="Бурим вперёд")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="drill_forward")

        # Assert
        Steps.step(message="Проверяем дистанцию, силу и энергию")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=40.0,
                                  expected_strength=78.0,
                                  expected_reactor_energy=50.0,
                                  expected_best_distance=40.0)

    def test_recovery_on_100m_marks(self):
        """BE_P_11 Проверяет восстановление ресурсов при пересечении 100 м."""
        # Arrange
        Steps.step(message="Ставим хоппера перед отметкой 100 м")
        Steps.update_hopper(hopper=self.hopper,
                            distance=95.0,
                            best_distance=95.0,
                            strength=20.0,
                            reactor_energy=20.0)

        # Act
        Steps.step(message="Выполняем прыжок через отметку 100 м")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем восстановление ресурсов")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=105.0,
                                  expected_strength=50.0,
                                  expected_reactor_energy=55.0,
                                  expected_best_distance=105.0)

    # endregion

    # region === Негативные сценарии ===

    def test_drill_forward_on_surface_returns_error(self):
        """BE_N_5 Проверяет запрет бурения на поверхности."""
        # Arrange
        Steps.step(message="Хоппер находится на поверхности")

        # Act
        Steps.step(message="Пытаемся бурить на поверхности")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="drill_forward")

        # Assert
        Steps.step(message="Проверяем ошибку, toast и отсутствие изменений хоппера")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertIn(member="Подземное бурение невозможно на поверхности",
                      container=response.context["error_message"])
        self.assertTemplateUsed(response=response,
                                template_name="hopper/partials/toast.html")
        self.assertContains(response=response,
                            text="Подземное бурение невозможно на поверхности. Сначала погрузитесь.",
                            status_code=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.headers.get("HX-Retarget"), second="#game-toast-wrap")
        self.assertEqual(first=response.headers.get("HX-Reswap"), second="innerHTML")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_location_state="surface")

    def test_not_enough_energy_for_reactor_jump(self):
        """BE_N_6 Проверяет запрет форсажа при недостатке энергии."""
        # Arrange
        Steps.step(message="Снижаем энергию реактора до 30")
        Steps.update_hopper(hopper=self.hopper,
                            reactor_energy=30.0)

        # Act
        Steps.step(message="Пытаемся выполнить форсаж")

        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="long_jump",
                                          use_reactor=True)

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertIn(member="Недостаточно энергии реактора для форсажа",
                      container=response.context["error_message"])

        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_reactor_energy=30.0)

    def test_go_underground_twice_returns_error(self):
        """BE_N_9 Проверяет запрет повторного погружения под землю."""
        # Arrange
        Steps.step(message="Погружаем хоппера под землю")
        first_response = Steps.post_game_action(client=self.client,
                                                hopper_id=self.hopper.id,
                                                action_type="go_underground")

        self.assertEqual(first=first_response.status_code, second=HttpStatus.OK)
        first_strength = Steps.reload_hopper(hopper=self.hopper).strength

        # Act
        Steps.step(message="Пытаемся погрузиться повторно")

        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="go_underground")

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)

        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_location_state="underground",
                                  expected_strength=first_strength)

    def test_unknown_action_returns_bad_request(self):
        """BE_N_10 Проверяет ошибку при неизвестном типе действия."""
        # Arrange
        Steps.step(message="Готовим неизвестное действие")

        # Act
        Steps.step(message="Пытаемся выполнить teleport")

        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="teleport")

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.context["error_message"],
                         second="Неизвестное действие: teleport")

        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=100.0)

    def test_action_on_other_users_hopper_returns_404(self):
        """BE_N_11 Проверяет запрет действия с чужим хоппером."""
        # Arrange
        Steps.step(message="Создаём второго пользователя")
        other_user = Steps.create_user(username="other",
                                       password=Passwords.DEFAULT)

        Steps.login(client=self.client,
                    username=other_user.username,
                    password=Passwords.DEFAULT)

        # Act
        Steps.step(message="Пытаемся управлять чужим хоппером")

        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.NOT_FOUND)

        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=100.0)

    def test_action_view_get_not_allowed(self):
        """BE_N_15 Проверяет запрет GET-запроса к эндпоинту действия."""
        # Arrange
        Steps.step(message="Готовим GET-запрос к действию")

        # Act
        Steps.step(message="Отправляем GET-запрос")
        response = Steps.get_action(client=self.client,
                                    hopper_id=self.hopper.id)

        # Assert
        Steps.step(message="Проверяем статус 405")
        self.assertEqual(first=response.status_code,
                         second=HttpStatus.METHOD_NOT_ALLOWED)

    def test_return_to_surface_when_already_on_surface(self):
        """BE_N_37 Проверяет запрет подъёма уже находящегося на поверхности хоппера."""
        # Arrange
        Steps.step(message="Запрет подъёма уже находящегося на поверхности хоппера")

        # Act
        Steps.step(message="Отправляем return_to_surface через HTTP")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="return_to_surface")

        # Assert
        Steps.step(message="Проверяем отказ, текст ошибки и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.context["error_message"],
                         second="Транспорт уже находится на поверхности.")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=100.0,
                                  expected_reactor_energy=100.0,
                                  expected_location_state="surface")

    # endregion


class HopperInsufficientStrengthViewTest(AuthenticatedHopperTestCase):
    hopper_strength = 1.0

    # region === Негативные сценарии ===

    def test_not_enough_strength_for_basic_jump(self):
        """BE_N_8 Проверяет запрет прыжка при недостатке силы."""
        # Arrange
        Steps.step(message="Фикстура подготовила хоппера с силой 1")

        # Act
        Steps.step(message="Пытаемся выполнить обычный прыжок")

        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)

        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=1.0)

    def test_not_enough_strength_for_long_jump(self):
        """BE_N_30 Проверяет запрет дальнего прыжка при недостатке силы."""
        # Arrange
        Steps.step(message="Запрет дальнего прыжка при недостатке силы")

        # Act
        Steps.step(message="Отправляем long_jump через HTTP")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="long_jump")

        # Assert
        Steps.step(message="Проверяем отказ, текст ошибки и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.context["error_message"],
                         second="Недостаточно силы для выполнения дальнего прыжка.")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=1.0,
                                  expected_reactor_energy=100.0,
                                  expected_location_state="surface")

    def test_not_enough_strength_for_reactor_jump(self):
        """BE_N_31 Проверяет запрет форсажа при недостатке силы."""
        # Arrange
        Steps.step(message="Запрет форсажа при недостатке силы")

        # Act
        Steps.step(message="Отправляем long_jump с форсажем через HTTP")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="long_jump",
                                          use_reactor=True)

        # Assert
        Steps.step(message="Проверяем отказ, текст ошибки и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.context["error_message"],
                         second="Недостаточно силы для выполнения дальнего прыжка.")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=1.0,
                                  expected_reactor_energy=100.0,
                                  expected_location_state="surface")

    def test_not_enough_strength_for_go_underground(self):
        """BE_N_32 Проверяет запрет погружения при недостатке силы."""
        # Arrange
        Steps.step(message="Запрет погружения при недостатке силы")

        # Act
        Steps.step(message="Отправляем go_underground через HTTP")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="go_underground")

        # Assert
        Steps.step(message="Проверяем отказ, текст ошибки и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.context["error_message"],
                         second="Недостаточно силы для погружения под землю.")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=1.0,
                                  expected_reactor_energy=100.0,
                                  expected_location_state="surface")

    # endregion


class HopperUndergroundInsufficientStrengthViewTest(AuthenticatedHopperTestCase):
    hopper_strength = 1.0
    hopper_location_state = "underground"

    # region === Негативные сценарии ===

    def test_not_enough_strength_for_return_to_surface(self):
        """BE_N_33 Проверяет запрет подъёма при недостатке силы."""
        # Arrange
        Steps.step(message="Запрет подъёма при недостатке силы")

        # Act
        Steps.step(message="Отправляем return_to_surface через HTTP")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="return_to_surface")

        # Assert
        Steps.step(message="Проверяем отказ, текст ошибки и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.context["error_message"],
                         second="Недостаточно силы для возвращения на поверхность.")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=1.0,
                                  expected_reactor_energy=100.0,
                                  expected_location_state="underground")

    def test_not_enough_strength_for_drill_forward(self):
        """BE_N_34 Проверяет запрет бурения при недостатке силы."""
        # Arrange
        Steps.step(message="Запрет бурения при недостатке силы")

        # Act
        Steps.step(message="Отправляем drill_forward через HTTP")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="drill_forward")

        # Assert
        Steps.step(message="Проверяем отказ, текст ошибки и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.context["error_message"],
                         second="Недостаточно силы для подземного бурения.")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=1.0,
                                  expected_reactor_energy=100.0,
                                  expected_location_state="underground")

    # endregion


class HopperUndergroundActionErrorsViewTest(AuthenticatedHopperTestCase):
    hopper_location_state = "underground"

    # region === Негативные сценарии ===

    def test_basic_jump_underground_returns_error(self):
        """BE_N_7 Проверяет запрет обычного прыжка под землёй."""
        # Arrange
        Steps.step(message="Фикстура подготовила хоппера под землёй")

        # Act
        Steps.step(message="Пытаемся прыгнуть под землёй")

        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)

        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_location_state="underground")

    def test_long_jump_underground_returns_error(self):
        """BE_N_35 Проверяет запрет дальнего прыжка под землёй."""
        # Arrange
        Steps.step(message="Запрет дальнего прыжка под землёй")

        # Act
        Steps.step(message="Отправляем long_jump через HTTP")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="long_jump")

        # Assert
        Steps.step(message="Проверяем отказ, текст ошибки и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.context["error_message"],
                         second="Дальний прыжок невозможен: транспорт находится под землей.")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=100.0,
                                  expected_reactor_energy=100.0,
                                  expected_location_state="underground")

    def test_reactor_jump_underground_returns_error(self):
        """BE_N_36 Проверяет запрет форсажа под землёй."""
        # Arrange
        Steps.step(message="Запрет форсажа под землёй")

        # Act
        Steps.step(message="Отправляем long_jump с форсажем через HTTP")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="long_jump",
                                          use_reactor=True)

        # Assert
        Steps.step(message="Проверяем отказ, текст ошибки и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.context["error_message"],
                         second="Дальний прыжок невозможен: транспорт находится под землей.")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=100.0,
                                  expected_reactor_energy=100.0,
                                  expected_location_state="underground")

    def test_not_enough_energy_for_drill_forward(self):
        """BE_N_38 Проверяет запрет бурения при недостатке энергии."""
        # Arrange
        Steps.step(message="Запрет бурения при недостатке энергии")
        Steps.update_hopper(hopper=self.hopper, reactor_energy=30.0)

        # Act
        Steps.step(message="Отправляем drill_forward через HTTP")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="drill_forward")

        # Assert
        Steps.step(message="Проверяем отказ, текст ошибки и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertEqual(first=response.context["error_message"],
                         second="Недостаточно энергии реактора для запуска буров (требуется 50.0).")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=100.0,
                                  expected_reactor_energy=30.0,
                                  expected_location_state="underground")

    # endregion


class HopperAnonymousActionViewTest(HopperTestCase):
    # region === Негативные сценарии ===

    def test_action_view_requires_login(self):
        """BE_N_14 Проверяет редирект на вход для анонимного действия."""
        # Arrange
        Steps.step(message="Используем анонимный клиент")

        # Act
        Steps.step(message="Отправляем действие анонимно")
        response = Steps.post_action(client=self.client,
                                     hopper_id=self.hopper.id,
                                     action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем редирект на вход")
        self.assertEqual(first=response.status_code, second=HttpStatus.FOUND)
        self.assertIn(member=reverse("login"), container=response.url)

    # endregion
