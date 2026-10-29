from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class AccountsViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_success_sets_jwt_cookies_and_redirects(self):
        resp = self.client.post(
            reverse('register'),
            {'username': 'newuser', 'password': 'StrongPass123', 'password_confirm': 'StrongPass123'},
        )
        self.assertRedirects(resp, reverse('hopper:dashboard'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

        access = resp.cookies.get('access_token')
        refresh = resp.cookies.get('refresh_token')
        self.assertIsNotNone(access)
        self.assertIsNotNone(refresh)
        self.assertTrue(access['httponly'])
        self.assertEqual(access['samesite'], 'Lax')
        self.assertTrue(refresh['httponly'])

    def test_register_password_mismatch_shows_error(self):
        resp = self.client.post(
            reverse('register'),
            {'username': 'newuser', 'password': 'StrongPass123', 'password_confirm': 'OtherPass456'},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Пароли не совпадают', resp.content.decode())
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_register_duplicate_username_shows_error(self):
        User.objects.create_user(username='taken', password='StrongPass123')
        resp = self.client.post(
            reverse('register'),
            {'username': 'taken', 'password': 'StrongPass123', 'password_confirm': 'StrongPass123'},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('уже существует', resp.content.decode())

    def test_login_success_sets_jwt_cookies_and_redirects(self):
        User.objects.create_user(username='driver', password='StrongPass123')

        resp = self.client.post(reverse('login'), {'username': 'driver', 'password': 'StrongPass123'})
        self.assertRedirects(resp, reverse('hopper:dashboard'))
        self.assertIsNotNone(resp.cookies.get('access_token'))
        self.assertIsNotNone(resp.cookies.get('refresh_token'))

    def test_login_wrong_password_shows_error(self):
        User.objects.create_user(username='driver', password='StrongPass123')

        resp = self.client.post(reverse('login'), {'username': 'driver', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)
        self.assertTrue(resp.context['form'].errors)

    def test_logout_deletes_cookies_and_redirects(self):
        User.objects.create_user(username='driver', password='StrongPass123')
        self.client.post(reverse('login'), {'username': 'driver', 'password': 'StrongPass123'})

        resp = self.client.post(reverse('logout'))
        self.assertRedirects(resp, reverse('login'))
        self.assertEqual(resp.cookies['access_token'].value, '')
        self.assertEqual(resp.cookies['refresh_token'].value, '')

    def test_index_redirects_to_login_when_anonymous(self):
        resp = self.client.get(reverse('index'))
        self.assertRedirects(resp, reverse('login'))

    def test_index_redirects_to_dashboard_when_authenticated(self):
        User.objects.create_user(username='driver', password='StrongPass123')
        self.client.login(username='driver', password='StrongPass123')

        resp = self.client.get(reverse('index'))
        self.assertRedirects(resp, reverse('hopper:dashboard'))


class JWTMiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='driver', password='StrongPass123')

    def test_access_token_in_cookie_authenticates_request(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = str(RefreshToken.for_user(self.user).access_token)
        resp = self.client.get(reverse('index'), HTTP_COOKIE=f'access_token={token}')
        self.assertRedirects(resp, reverse('hopper:dashboard'))
