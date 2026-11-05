from django.test import Client, TestCase
from django.urls import reverse

from apps.common.testing.steps import Steps


class HopperGameScreenTest(TestCase):
    def setUp(self):
        self.user = Steps.create_user(
            username="testdriver",
            password="password",
        )
        self.other_user = Steps.create_user(
            username="other",
            password="password",
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name="Крот-1",
            mass_kg=200.0,
        )
        self.client = Client()
        Steps.login(
            client=self.client,
            username="testdriver",
            password="password",
        )

    # region === Позитивные сценарии ===

    def test_game_screen_renders(self):
        """Проверяет отображение игрового экрана хоппера.

        Предусловия:
            Пользователь testdriver авторизован, хоппер существует.
        Шаги:
            1. Открыть игровой экран хоппера.
        Ожидаемый результат:
            Статус 200, использован game.html, видны основные элементы.
        """
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
        self.assertEqual(first=response.status_code, second=200)
        self.assertTemplateUsed(
            response=response,
            template_name="hopper/game.html",
        )
        self.assertContains(response=response, text=self.hopper.name)
        self.assertContains(response=response, text="Назад в гараж")
        self.assertContains(response=response, text="Подземелье")
        self.assertContains(response=response, text="Обычный прыжок (+10м)")

    def test_state_api_returns_json(self):
        """Проверяет JSON-ответ API состояния хоппера.

        Предусловия:
            Пользователь testdriver авторизован, хоппер существует.
        Шаги:
            1. Запросить состояние хоппера через API.
        Ожидаемый результат:
            Статус 200, JSON содержит имя, дистанцию и положение.
        """
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
        self.assertEqual(first=response.status_code, second=200)

        state = response.json()
        self.assertEqual(first=state["name"], second="Крот-1")
        self.assertEqual(first=state["distance"], second=0.0)
        self.assertEqual(first=state["best_distance"], second=0.0)
        self.assertEqual(first=state["location_state"], second="surface")

    def test_dashboard_card_has_no_action_buttons(self):
        """Проверяет отсутствие игровых кнопок на карточке дашборда.

        Предусловия:
            Пользователь testdriver авторизован.
        Шаги:
            1. Открыть дашборд.
        Ожидаемый результат:
            Есть кнопка запуска заезда, нет кнопок прыжка и бурения.
        """
        # Arrange
        Steps.step(message="Готовим дашборд с карточкой хоппера")

        # Act
        Steps.step(message="Открываем дашборд")
        response = Steps.get_dashboard(client=self.client)

        # Assert
        Steps.step(message="Проверяем наличие и отсутствие кнопок")
        self.assertEqual(first=response.status_code, second=200)
        self.assertContains(response=response, text="Запустить заезд")
        self.assertNotContains(response=response, text="Прыжок")
        self.assertNotContains(response=response, text="Бурить")

    def test_start_race_resets_session_keeps_best_distance(self):
        """Проверяет сброс заезда при открытии игрового экрана.

        Предусловия:
            Хоппер имеет накопленные ресурсы и рекорд 130 м.
        Шаги:
            1. Открыть игровой экран хоппера.
        Ожидаемый результат:
            Ресурсы и дистанция сброшены, рекорд сохранён.
        """
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
        self.assertEqual(first=response.status_code, second=200)

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=0.0)
        self.assertEqual(first=updated_hopper.strength, second=100.0)
        self.assertEqual(first=updated_hopper.reactor_energy, second=100.0)
        self.assertEqual(first=updated_hopper.location_state, second="surface")
        self.assertEqual(first=updated_hopper.best_distance, second=130.0)

    def test_start_race_service(self):
        """Проверяет сброс заезда через сервис start_race.

        Предусловия:
            Хоппер на дистанции 55 м с рекордом 55 м.
        Шаги:
            1. Вызвать сервис start_race.
        Ожидаемый результат:
            Дистанция сброшена, рекорд сохранён.
        """
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
        """Проверяет редирект на вход для неавторизованного пользователя.

        Предусловия:
            Пользователь вышел из системы.
        Шаги:
            1. Открыть игровой экран хоппера.
        Ожидаемый результат:
            Статус 302, редирект на страницу входа.
        """
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
        self.assertEqual(first=response.status_code, second=302)
        self.assertIn(member=reverse("login"), container=response.url)

    def test_game_screen_forbidden_for_other_user(self):
        """Проверяет запрет доступа к чужому игровому экрану.

        Предусловия:
            Хоппер принадлежит пользователю testdriver.
        Шаги:
            1. Открыть игровой экран от имени пользователя other.
        Ожидаемый результат:
            Статус 404.
        """
        # Arrange
        Steps.step(message="Авторизуемся под другим пользователем")
        Steps.login(
            client=self.client,
            username="other",
            password="password",
        )

        # Act
        Steps.step(message="Пытаемся открыть чужой игровой экран")
        response = Steps.get_game_screen(
            client=self.client,
            hopper_id=self.hopper.id,
        )

        # Assert
        Steps.step(message="Проверяем статус 404")
        self.assertEqual(first=response.status_code, second=404)

    # endregion


