from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from apps.common.testing.steps import Steps
from apps.hopper.models import Hopper


class HopperModelTest(TestCase):
    def setUp(self):
        self.user = Steps.create_user(username="test", password="pass")

    # region === Позитивные сценарии ===

    def test_create_hopper_valid(self):
        """Проверяет создание хоппера с корректными полями.

        Предусловия:
            Пользователь test существует.
        Шаги:
            1. Создать хоппера с массой 200 кг.
        Ожидаемый результат:
            Хоппер сохранён с указанными именем и массой.
        """
        # Arrange
        Steps.step(message="Готовим корректные данные хоппера")

        # Act
        Steps.step(message="Создаём хоппера")
        hopper = Steps.create_hopper(
            user=self.user,
            name="Hopper1",
            mass_kg=200.0,
        )

        # Assert
        Steps.step(message="Проверяем сохранённые поля")
        self.assertEqual(first=hopper.name, second="Hopper1")
        self.assertEqual(first=hopper.mass_kg, second=200.0)
        self.assertEqual(first=hopper.strength, second=100.0)

    # endregion

    # region === Негативные сценарии ===

    def test_name_empty_raises(self):
        """Проверяет ошибку сохранения хоппера с пустым именем.

        Предусловия:
            Пользователь test существует.
        Шаги:
            1. Попытаться сохранить хоппера с именем из пробелов.
        Ожидаемый результат:
            Выброшено ValidationError, запись не создана.
        """
        # Arrange
        Steps.step(message="Создаём хоппера с пустым именем")
        invalid_hopper = Steps.build_hopper(
            user=self.user,
            name="   ",
            mass_kg=200.0,
        )

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        # Assert
        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=invalid_hopper)
        self.assertFalse(Hopper.objects.exists())

    def test_mass_below_minimum_raises(self):
        """Проверяет ошибку сохранения при массе ниже допустимой.

        Предусловия:
            Пользователь test существует.
        Шаги:
            1. Попытаться сохранить хоппера с массой 50 кг.
        Ожидаемый результат:
            Выброшено ValidationError, запись не создана.
        """
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
        """Проверяет ошибку сохранения при массе выше допустимой.

        Предусловия:
            Пользователь test существует.
        Шаги:
            1. Попытаться сохранить хоппера с массой 600 кг.
        Ожидаемый результат:
            Выброшено ValidationError, запись не создана.
        """
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
        """Проверяет ошибку сохранения при отрицательной силе.

        Предусловия:
            Пользователь test существует.
        Шаги:
            1. Попытаться сохранить хоппера с силой -1.
        Ожидаемый результат:
            Выброшено ValidationError, запись не создана.
        """
        # Arrange
        Steps.step(message="Создаём хоппера с отрицательной силой")
        invalid_hopper = Steps.build_hopper(
            user=self.user,
            name="H",
            mass_kg=200.0,
            strength=-1.0,
        )

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        # Assert
        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=invalid_hopper)
        self.assertFalse(Hopper.objects.exists())

    def test_reactor_energy_range_raises(self):
        """Проверяет ошибку сохранения при энергии реактора больше 100.

        Предусловия:
            Пользователь test существует.
        Шаги:
            1. Попытаться сохранить хоппера с энергией 101.
        Ожидаемый результат:
            Выброшено ValidationError, запись не создана.
        """
        # Arrange
        Steps.step(message="Создаём хоппера с избыточной энергией реактора")
        invalid_hopper = Steps.build_hopper(
            user=self.user,
            name="H",
            mass_kg=200.0,
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
        """Проверяет создание хоппера через сервис.

        Предусловия:
            Пользователь u существует.
        Шаги:
            1. Создать хоппера через create_hopper_for_user.
        Ожидаемый результат:
            Хоппер сохранён с именем Test и массой 250 кг.
        """
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
        """Проверяет успешное создание хоппера через HTTP-эндпоинт.

        Предусловия:
            Пользователь u авторизован.
        Шаги:
            1. Отправить форму создания хоппера.
        Ожидаемый результат:
            Статус 200, хоппер сохранён в БД.
        """
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
        self.assertEqual(first=response.status_code, second=200)
        self.assertTrue(
            Hopper.objects.filter(user=self.user, name="MyHopper").exists(),
        )

    # endregion

    # region === Негативные сценарии ===

    def test_service_empty_name(self):
        """Проверяет ошибку сервиса при пустом имени хоппера.

        Предусловия:
            Пользователь u существует.
        Шаги:
            1. Создать хоппера с именем из пробелов.
        Ожидаемый результат:
            Выброшено ValueError, хоппер не создан.
        """
        # Arrange
        Steps.step(message="Готовим пустое имя")

        # Act
        Steps.step(message="Пытаемся создать хоппера через сервис")

        # Assert
        with self.assertRaises(ValueError) as context:
            Steps.create_hopper_for_user(
                user=self.user,
                name="   ",
                mass_kg=200.0,
            )
        self.assertIn(
            member="Имя не может быть пустым",
            container=str(context.exception),
        )
        self.assertFalse(Hopper.objects.exists())

    def test_service_mass_below_minimum(self):
        """Проверяет ошибку сервиса при массе ниже допустимой.

        Предусловия:
            Пользователь u существует.
        Шаги:
            1. Создать хоппера с массой 50 кг.
        Ожидаемый результат:
            Выброшено ValueError, хоппер не создан.
        """
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
        """Проверяет ошибку сервиса при массе выше допустимой.

        Предусловия:
            Пользователь u существует.
        Шаги:
            1. Создать хоппера с массой 600 кг.
        Ожидаемый результат:
            Выброшено ValueError, хоппер не создан.
        """
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
        """Проверяет ошибку HTTP-эндпоинта при пустом имени.

        Предусловия:
            Пользователь u авторизован.
        Шаги:
            1. Отправить форму создания с пустым именем.
        Ожидаемый результат:
            Статус 400, показана ошибка, хоппер не создан.
        """
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
        self.assertEqual(first=response.status_code, second=400)
        self.assertContains(
            response=response,
            text="Имя не может быть пустым",
            status_code=400,
        )
        self.assertFalse(Hopper.objects.exists())

    # endregion
