"""Общая подготовка пользователей и хопперов для backend-АТ."""

from django.test import TestCase

from apps.common.testing.constants import HopperData, Passwords, Users
from apps.common.testing.steps import Steps


class UserTestCase(TestCase):
    username = Users.TEST_DRIVER
    password = Passwords.DEFAULT

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Steps.step(message=f"Создаём пользователя {cls.username}")
        cls.user = Steps.create_user(username=cls.username,
                                     password=cls.password)

    def login_as_user(self):
        Steps.step(message=f"Авторизуем пользователя {self.user.username}")
        Steps.login(client=self.client,
                    username=self.user.username,
                    password=self.password)


class HopperTestCase(UserTestCase):
    hopper_name = HopperData.DEFAULT_NAME
    hopper_mass_kg = HopperData.DEFAULT_MASS_KG
    hopper_strength = 100.0
    hopper_reactor_energy = 100.0
    hopper_location_state = "surface"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Steps.step(message="Создаём хоппера для пользователя")
        cls.hopper = Steps.create_hopper(user=cls.user,
                                         name=cls.hopper_name,
                                         mass_kg=cls.hopper_mass_kg,
                                         strength=cls.hopper_strength,
                                         reactor_energy=cls.hopper_reactor_energy,
                                         location_state=cls.hopper_location_state)


class AuthenticatedHopperTestCase(HopperTestCase):
    def setUp(self):
        super().setUp()
        self.login_as_user()
