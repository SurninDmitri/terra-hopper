from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from apps.common.testing.constants import HopperData, HttpStatus
from apps.common.testing.steps import Steps
from apps.hopper.models import Hopper


class HopperModelTest(TestCase):
    def setUp(self):
        self.user = Steps.create_user(username="test", password="pass")

    # region === Позитивные сценарии ===

    def test_create_hopper_valid(self):
        """DB_P_1 Проверяет создание хоппера с корректными полями."""
        # Arrange
        Steps.step(message="Готовим корректные данные хоппера")

        # Act
        Steps.step(message="Создаём хоппера")
        hopper = Steps.create_hopper(
            user=self.user,
            name="Hopper1",
            mass_kg=HopperData.DEFAULT_MASS_KG,
        )

        # Assert
        Steps.step(message="Проверяем сохранённые поля")
        self.assertEqual(first=hopper.name, second="Hopper1")
        self.assertEqual(first=hopper.mass_kg, second=HopperData.DEFAULT_MASS_KG)
        self.assertEqual(first=hopper.strength, second=100.0)

    # endregion

    # region === Негативные сценарии ===

    def test_name_empty_raises(self):
        """DB_N_1 Проверяет ошибку сохранения хоппера с пустым именем."""
        # Arrange
        Steps.step(message="Создаём хоппера с пустым именем")
        invalid_hopper = Steps.build_hopper(
            user=self.user,
            name="   ",
            mass_kg=HopperData.DEFAULT_MASS_KG,
        )

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        # Assert
        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=invalid_hopper)
        self.assertFalse(Hopper.objects.exists())

    def test_mass_below_minimum_raises(self):
        """DB_N_2 Проверяет ошибку сохранения при массе ниже допустимой."""
        # Arrange
        Steps.step(message="Создаём хоппера с массой ниже минимума")
        invalid_hopper = Steps.build_hopper(
            user=self.user,
            name="H",
            mass_kg=50.0,
        )

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        # Assert
        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=invalid_hopper)
        self.assertFalse(Hopper.objects.exists())

    def test_mass_above_maximum_raises(self):
        """DB_N_3 Проверяет ошибку сохранения при массе выше допустимой."""
        # Arrange
        Steps.step(message="Создаём хоппера с массой выше максимума")
        invalid_hopper = Steps.build_hopper(
            user=self.user,
            name="H",
            mass_kg=600.0,
        )

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        # Assert
        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=invalid_hopper)
        self.assertFalse(Hopper.objects.exists())

    def test_strength_range_raises(self):
        """DB_N_4 Проверяет ошибку сохранения при отрицательной силе."""
        # Arrange
        Steps.step(message="Создаём хоппера с отрицательной силой")
        invalid_hopper = Steps.build_hopper(
            user=self.user,
            name="H",
            mass_kg=HopperData.DEFAULT_MASS_KG,
            strength=-1.0,
        )

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        # Assert
        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=invalid_hopper)
        self.assertFalse(Hopper.objects.exists())

    def test_reactor_energy_range_raises(self):
        """DB_N_5 Проверяет ошибку сохранения при энергии реактора больше 100."""
        # Arrange
        Steps.step(message="Создаём хоппера с избыточной энергией реактора")
        invalid_hopper = Steps.build_hopper(
            user=self.user,
            name="H",
            mass_kg=HopperData.DEFAULT_MASS_KG,
            reactor_energy=101.0,
        )

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        # Assert
        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=invalid_hopper)
        self.assertFalse(Hopper.objects.exists())

    # endregion


class HopperCreateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Steps.create_user(username="u", password="pass")
        Steps.login(
            client=self.client,
            username="u",
            password="pass",
        )

    # region === Позитивные сценарии ===

    def test_service_create(self):
        """BE_P_23 Проверяет создание хоппера через сервис."""
        # Arrange
        Steps.step(message="Готовим данные для сервиса создания")

        # Act
        Steps.step(message="Создаём хоппера через сервис")
        hopper = Steps.create_hopper_for_user(
            user=self.user,
            name="Test",
            mass_kg=250.0,
        )

        # Assert
        Steps.step(message="Проверяем имя и массу хоппера")
        self.assertEqual(first=hopper.name, second="Test")
        self.assertEqual(first=hopper.mass_kg, second=250.0)

    def test_create_view_success(self):
        """BE_P_24 Проверяет успешное создание хоппера через HTTP-эндпоинт."""
        # Arrange
        Steps.step(message="Готовим данные для создания через эндпоинт")

        # Act
        Steps.step(message="Создаём хоппера через эндпоинт")
        response = Steps.create_hopper_via_endpoint(
            client=self.client,
            name="MyHopper",
            mass_kg="300",
        )

        # Assert
        Steps.step(message="Проверяем ответ и запись в БД")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertTrue(
            Hopper.objects.filter(user=self.user, name="MyHopper").exists(),
        )

    # endregion

    # region === Негативные сценарии ===

    def test_service_empty_name(self):
        """BE_N_25 Проверяет ошибку сервиса при пустом имени хоппера."""
        # Arrange
        Steps.step(message="Готовим пустое имя")

        # Act
        Steps.step(message="Пытаемся создать хоппера через сервис")

        # Assert
        with self.assertRaises(ValueError) as context:
            Steps.create_hopper_for_user(
                user=self.user,
                name="   ",
                mass_kg=HopperData.DEFAULT_MASS_KG,
            )
        self.assertIn(
            member="Имя не может быть пустым",
            container=str(context.exception),
        )
        self.assertFalse(Hopper.objects.exists())

    def test_service_mass_below_minimum(self):
        """BE_N_26 Проверяет ошибку сервиса при массе ниже допустимой."""
        # Arrange
        Steps.step(message="Готовим массу ниже минимума")

        # Act
        Steps.step(message="Пытаемся создать хоппера через сервис")

        # Assert
        with self.assertRaises(ValueError) as context:
            Steps.create_hopper_for_user(
                user=self.user,
                name="Test",
                mass_kg=50.0,
            )
        self.assertIn(
            member="Масса должна быть в диапазоне",
            container=str(context.exception),
        )
        self.assertFalse(Hopper.objects.exists())

    def test_service_mass_above_maximum(self):
        """BE_N_27 Проверяет ошибку сервиса при массе выше допустимой."""
        # Arrange
        Steps.step(message="Готовим массу выше максимума")

        # Act
        Steps.step(message="Пытаемся создать хоппера через сервис")

        # Assert
        with self.assertRaises(ValueError) as context:
            Steps.create_hopper_for_user(
                user=self.user,
                name="Test",
                mass_kg=600.0,
            )
        self.assertIn(
            member="Масса должна быть в диапазоне",
            container=str(context.exception),
        )
        self.assertFalse(Hopper.objects.exists())

    def test_create_view_error(self):
        """BE_N_28 Проверяет ошибку HTTP-эндпоинта при пустом имени."""
        # Arrange
        Steps.step(message="Готовим пустое имя для эндпоинта")

        # Act
        Steps.step(message="Пытаемся создать хоппера через эндпоинт")
        response = Steps.create_hopper_via_endpoint(
            client=self.client,
            name="",
            mass_kg="200",
        )

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие записи")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertContains(
            response=response,
            text="Имя не может быть пустым",
            status_code=HttpStatus.BAD_REQUEST,
        )
        self.assertFalse(Hopper.objects.exists())

    # endregion
