from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.hopper.models import Hopper
from apps.hopper.services import execute_hopper_action
from apps.hopper.domain.exceptions import (
    InvalidLocationError,
    NotEnoughStrengthError,
    NotEnoughEnergyError,
)


class HopperActionsServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testdriver', password='password')
        self.hopper = Hopper.objects.create(
            user=self.user,
            name='Крот-1',
            mass_kg=200.0,
            strength=100.0,
            reactor_energy=100.0,
            location_state='surface',
            distance=0.0,
            best_distance=0.0,
        )

    def test_basic_jump_success(self):
        updated = execute_hopper_action(self.hopper.id, self.user, 'basic_jump')
        self.assertEqual(updated.distance, 10.0)
        self.assertEqual(updated.strength, 95.0)
        self.assertEqual(updated.best_distance, 10.0)

    def test_long_jump_with_reactor_success(self):
        updated = execute_hopper_action(self.hopper.id, self.user, 'long_jump', use_reactor=True)
        self.assertEqual(updated.distance, 45.0)
        self.assertEqual(updated.strength, 86.0)
        self.assertEqual(updated.reactor_energy, 50.0)
        self.assertEqual(updated.best_distance, 45.0)

    def test_drill_forward_on_surface_raises_error(self):
        with self.assertRaises(InvalidLocationError) as ctx:
            execute_hopper_action(self.hopper.id, self.user, 'drill_forward')
        self.assertIn('Подземное бурение невозможно на поверхности', str(ctx.exception))

    def test_not_enough_energy_for_reactor_jump(self):
        self.hopper.reactor_energy = 30.0
        self.hopper.save()

        with self.assertRaises(NotEnoughEnergyError) as ctx:
            execute_hopper_action(self.hopper.id, self.user, 'long_jump', use_reactor=True)
        self.assertIn('Недостаточно энергии реактора для форсажа', str(ctx.exception))

    def test_basic_jump_underground_raises(self):
        self.hopper.location_state = 'underground'
        self.hopper.save()

        with self.assertRaises(InvalidLocationError):
            execute_hopper_action(self.hopper.id, self.user, 'basic_jump')

    def test_not_enough_strength_for_basic_jump(self):
        self.hopper.strength = 1.0
        self.hopper.save()

        with self.assertRaises(NotEnoughStrengthError):
            execute_hopper_action(self.hopper.id, self.user, 'basic_jump')

    def test_go_underground_success(self):
        updated = execute_hopper_action(self.hopper.id, self.user, 'go_underground')
        self.assertEqual(updated.location_state, 'underground')
        self.assertEqual(updated.strength, 94.0)

    def test_return_to_surface_success(self):
        self.hopper.location_state = 'underground'
        self.hopper.strength = 100.0
        self.hopper.save()

        updated = execute_hopper_action(self.hopper.id, self.user, 'return_to_surface')
        self.assertEqual(updated.location_state, 'surface')
        self.assertEqual(updated.strength, 94.0)

    def test_go_underground_twice_raises(self):
        execute_hopper_action(self.hopper.id, self.user, 'go_underground')

        with self.assertRaises(InvalidLocationError):
            execute_hopper_action(self.hopper.id, self.user, 'go_underground')

    def test_drill_forward_success(self):
        execute_hopper_action(self.hopper.id, self.user, 'go_underground')
        updated = execute_hopper_action(self.hopper.id, self.user, 'drill_forward')
        self.assertEqual(updated.distance, 40.0)
        self.assertEqual(updated.strength, 78.0)
        self.assertEqual(updated.reactor_energy, 50.0)
        self.assertEqual(updated.best_distance, 40.0)

    def test_recovery_on_100m_marks(self):
        self.hopper.distance = 95.0
        self.hopper.best_distance = 95.0
        self.hopper.strength = 20.0
        self.hopper.reactor_energy = 20.0
        self.hopper.save()

        updated = execute_hopper_action(self.hopper.id, self.user, 'basic_jump')
        # Crossing 100m mark: +45 - 200/10*0.5 = +35
        self.assertEqual(updated.distance, 105.0)
        self.assertEqual(updated.strength, 50.0)
        self.assertEqual(updated.reactor_energy, 55.0)
        self.assertEqual(updated.best_distance, 105.0)

    def test_unknown_action_raises(self):
        with self.assertRaises(ValueError):
            execute_hopper_action(self.hopper.id, self.user, 'teleport')

    def test_action_on_other_users_hopper_raises_http404(self):
        other_user = User.objects.create_user(username='other', password='password')
        from django.http import Http404
        with self.assertRaises(Http404):
            execute_hopper_action(self.hopper.id, other_user, 'basic_jump')


class HopperActionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testdriver', password='password')
        self.client.login(username='testdriver', password='password')
        self.hopper = Hopper.objects.create(
            user=self.user,
            name='Крот-1',
            mass_kg=200.0,
            strength=100.0,
            reactor_energy=100.0,
            location_state='surface',
            distance=0.0,
            best_distance=0.0,
        )
        self.url = f'/hopper/{self.hopper.id}/action/'

    def test_action_view_success_htmx(self):
        resp = self.client.post(self.url, {'action_type': 'basic_jump'}, HTTP_HX_REQUEST='true')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(f'hopper-card-{self.hopper.id}', resp.content.decode())
        self.assertNotIn('bg-red-50', resp.content.decode())

        self.hopper.refresh_from_db()
        self.assertEqual(self.hopper.distance, 10.0)
        self.assertEqual(self.hopper.strength, 95.0)

    def test_action_view_error_htmx_returns_400(self):
        resp = self.client.post(self.url, {'action_type': 'drill_forward'}, HTTP_HX_REQUEST='true')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Подземное бурение невозможно на поверхности', resp.content.decode())
        self.assertEqual(resp['HX-Retarget'], f'#hopper-error-{self.hopper.id}')

    def test_action_view_error_json(self):
        resp = self.client.post(self.url, {'action_type': 'drill_forward'})
        self.assertEqual(resp.status_code, 400)
        self.assertJSONEqual(resp.content, {'error': 'Подземное бурение невозможно на поверхности. Сначала погрузитесь.'})

    def test_action_view_requires_login(self):
        self.client.logout()
        resp = self.client.post(self.url, {'action_type': 'basic_jump'})
        self.assertEqual(resp.status_code, 302)

    def test_action_view_get_not_allowed(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)
