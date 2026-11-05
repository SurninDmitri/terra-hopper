from django.test import Client, TestCase
from django.urls import reverse

from apps.common.testing.constants import HopperData, HttpStatus, Passwords, Users
from apps.common.testing.steps import Steps


class HopperGameScreenTest(TestCase):
    def setUp(self):
        self.user = Steps.create_user(
            username=Users.TEST_DRIVER,
            password=Passwords.DEFAULT,
        )
        self.other_user = Steps.create_user(
            username="other",
            password=Passwords.DEFAULT,
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name=HopperData.DEFAULT_NAME,
            mass_kg=HopperData.DEFAULT_MASS_KG,
        )
        self.client = Client()
        Steps.login(
            client=self.client,
            username=Users.TEST_DRIVER,
            password=Passwords.DEFAULT,
        )

    # region === Позитивные сценарии ===

    def test_game_screen_renders(self):
        """BE_P_13 Проверяет отображение игрового экрана хоппера."""
        # Arrange
        Steps.step(message="Готовим игровой экран хоппера")

        # Act
        Steps.step(message="Открываем игровой экран")
        response = Steps.get_game_screen(
            client=self.client,
            hopper_id=self.hopper.id,
        )

        # Assert
        Steps.step(message="Проверяем шаблон и элементы интерфейса")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertTemplateUsed(
            response=response,
            template_name="hopper/game.html",
        )
        self.assertContains(response=response, text=self.hopper.name)
        self.assertContains(response=response, text="Назад в гараж")
        self.assertContains(response=response, text="Подземелье")
        self.assertContains(response=response, text="Обычный прыжок (+10м)")

    def test_state_api_returns_json(self):
        """BE_P_14 Проверяет JSON-ответ API состояния хоппера."""
        # Arrange
        Steps.step(message="Готовим запрос состояния хоппера")

        # Act
        Steps.step(message="Запрашиваем состояние через API")
        response = Steps.get_state(
            client=self.client,
            hopper_id=self.hopper.id,
        )

        # Assert
        Steps.step(message="Проверяем поля JSON")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)

        state = response.json()
        self.assertEqual(first=state["name"], second=HopperData.DEFAULT_NAME)
        self.assertEqual(first=state["distance"], second=0.0)
        self.assertEqual(first=state["best_distance"], second=0.0)
        self.assertEqual(first=state["location_state"], second="surface")

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
        Steps.update_hopper(
            hopper=self.hopper,
            distance=120.0,
            strength=40.0,
            reactor_energy=30.0,
            location_state="underground",
            best_distance=130.0,
        )

        # Act
        Steps.step(message="Открываем игровой экран для старта заезда")
        response = Steps.get_game_screen(
            client=self.client,
            hopper_id=self.hopper.id,
        )

        # Assert
        Steps.step(message="Проверяем сброс ресурсов и сохранение рекорда")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)
        self.assertEqual(first=updated_hopper.strength, second=100.0)
        self.assertEqual(first=updated_hopper.reactor_energy, second=100.0)
        self.assertEqual(first=updated_hopper.location_state, second="surface")
        self.assertEqual(first=updated_hopper.best_distance, second=130.0)

    def test_start_race_service(self):
        """BE_P_17 Проверяет сброс заезда через сервис start_race."""
        # Arrange
        Steps.step(message="Готовим хоппера перед стартом заезда")
        Steps.update_hopper(
            hopper=self.hopper,
            distance=55.0,
            strength=10.0,
            best_distance=55.0,
        )

        # Act
        Steps.step(message="Запускаем заезд через сервис")
        started_hopper = Steps.start_race(
            hopper_id=self.hopper.id,
            user=self.user,
        )

        # Assert
        Steps.step(message="Проверяем сброс дистанции и сохранение рекорда")
        self.assertEqual(first=started_hopper.distance, second=0.0)
        self.assertEqual(first=started_hopper.best_distance, second=55.0)

    # endregion

    # region === Негативные сценарии ===

    def test_game_screen_requires_login(self):
        """BE_N_16 Проверяет редирект на вход для неавторизованного пользователя."""
        # Arrange
        Steps.step(message="Выполняем выход из системы")
        Steps.logout_session(client=self.client)

        # Act
        Steps.step(message="Пытаемся открыть игровой экран анонимно")
        response = Steps.get_game_screen(
            client=self.client,
            hopper_id=self.hopper.id,
        )

        # Assert
        Steps.step(message="Проверяем редирект на вход")
        self.assertEqual(first=response.status_code, second=HttpStatus.FOUND)
        self.assertIn(member=reverse("login"), container=response.url)

    def test_game_screen_forbidden_for_other_user(self):
        """BE_N_17 Проверяет запрет доступа к чужому игровому экрану."""
        # Arrange
        Steps.step(message="Авторизуемся под другим пользователем")
        Steps.login(
            client=self.client,
            username="other",
            password=Passwords.DEFAULT,
        )

        # Act
        Steps.step(message="Пытаемся открыть чужой игровой экран")
        response = Steps.get_game_screen(
            client=self.client,
            hopper_id=self.hopper.id,
        )

        # Assert
        Steps.step(message="Проверяем статус 404")
        self.assertEqual(first=response.status_code, second=HttpStatus.NOT_FOUND)

    # endregion


