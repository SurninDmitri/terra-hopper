from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.hopper.models import Hopper
from apps.hopper import services


class HopperModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='pass')

    def test_create_hopper_valid(self):
        hopper = Hopper.objects.create(
            user=self.user,
            name='Hopper1',
            mass_kg=200.0,
            strength=100.0,
            reactor_energy=100.0,
        )
        self.assertEqual(hopper.name, 'Hopper1')

    def test_name_empty_raises(self):
        hopper = Hopper(user=self.user, name='   ', mass_kg=200.0, strength=100.0, reactor_energy=100.0)
        with self.assertRaises(ValidationError):
            hopper.save()

    def test_mass_range(self):
        hopper = Hopper(user=self.user, name='H', mass_kg=50.0, strength=100.0, reactor_energy=100.0)
        with self.assertRaises(ValidationError):
            hopper.save()
        hopper2 = Hopper(user=self.user, name='H', mass_kg=600.0, strength=100.0, reactor_energy=100.0)
        with self.assertRaises(ValidationError):
            hopper2.save()

    def test_strength_range(self):
        hopper = Hopper(user=self.user, name='H', mass_kg=200.0, strength=-1.0, reactor_energy=100.0)
        with self.assertRaises(ValidationError):
            hopper.save()

    def test_reactor_energy_range(self):
        hopper = Hopper(user=self.user, name='H', mass_kg=200.0, strength=100.0, reactor_energy=101.0)
        with self.assertRaises(ValidationError):
            hopper.save()


class HopperCreateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='u', password='pass')
        self.client.login(username='u', password='pass')

    def test_service_create(self):
        h = services.create_hopper_for_user(self.user, 'Test', 250.0)
        self.assertEqual(h.name, 'Test')
        self.assertEqual(h.mass_kg, 250.0)

    def test_service_empty_name(self):
        with self.assertRaises(ValueError):
            services.create_hopper_for_user(self.user, '   ', 200.0)

    def test_service_bad_mass(self):
        with self.assertRaises(ValueError):
            services.create_hopper_for_user(self.user, 'Test', 50.0)
        with self.assertRaises(ValueError):
            services.create_hopper_for_user(self.user, 'Test', 600.0)

    def test_create_view_success(self):
        resp = self.client.post('/hopper/create/', {'name': 'MyHopper', 'mass_kg': '300'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Hopper.objects.filter(user=self.user, name='MyHopper').exists())

    def test_create_view_error(self):
        resp = self.client.post('/hopper/create/', {'name': '', 'mass_kg': '200'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Имя не может быть пустым', resp.content.decode())
