from django.urls import reverse

from apps.common.testing.cases import AuthenticatedHopperTestCase, HopperTestCase
from apps.common.testing.constants import HopperData, HttpStatus, Passwords
from apps.common.testing.steps import Steps


class HopperGameScreenTest(AuthenticatedHopperTestCase):
    # region === Позитивные сценарии ===

    def test_game_screen_renders(self):
        """BE_P_13 Проверяет отображение игрового экрана хоппера."""
        # Arrange
        Steps.step(message="Готовим игровой экран хоппера")

        # Act
        Steps.step(message="Открываем игровой экран")
        response = Steps.get_game_screen(client=self.client,
                                         hopper_id=self.hopper.id)

        # Assert
        Steps.step(message="Проверяем шаблон и элементы интерфейса")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertTemplateUsed(response=response,
                                template_name="hopper/game.html")
        self.assertContains(response=response, text=self.hopper.name)
        self.assertContains(response=response, text="Назад в гараж")
        self.assertContains(response=response, text="Подземелье")
        self.assertContains(response=response, text="Обычный прыжок (+10м)")

    def test_state_api_returns_json(self):
        """BE_P_14 Проверяет состояние в API и БД после каждого действия."""
        # Arrange
        Steps.step(message="Готовим рассчитанные вручную состояния хоппера массой 200 кг")
        initial_state = {
            "id": self.hopper.id,
            "name": HopperData.DEFAULT_NAME,
            "distance": 0.0,
            "best_distance": 0.0,
            "strength": 100.0,
            "reactor_energy": 100.0,
            "location_state": "surface",
        }
        expected_states = (
            # Погружение тратит 6 силы: 100 - 6 = 94.
            ("go_underground", {
                "distance": 0.0,
                "best_distance": 0.0,
                "strength": 94.0,
                "reactor_energy": 100.0,
                "location_state": "underground",
            }),
            # Бурение даёт 40 м, тратит 16 силы и 50 энергии: 94 - 16 = 78.
            ("drill_forward", {
                "distance": 40.0,
                "best_distance": 40.0,
                "strength": 78.0,
                "reactor_energy": 50.0,
                "location_state": "underground",
            }),
            # Подъём тратит ещё 6 силы: 78 - 6 = 72, дистанция сохраняется.
            ("return_to_surface", {
                "distance": 40.0,
                "best_distance": 40.0,
                "strength": 72.0,
                "reactor_energy": 50.0,
                "location_state": "surface",
            }),
        )

        # Act
        Steps.step(message="Запрашиваем исходное состояние через API")
        response = Steps.get_state(client=self.client,
                                   hopper_id=self.hopper.id)

        # Assert
        Steps.step(message="Проверяем исходное состояние в API и БД")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertEqual(first=response.json(), second=initial_state)
        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_name=HopperData.DEFAULT_NAME,
                                  expected_distance=0.0,
                                  expected_strength=100.0,
                                  expected_reactor_energy=100.0,
                                  expected_best_distance=0.0,
                                  expected_location_state="surface")

        for action_type, expected_state in expected_states:
            with self.subTest(action_type=action_type):
                # Act
                Steps.step(message=f"Выполняем {action_type} и запрашиваем состояние")
                action_response = Steps.post_game_action(client=self.client,
                                                         hopper_id=self.hopper.id,
                                                         action_type=action_type)
                state_response = Steps.get_state(client=self.client,
                                                 hopper_id=self.hopper.id)

                # Assert
                Steps.step(message="Сверяем API и БД с рассчитанным состоянием")
                self.assertEqual(first=action_response.status_code, second=HttpStatus.OK)
                self.assertEqual(first=state_response.status_code, second=HttpStatus.OK)
                expected_payload = {
                    "id": self.hopper.id,
                    "name": HopperData.DEFAULT_NAME,
                    **expected_state,
                }
                self.assertEqual(first=state_response.json(), second=expected_payload)
                Steps.assert_hopper_state(test_case=self,
                                          hopper=self.hopper,
                                          expected_name=HopperData.DEFAULT_NAME,
                                          expected_distance=expected_state["distance"],
                                          expected_strength=expected_state["strength"],
                                          expected_reactor_energy=expected_state["reactor_energy"],
                                          expected_best_distance=expected_state["best_distance"],
                                          expected_location_state=expected_state["location_state"])

    def test_dashboard_card_has_no_action_buttons(self):
        """BE_P_15 Проверяет отсутствие игровых кнопок на карточке дашборда."""
        # Arrange
        Steps.step(message="Готовим дашборд с карточкой хоппера")

        # Act
        Steps.step(message="Открываем дашборд")
        response = Steps.get_dashboard(client=self.client)

        # Assert
        Steps.step(message="Проверяем наличие и отсутствие кнопок")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertContains(response=response, text="Запустить заезд")
        self.assertNotContains(response=response, text="Прыжок")
        self.assertNotContains(response=response, text="Бурить")

    def test_start_race_resets_session_keeps_best_distance(self):
        """BE_P_16 Проверяет сброс заезда при открытии игрового экрана."""
        # Arrange
        Steps.step(message="Заполняем хоппера накопленными значениями")
        Steps.update_hopper(hopper=self.hopper,
                            distance=120.0,
                            strength=40.0,
                            reactor_energy=30.0,
                            location_state="underground",
                            best_distance=130.0)

        # Act
        Steps.step(message="Открываем игровой экран для старта заезда")
        response = Steps.get_game_screen(client=self.client,
                                         hopper_id=self.hopper.id)

        # Assert
        Steps.step(message="Проверяем сброс ресурсов и сохранение рекорда")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)

        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=0.0,
                                  expected_strength=100.0,
                                  expected_reactor_energy=100.0,
                                  expected_location_state="surface",
                                  expected_best_distance=130.0)

    # endregion