class HopperActionAvailabilityTest(TestCase):
    def setUp(self):
        self.user = Steps.create_user(
            username=Users.TEST_DRIVER,
            password=Passwords.DEFAULT,
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name=HopperData.DEFAULT_NAME,
            mass_kg=400.0,
        )

    # region === Позитивные сценарии ===

    def test_all_available_on_fresh_surface_transport(self):
        """BE_P_18 Проверяет доступность действий для нового хоппера на поверхности."""
        # Arrange
        Steps.step(message="Готовим нового хоппера на поверхности")

        # Act
        Steps.step(message="Вычисляем доступность действий")
        allowed = Steps.get_action_availability(hopper=self.hopper)

        # Assert
        Steps.step(message="Проверяем флаги доступности")
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
        Steps.step(message="Переводим хоппера под землю")
        Steps.update_hopper(
            hopper=self.hopper,
            location_state="underground",
        )

        # Act
        Steps.step(message="Вычисляем доступность действий")
        allowed = Steps.get_action_availability(hopper=self.hopper)

        # Assert
        Steps.step(message="Проверяем блокировку по положению")
        self.assertFalse(allowed["basic_jump"])
        self.assertFalse(allowed["long_jump"])
        self.assertFalse(allowed["long_reactor"])
        self.assertFalse(allowed["go_underground"])
        self.assertTrue(allowed["return_to_surface"])
        self.assertTrue(allowed["drill_forward"])

    def test_blocked_by_strength(self):
        """BE_N_19 Проверяет блокировку действий из-за недостатка силы."""
        # Arrange
        Steps.step(message="Снижаем силу хоппера до 12")
        Steps.update_hopper(
            hopper=self.hopper,
            strength=12.0,
        )

        # Act
        Steps.step(message="Вычисляем доступность действий")
        allowed = Steps.get_action_availability(hopper=self.hopper)

        # Assert
        Steps.step(message="Проверяем блокировку по силе")
        self.assertTrue(allowed["basic_jump"])
        self.assertFalse(allowed["long_jump"])
        self.assertFalse(allowed["long_reactor"])
        self.assertTrue(allowed["go_underground"])

    def test_reactor_blocked_by_energy(self):
        """BE_N_20 Проверяет блокировку форсажа из-за недостатка энергии."""
        # Arrange
        Steps.step(message="Снижаем энергию реактора до 40")
        Steps.update_hopper(
            hopper=self.hopper,
            reactor_energy=40.0,
        )

        # Act
        Steps.step(message="Вычисляем доступность действий")
        allowed = Steps.get_action_availability(hopper=self.hopper)

        # Assert
        Steps.step(message="Проверяем блокировку форсажа")
        self.assertTrue(allowed["long_jump"])
        self.assertFalse(allowed["long_reactor"])

    def test_drill_blocked_by_energy_underground(self):
        """BE_N_21 Проверяет блокировку бурения из-за недостатка энергии."""
        # Arrange
        Steps.step(message="Готовим хоппера под землёй с энергией 40")
        Steps.update_hopper(
            hopper=self.hopper,
            location_state="underground",
            reactor_energy=40.0,
        )

        # Act
        Steps.step(message="Вычисляем доступность действий")
        allowed = Steps.get_action_availability(hopper=self.hopper)

        # Assert
        Steps.step(message="Проверяем блокировку бурения")
        self.assertFalse(allowed["drill_forward"])

    # endregion