class HopperActionAvailabilityTest(TestCase):
    def setUp(self):
        self.user = Steps.create_user(
            username="testdriver",
            password="password",
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name="Крот-1",
            mass_kg=400.0,
        )

    # region === Позитивные сценарии ===

    def test_all_available_on_fresh_surface_transport(self):
        """Проверяет доступность действий для нового хоппера на поверхности.

        Предусловия:
            Хоппер на поверхности, сила и энергия по 100, масса 400 кг.
        Шаги:
            1. Вычислить доступность действий.
        Ожидаемый результат:
            Доступны прыжки и погружение, недоступны подъём и бурение.
        """
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
        """Проверяет блокировку действий из-за положения под землёй.

        Предусловия:
            Хоппер находится под землёй.
        Шаги:
            1. Вычислить доступность действий.
        Ожидаемый результат:
            Доступны подъём и бурение, прыжки и погружение недоступны.
        """
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
        """Проверяет блокировку действий из-за недостатка силы.

        Предусловия:
            Сила хоппера равна 12, масса 400 кг.
        Шаги:
            1. Вычислить доступность действий.
        Ожидаемый результат:
            Доступны basic_jump и go_underground, long_jump недоступен.
        """
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
        """Проверяет блокировку форсажа из-за недостатка энергии.

        Предусловия:
            Энергия реактора равна 40.
        Шаги:
            1. Вычислить доступность действий.
        Ожидаемый результат:
            long_jump доступен, long_reactor недоступен.
        """
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
        """Проверяет блокировку бурения из-за недостатка энергии.

        Предусловия:
            Хоппер под землёй, энергия реактора равна 40.
        Шаги:
            1. Вычислить доступность действий.
        Ожидаемый результат:
            drill_forward недоступен.
        """
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
            username="testdriver",
            password="password",
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name="Крот-1",
            mass_kg=200.0,
        )
        self.client = Client()
        Steps.login(
            client=self.client,
            username="testdriver",
            password="password",
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
        """Проверяет успешный HTMX-ответ на действие с обновлением карты.

        Предусловия:
            Пользователь авторизован, хоппер на поверхности.
        Шаги:
            1. Выполнить basic_jump из игрового экрана.
        Ожидаемый результат:
            Статус 200, обновлена панель, HX-Trigger содержит updateMap.
        """
        # Arrange
        Steps.step(message="Готовим действие basic_jump из игры")

        # Act
        Steps.step(message="Выполняем действие из игрового экрана")
        response = self._post_game_action(action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем панель, карту и состояние хоппера")
        self.assertEqual(first=response.status_code, second=200)
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
        """Проверяет сохранение id панели после нескольких действий подряд.

        Предусловия:
            Пользователь авторизован, хоппер на поверхности.
        Шаги:
            1. Выполнить basic_jump.
            2. Повторно выполнить basic_jump по обновлённой панели.
        Ожидаемый результат:
            Панель сохраняет id game-panel, дистанция равна 20 м.
        """
        # Arrange
        Steps.step(message="Готовим цепочку из двух прыжков")

        # Act
        Steps.step(message="Выполняем первый прыжок")
        first_response = self._post_game_action(action_type="basic_jump")

        Steps.step(message="Выполняем второй прыжок")
        second_response = self._post_game_action(action_type="basic_jump")

        # Assert
        Steps.step(message="Проверяем id панели и итоговую дистанцию")
        self.assertEqual(first=first_response.status_code, second=200)
        self.assertContains(response=first_response, text='id="game-panel"')

        self.assertEqual(first=second_response.status_code, second=200)
        self.assertContains(response=second_response, text="Дистанция: 20,0")

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.distance, second=20.0)

    def test_reactor_button_disabled_after_energy_spent(self):
        """Проверяет блокировку форсажа после полного расхода энергии.

        Предусловия:
            Энергия реактора равна 100.
        Шаги:
            1. Выполнить два long_jump с форсажем.
            2. Попытаться выполнить третий форсаж.
        Ожидаемый результат:
            Энергия равна 0, кнопка заблокирована, третье действие даёт 400.
        """
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
        self.assertEqual(first=second_response.status_code, second=200)

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
        self.assertEqual(first=third_response.status_code, second=400)

    def test_underground_flow_updates_location(self):
        """Проверяет переход под землю из игрового экрана.

        Предусловия:
            Пользователь авторизован, хоппер на поверхности.
        Шаги:
            1. Выполнить go_underground из игрового экрана.
        Ожидаемый результат:
            Статус 200, панель показывает выход, HX-Trigger обновляет положение.
        """
        # Arrange
        Steps.step(message="Готовим переход под землю")

        # Act
        Steps.step(message="Выполняем погружение")
        response = self._post_game_action(action_type="go_underground")

        # Assert
        Steps.step(message="Проверяем панель и обновление положения")
        self.assertEqual(first=response.status_code, second=200)
        self.assertContains(response=response, text="Выйти на поверхность")

        trigger = response.headers.get("HX-Trigger")
        self.assertIn(member='"location_state": "underground"', container=trigger)

        updated_hopper = Steps.reload_hopper(hopper=self.hopper)
        self.assertEqual(first=updated_hopper.location_state, second="underground")

    def test_disabled_buttons_render_with_not_allowed_style(self):
        """Проверяет отрисовку недоступных кнопок после подъёма.

        Предусловия:
            Хоппер под землёй, энергия реактора равна 30.
        Шаги:
            1. Выполнить return_to_surface из игрового экрана.
        Ожидаемый результат:
            Поверхность активна, недоступные кнопки имеют стиль блокировки.
        """
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
        self.assertEqual(first=response.status_code, second=200)
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
        """Проверяет HTMX-ошибку из игрового экрана в виде toast.

        Предусловия:
            Хоппер на поверхности.
        Шаги:
            1. Выполнить drill_forward из игрового экрана.
        Ожидаемый результат:
            Статус 400, toast с ошибкой, состояние хоппера не изменилось.
        """
        # Arrange
        Steps.step(message="Готовим недопустимое бурение из игры")

        # Act
        Steps.step(message="Пытаемся бурить на поверхности")
        response = self._post_game_action(action_type="drill_forward")

        # Assert
        Steps.step(message="Проверяем toast и отсутствие изменений")
        self.assertEqual(first=response.status_code, second=400)
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
            status_code=400,
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
        """Проверяет HTMX-ошибку действия с дашборда.

        Предусловия:
            Пользователь авторизован, хоппер на поверхности.
        Шаги:
            1. Выполнить drill_forward без источника game.
        Ожидаемый результат:
            Статус 400, ошибка адресована карточке хоппера.
        """
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
        self.assertEqual(first=response.status_code, second=400)
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