class HopperGameAccessTest(HopperTestCase):
    # region === Негативные сценарии ===

    def test_game_screen_requires_login(self):
        """BE_N_16 Проверяет редирект на вход для неавторизованного пользователя."""
        # Arrange
        Steps.step(message="Используем анонимный клиент")

        # Act
        Steps.step(message="Пытаемся открыть игровой экран анонимно")
        response = Steps.get_game_screen(client=self.client,
                                         hopper_id=self.hopper.id)

        # Assert
        Steps.step(message="Проверяем редирект на вход")
        self.assertEqual(first=response.status_code, second=HttpStatus.FOUND)
        self.assertIn(member=reverse("login"), container=response.url)

    def test_game_screen_forbidden_for_other_user(self):
        """BE_N_17 Проверяет запрет доступа к чужому игровому экрану."""
        # Arrange
        Steps.step(message="Создаём другого пользователя и авторизуемся")
        other_user = Steps.create_user(username="other", password=Passwords.DEFAULT)
        Steps.login(client=self.client,
                    username=other_user.username,
                    password=Passwords.DEFAULT)

        # Act
        Steps.step(message="Пытаемся открыть чужой игровой экран")
        response = Steps.get_game_screen(client=self.client,
                                         hopper_id=self.hopper.id)

        # Assert
        Steps.step(message="Проверяем статус 404")
        self.assertEqual(first=response.status_code, second=HttpStatus.NOT_FOUND)

    # endregion


class HopperActionAvailabilityViewTest(AuthenticatedHopperTestCase):
    hopper_mass_kg = 400.0

    # region === Позитивные сценарии ===

    def test_all_available_on_fresh_surface_transport(self):
        """BE_P_18 Проверяет доступность действий для нового хоппера на поверхности."""
        # Arrange
        Steps.step(message="Готовим нового хоппера на поверхности")

        # Act
        Steps.step(message="Получаем доступность действий из ответа игрового экрана")
        response = Steps.get_game_screen(client=self.client,
                                         hopper_id=self.hopper.id)

        # Assert
        Steps.step(message="Проверяем флаги доступности")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        allowed = response.context["allowed"]
        self.assertTrue(allowed["basic_jump"])
        self.assertTrue(allowed["long_jump"])
        self.assertTrue(allowed["long_reactor"])
        self.assertTrue(allowed["go_underground"])
        self.assertFalse(allowed["return_to_surface"])
        self.assertFalse(allowed["drill_forward"])

    # endregion

    # region === Негативные сценарии ===

    def test_blocked_by_location(self):
        """BE_N_18 Проверяет блокировку действий из-за положения под землёй."""
        # Arrange
        Steps.step(message="Готовим хоппера к погружению")

        # Act
        Steps.step(message="Получаем доступность действий из ответа игрового экрана")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="go_underground")

        # Assert
        Steps.step(message="Проверяем блокировку по положению")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        allowed = response.context["allowed"]
        self.assertFalse(allowed["basic_jump"])
        self.assertFalse(allowed["long_jump"])
        self.assertFalse(allowed["long_reactor"])
        self.assertFalse(allowed["go_underground"])
        self.assertTrue(allowed["return_to_surface"])
        self.assertTrue(allowed["drill_forward"])

    def test_blocked_by_strength(self):
        """BE_N_19 Проверяет блокировку действий из-за недостатка силы."""
        # Arrange
        Steps.step(message="Готовим силу 19: после обычного прыжка останется 12")
        Steps.update_hopper(hopper=self.hopper,
                            strength=19.0)

        # Act
        Steps.step(message="Получаем доступность действий из ответа игрового экрана")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем блокировку по силе")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        allowed = response.context["allowed"]
        self.assertTrue(allowed["basic_jump"])
        self.assertFalse(allowed["long_jump"])
        self.assertFalse(allowed["long_reactor"])
        self.assertTrue(allowed["go_underground"])

    def test_reactor_blocked_by_energy(self):
        """BE_N_20 Проверяет блокировку форсажа из-за недостатка энергии."""
        # Arrange
        Steps.step(message="Снижаем энергию реактора до 40")
        Steps.update_hopper(hopper=self.hopper,
                            reactor_energy=40.0)

        # Act
        Steps.step(message="Получаем доступность действий из ответа игрового экрана")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем блокировку форсажа")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        allowed = response.context["allowed"]
        self.assertTrue(allowed["long_jump"])
        self.assertFalse(allowed["long_reactor"])

    def test_drill_blocked_by_energy_underground(self):
        """BE_N_21 Проверяет блокировку бурения из-за недостатка энергии."""
        # Arrange
        Steps.step(message="Готовим хоппера к погружению с энергией 40")
        Steps.update_hopper(hopper=self.hopper,
                            reactor_energy=40.0)

        # Act
        Steps.step(message="Получаем доступность действий из ответа игрового экрана")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="go_underground")

        # Assert
        Steps.step(message="Проверяем блокировку бурения")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        allowed = response.context["allowed"]
        self.assertFalse(allowed["drill_forward"])

    # endregion


