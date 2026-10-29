from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from apps.hopper.models import Hopper
from apps.hopper.services import compute_action_availability, start_race


class HopperGameScreenTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testdriver', password='password')
        self.other_user = User.objects.create_user(username='other', password='password')
        self.hopper = Hopper.objects.create(
            user=self.user,
            name='Крот-1',
            mass_kg=200.0,
        )
        self.client.login(username='testdriver', password='password')

    def test_game_screen_renders(self):
        response = self.client.get(reverse('hopper:game', args=[self.hopper.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hopper/game.html')
        self.assertContains(response, self.hopper.name)
        self.assertContains(response, 'Назад в гараж')
        self.assertContains(response, 'Подземелье')
        self.assertContains(response, 'Обычный прыжок (+10м)')

    def test_game_screen_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('hopper:game', args=[self.hopper.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_game_screen_forbidden_for_other_user(self):
        self.client.login(username='other', password='password')
        response = self.client.get(reverse('hopper:game', args=[self.hopper.id]))
        self.assertEqual(response.status_code, 404)

    def test_state_api_returns_json(self):
        response = self.client.get(reverse('hopper:state_api', args=[self.hopper.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Крот-1')
        self.assertEqual(data['distance'], 0.0)
        self.assertEqual(data['best_distance'], 0.0)
        self.assertEqual(data['location_state'], 'surface')

    def test_dashboard_card_has_no_action_buttons(self):
        response = self.client.get(reverse('hopper:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Запустить заезд')
        self.assertNotContains(response, 'Прыжок')
        self.assertNotContains(response, 'Бурить')

    def test_start_race_resets_session_keeps_best_distance(self):
        self.hopper.distance = 120.0
        self.hopper.strength = 40.0
        self.hopper.reactor_energy = 30.0
        self.hopper.location_state = 'underground'
        self.hopper.best_distance = 130.0
        self.hopper.save()

        response = self.client.get(reverse('hopper:game', args=[self.hopper.id]))
        self.assertEqual(response.status_code, 200)

        self.hopper.refresh_from_db()
        self.assertEqual(self.hopper.distance, 0.0)
        self.assertEqual(self.hopper.strength, 100.0)
        self.assertEqual(self.hopper.reactor_energy, 100.0)
        self.assertEqual(self.hopper.location_state, 'surface')
        self.assertEqual(self.hopper.best_distance, 130.0)

    def test_start_race_service(self):
        self.hopper.distance = 55.0
        self.hopper.strength = 10.0
        self.hopper.best_distance = 55.0
        self.hopper.save()
        started = start_race(self.hopper.id, self.user)
        self.assertEqual(started.distance, 0.0)
        self.assertEqual(started.best_distance, 55.0)


class HopperActionAvailabilityTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testdriver', password='password')
        self.hopper = Hopper.objects.create(
            user=self.user,
            name='Крот-1',
            mass_kg=400.0,
        )

    def test_all_available_on_fresh_surface_transport(self):
        allowed = compute_action_availability(self.hopper)
        self.assertTrue(allowed['basic_jump'])
        self.assertTrue(allowed['long_jump'])
        self.assertTrue(allowed['long_reactor'])
        self.assertTrue(allowed['go_underground'])
        self.assertFalse(allowed['return_to_surface'])
        self.assertFalse(allowed['drill_forward'])

    def test_blocked_by_location(self):
        self.hopper.location_state = 'underground'
        allowed = compute_action_availability(self.hopper)
        self.assertFalse(allowed['basic_jump'])
        self.assertFalse(allowed['long_jump'])
        self.assertFalse(allowed['long_reactor'])
        self.assertFalse(allowed['go_underground'])
        self.assertTrue(allowed['return_to_surface'])
        self.assertTrue(allowed['drill_forward'])

    def test_blocked_by_strength(self):
        self.hopper.strength = 12.0
        allowed = compute_action_availability(self.hopper)
        # basic: 3 + 4 = 7 <= 12 OK
        self.assertTrue(allowed['basic_jump'])
        # long: 10 + 8 = 18 > 12
        self.assertFalse(allowed['long_jump'])
        self.assertFalse(allowed['long_reactor'])
        # underground: 3 * 4 = 12 <= 12 OK
        self.assertTrue(allowed['go_underground'])

    def test_reactor_blocked_by_energy(self):
        self.hopper.reactor_energy = 40.0
        allowed = compute_action_availability(self.hopper)
        self.assertTrue(allowed['long_jump'])
        self.assertFalse(allowed['long_reactor'])

    def test_drill_blocked_by_energy_underground(self):
        self.hopper.location_state = 'underground'
        self.hopper.reactor_energy = 40.0
        allowed = compute_action_availability(self.hopper)
        self.assertFalse(allowed['drill_forward'])


class HopperGameActionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testdriver', password='password')
        self.hopper = Hopper.objects.create(
            user=self.user,
            name='Крот-1',
            mass_kg=200.0,
        )
        self.client.login(username='testdriver', password='password')

    def _post_action(self, payload):
        return self.client.post(
            reverse('hopper:action', args=[self.hopper.id]),
            payload,
            headers={'HX-Request': 'true'},
        )

    def test_game_action_success_returns_panel_and_update_map(self):
        response = self._post_action({'action_type': 'basic_jump', 'source': 'game'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hopper/partials/game_panel.html')
        self.assertContains(response, 'Дистанция: 10,0')
        trigger = response.headers.get('HX-Trigger')
        self.assertIsNotNone(trigger)
        self.assertIn('updateMap', trigger)
        self.assertIn('"distance": 10.0', trigger)
        self.hopper.refresh_from_db()
        self.assertEqual(self.hopper.distance, 10.0)

    def test_panel_keeps_id_after_swap_for_chained_actions(self):
        first = self._post_action({'action_type': 'basic_jump', 'source': 'game'})
        self.assertEqual(first.status_code, 200)
        self.assertContains(first, 'id="game-panel"')
        # Второе действие подряд по новой панели — имитация нескольких кликов
        second = self._post_action({'action_type': 'basic_jump', 'source': 'game'})
        self.assertEqual(second.status_code, 200)
        self.assertContains(second, 'Дистанция: 20,0')
        self.hopper.refresh_from_db()
        self.assertEqual(self.hopper.distance, 20.0)

    def test_reactor_button_disabled_after_energy_spent(self):
        # Два форсажа: 100 -> 50 -> 0 энергии
        self._post_action({'action_type': 'long_jump', 'use_reactor': 'true', 'source': 'game'})
        second = self._post_action({'action_type': 'long_jump', 'use_reactor': 'true', 'source': 'game'})
        self.assertEqual(second.status_code, 200)
        self.hopper.refresh_from_db()
        self.assertEqual(self.hopper.reactor_energy, 0.0)
        # В панели из ответа (энергия 0) кнопка форсажа заблокирована
        self.assertContains(second, 'Форсаж реактора (+45м)')
        self.assertNotContains(second, 'bg-fuchsia-600 hover:bg-fuchsia-700')
        self.assertContains(second, 'bg-fuchsia-600 opacity-50 cursor-not-allowed')
        # Третий форсаж невозможен -> доменная ошибка
        third = self._post_action({'action_type': 'long_jump', 'use_reactor': 'true', 'source': 'game'})
        self.assertEqual(third.status_code, 400)

    def test_game_action_error_returns_toast_with_retarget(self):
        response = self._post_action({'action_type': 'drill_forward', 'source': 'game'})
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, 'hopper/partials/toast.html')
        self.assertContains(
            response,
            'Подземное бурение невозможно на поверхности. Сначала погрузитесь.',
            status_code=400,
        )
        self.assertEqual(response.headers.get('HX-Retarget'), '#game-toast-wrap')
        self.assertEqual(response.headers.get('HX-Reswap'), 'innerHTML')
        self.hopper.refresh_from_db()
        self.assertEqual(self.hopper.distance, 0.0)

    def test_dashboard_action_error_keeps_card_retarget(self):
        response = self._post_action({'action_type': 'drill_forward'})
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, 'hopper/partials/action_error.html')
        self.assertEqual(response.headers.get('HX-Retarget'), f'#hopper-error-{self.hopper.id}')

    def test_underground_flow_updates_location(self):
        response = self._post_action({'action_type': 'go_underground', 'source': 'game'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Выйти на поверхность')
        trigger = response.headers.get('HX-Trigger')
        self.assertIn('"location_state": "underground"', trigger)

    def test_disabled_buttons_render_with_not_allowed_style(self):
        self.hopper.location_state = 'underground'
        self.hopper.reactor_energy = 30.0
        self.hopper.save()
        response = self._post_action({'action_type': 'return_to_surface', 'source': 'game'})
        self.assertEqual(response.status_code, 200)
        # После подъёма на поверхность недоступны прыжки из-под земли невозможны? Нет —
        # на поверхности вновь обязательны прыжки; невозможны только подъём и бурение.
        self.assertContains(response, 'Дистанция: 0,0')
        self.assertNotContains(response, 'bg-emerald-600 hover:bg-emerald-700')
        self.assertNotContains(response, 'bg-stone-700 hover:bg-stone-800')
        self.assertContains(response, 'opacity-50 cursor-not-allowed')