class HopperGameActionTest(TestCase):
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
        self.client = Client()
        Steps.login(
            client=self.client,
            username=Users.TEST_DRIVER,
            password=Passwords.DEFAULT,
        )

    def _post_game_action(self, action_type: str, **kwargs):
        return Steps.post_action(
            client=self.client,
            hopper_id=self.hopper.id,
            action_type=action_type,
            source="game",
            headers={"HX-Request": "true"},
            **kwargs,
        )

    # region === Позитивные сценарии ===

    def test_game_action_success_returns_panel_and_update_map(self):
        """BE_P_19 Проверяет успешный HTMX-ответ на действие с обновлением карты."""
        # Arrange
        Steps.step(message="Готовим действие basic_jump из игры")

        # Act
        Steps.step(message="Выполняем действие из игрового экрана")
        response = self._post_game_action(action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем панель, карту и состояние хоппера")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertTemplateUsed(
            response=response,
            template_name="hopper/partials/game_panel.html",
        )
        self.assertContains(response=response, text="Дистанция: 10,0")

        trigger = response.headers.get("HX-Trigger")
        self.assertIsNotNone(trigger)
        self.assertIn(member="updateMap", container=trigger)
        self.assertIn(member='"distance": 10.0', container=trigger)

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=10.0)

    def test_panel_keeps_id_after_swap_for_chained_actions(self):
        """BE_P_20 Проверяет сохранение id панели после нескольких действий подряд."""
        # Arrange
        Steps.step(message="Готовим цепочку из двух прыжков")

        # Act
        Steps.step(message="Выполняем первый прыжок")
        first_response = self._post_game_action(action_type="basic_jump")

        Steps.step(message="Выполняем второй прыжок")
        second_response = self._post_game_action(action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем id панели и итоговую дистанцию")
        self.assertEqual(first=first_response.status_code, second=HttpStatus.OK)
        self.assertContains(response=first_response, text='id="game-panel"')

        self.assertEqual(first=second_response.status_code, second=HttpStatus.OK)
        self.assertContains(response=second_response, text="Дистанция: 20,0")

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=20.0)

    def test_reactor_button_disabled_after_energy_spent(self):
        """BE_N_22 Проверяет блокировку форсажа после полного расхода энергии."""
        # Arrange
        Steps.step(message="Готовим два форсажа подряд")

        # Act
        Steps.step(message="Выполняем первый форсаж")
        self._post_game_action(
            action_type="long_jump",
            use_reactor=True,
        )

        Steps.step(message="Выполняем второй форсаж")
        second_response = self._post_game_action(
            action_type="long_jump",
            use_reactor=True,
        )

        Steps.step(message="Пытаемся выполнить третий форсаж")
        third_response = self._post_game_action(
            action_type="long_jump",
            use_reactor=True,
        )

        # Assert
        Steps.step(message="Проверяем энергию и состояние кнопки")
        self.assertEqual(first=second_response.status_code, second=HttpStatus.OK)

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.reactor_energy, second=0.0)

        self.assertContains(
            response=second_response,
            text="Форсаж реактора (+45м)",
        )
        self.assertNotContains(
            response=second_response,
            text="bg-fuchsia-600 hover:bg-fuchsia-700",
        )
        self.assertContains(
            response=second_response,
            text="bg-fuchsia-600 opacity-50 cursor-not-allowed",
        )
        self.assertEqual(
            first=third_response.status_code,
            second=HttpStatus.BAD_REQUEST,
        )

    def test_underground_flow_updates_location(self):
        """BE_P_21 Проверяет переход под землю из игрового экрана."""
        # Arrange
        Steps.step(message="Готовим переход под землю")

        # Act
        Steps.step(message="Выполняем погружение")
        response = self._post_game_action(action_type="go_underground")

        # Assert
        Steps.step(message="Проверяем панель и обновление положения")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertContains(response=response, text="Выйти на поверхность")

        trigger = response.headers.get("HX-Trigger")
        self.assertIn(member='"location_state": "underground"', container=trigger)

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.location_state, second="underground")

    def test_disabled_buttons_render_with_not_allowed_style(self):
        """BE_P_22 Проверяет отрисовку недоступных кнопок после подъёма."""
        # Arrange
        Steps.step(message="Готовим хоппера под землёй с энергией 30")
        Steps.update_hopper(
            hopper=self.hopper,
            location_state="underground",
            reactor_energy=30.0,
        )

        # Act
        Steps.step(message="Возвращаемся на поверхность")
        response = self._post_game_action(action_type="return_to_surface")

        # Assert
        Steps.step(message="Проверяем стили активных и заблокированных кнопок")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertContains(response=response, text="Дистанция: 0,0")
        self.assertNotContains(
            response=response,
            text="bg-emerald-600 hover:bg-emerald-700",
        )
        self.assertNotContains(
            response=response,
            text="bg-stone-700 hover:bg-stone-800",
        )
        self.assertContains(
            response=response,
            text="opacity-50 cursor-not-allowed",
        )

    # endregion

    # region === Негативные сценарии ===

    def test_game_action_error_returns_toast_with_retarget(self):
        """BE_N_23 Проверяет HTMX-ошибку из игрового экрана в виде toast."""
        # Arrange
        Steps.step(message="Готовим недопустимое бурение из игры")

        # Act
        Steps.step(message="Пытаемся бурить на поверхности")
        response = self._post_game_action(action_type="drill_forward")

        # Assert
        Steps.step(message="Проверяем toast и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertTemplateUsed(
            response=response,
            template_name="hopper/partials/toast.html",
        )
        self.assertContains(
            response=response,
            text=(
                "Подземное бурение невозможно на поверхности. "
                "Сначала погрузитесь."
            ),
            status_code=HttpStatus.BAD_REQUEST,
        )
        self.assertEqual(
            first=response.headers.get("HX-Retarget"),
            second="#game-toast-wrap",
        )
        self.assertEqual(
            first=response.headers.get("HX-Reswap"),
            second="innerHTML",
        )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)

    def test_dashboard_action_error_keeps_card_retarget(self):
        """BE_N_24 Проверяет HTMX-ошибку действия с дашборда."""
        # Arrange
        Steps.step(message="Готовим недопустимое действие с дашборда")

        # Act
        Steps.step(message="Выполняем действие с дашборда")
        response = Steps.post_action(
            client=self.client,
            hopper_id=self.hopper.id,
            action_type="drill_forward",
            headers={"HX-Request": "true"},
        )

        # Assert
        Steps.step(message="Проверяем шаблон ошибки и retarget")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertTemplateUsed(
            response=response,
            template_name="hopper/partials/action_error.html",
        )
        self.assertEqual(
            first=response.headers.get("HX-Retarget"),
            second=f"#hopper-error-{self.hopper.id}",
        )

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)

    # endregion