class HopperGameActionTest(AuthenticatedHopperTestCase):
    # region === Позитивные сценарии ===

    def test_panel_keeps_id_after_swap_for_chained_actions(self):
        """BE_P_20 Проверяет сохранение id панели после нескольких действий подряд."""
        # Arrange
        Steps.step(message="Готовим цепочку из двух прыжков")

        # Act
        Steps.step(message="Выполняем первый прыжок")
        first_response = Steps.post_game_action(client=self.client,
                                                hopper_id=self.hopper.id,
                                                action_type="basic_jump")

        Steps.step(message="Выполняем второй прыжок")
        second_response = Steps.post_game_action(client=self.client,
                                                 hopper_id=self.hopper.id,
                                                 action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем id панели и итоговую дистанцию")
        self.assertEqual(first=first_response.status_code, second=HttpStatus.OK)
        self.assertContains(response=first_response, text='id="game-panel"')

        self.assertEqual(first=second_response.status_code, second=HttpStatus.OK)
        self.assertContains(response=second_response, text="Дистанция: 20,0")

        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_distance=20.0)

    def test_disabled_buttons_render_with_not_allowed_style(self):
        """BE_P_22 Проверяет отрисовку недоступных кнопок после подъёма."""
        # Arrange
        Steps.step(message="Готовим хоппера под землёй с энергией 30")
        Steps.update_hopper(hopper=self.hopper,
                            location_state="underground",
                            reactor_energy=30.0)

        # Act
        Steps.step(message="Возвращаемся на поверхность")
        response = Steps.post_game_action(client=self.client,
                                          hopper_id=self.hopper.id,
                                          action_type="return_to_surface")

        # Assert
        Steps.step(message="Проверяем стили активных и заблокированных кнопок")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertContains(response=response, text="Дистанция: 0,0")
        self.assertNotContains(response=response,
                               text="bg-emerald-600 hover:bg-emerald-700")
        self.assertNotContains(response=response,
                               text="bg-stone-700 hover:bg-stone-800")
        self.assertContains(response=response,
                            text="opacity-50 cursor-not-allowed")

    # endregion

    # region === Негативные сценарии ===

    def test_reactor_button_disabled_after_energy_spent(self):
        """BE_N_22 Проверяет блокировку форсажа после полного расхода энергии."""
        # Arrange
        Steps.step(message="Готовим два форсажа подряд")

        # Act
        Steps.step(message="Выполняем первый форсаж")
        Steps.post_game_action(client=self.client,
                               hopper_id=self.hopper.id,
                               action_type="long_jump",
                               use_reactor=True)

        Steps.step(message="Выполняем второй форсаж")
        second_response = Steps.post_game_action(client=self.client,
                                                 hopper_id=self.hopper.id,
                                                 action_type="long_jump",
                                                 use_reactor=True)

        Steps.step(message="Пытаемся выполнить третий форсаж")
        third_response = Steps.post_game_action(client=self.client,
                                                hopper_id=self.hopper.id,
                                                action_type="long_jump",
                                                use_reactor=True)

        # Assert
        Steps.step(message="Проверяем энергию и состояние кнопки")
        self.assertEqual(first=second_response.status_code, second=HttpStatus.OK)

        Steps.assert_hopper_state(test_case=self,
                                  hopper=self.hopper,
                                  expected_reactor_energy=0.0)

        self.assertContains(response=second_response,
                            text="Форсаж реактора (+45м)")
        self.assertNotContains(response=second_response,
                               text="bg-fuchsia-600 hover:bg-fuchsia-700")
        self.assertContains(response=second_response,
                            text="bg-fuchsia-600 opacity-50 cursor-not-allowed")
        self.assertEqual(first=third_response.status_code,
                         second=HttpStatus.BAD_REQUEST)

    # endregion
