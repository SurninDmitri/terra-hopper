from django.core.exceptions import ValidationError

from apps.common.testing.cases import UserTestCase
from apps.common.testing.constants import HopperData, HttpStatus
from apps.common.testing.steps import Steps
from apps.hopper.models import Hopper


class HopperModelTest(UserTestCase):
    username = "test"
    password = "pass"

    # region === Позитивные сценарии ===

    def test_create_hopper_valid(self):
        """DB_P_1 Проверяет создание хоппера с корректными полями."""
        # Arrange
        Steps.step(message="Готовим корректные данные хоппера")

        # Act
        Steps.step(message="Создаём хоппера")
        hopper = Steps.create_hopper(user=self.user,
                                     name="Hopper1",
                                     mass_kg=HopperData.DEFAULT_MASS_KG)

        # Assert
        Steps.step(message="Проверяем сохранённые поля")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=hopper,
                                  expected_name="Hopper1",
                                  expected_mass_kg=HopperData.DEFAULT_MASS_KG,
                                  expected_strength=100.0)

    # endregion


class HopperModelValidationTest(UserTestCase):
    username = "test"
    password = "pass"

    def setUp(self):
        super().setUp()
        Steps.step(message="Готовим несохранённого хоппера для проверки валидации")
        self.invalid_hopper = Steps.build_hopper(user=self.user,
                                                 name="H",
                                                 mass_kg=HopperData.DEFAULT_MASS_KG)

    # region === Негативные сценарии ===

    def test_name_empty_raises(self):
        """DB_N_1 Проверяет ошибку сохранения хоппера с пустым именем."""
        # Arrange
        Steps.step(message="Создаём хоппера с пустым именем")
        self.invalid_hopper.name = "   "

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=self.invalid_hopper)

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertFalse(Hopper.objects.exists())

    def test_mass_below_minimum_raises(self):
        """DB_N_2 Проверяет ошибку сохранения при массе ниже допустимой."""
        # Arrange
        Steps.step(message="Создаём хоппера с массой ниже минимума")
        self.invalid_hopper.mass_kg = 50.0

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=self.invalid_hopper)

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertFalse(Hopper.objects.exists())

    def test_mass_above_maximum_raises(self):
        """DB_N_3 Проверяет ошибку сохранения при массе выше допустимой."""
        # Arrange
        Steps.step(message="Создаём хоппера с массой выше максимума")
        self.invalid_hopper.mass_kg = 600.0

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=self.invalid_hopper)

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertFalse(Hopper.objects.exists())

    def test_strength_range_raises(self):
        """DB_N_4 Проверяет ошибку сохранения при отрицательной силе."""
        # Arrange
        Steps.step(message="Создаём хоппера с отрицательной силой")
        self.invalid_hopper.strength = -1.0

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=self.invalid_hopper)

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertFalse(Hopper.objects.exists())

    def test_reactor_energy_range_raises(self):
        """DB_N_5 Проверяет ошибку сохранения при энергии реактора больше 100."""
        # Arrange
        Steps.step(message="Создаём хоппера с избыточной энергией реактора")
        self.invalid_hopper.reactor_energy = 101.0

        # Act
        Steps.step(message="Пытаемся сохранить хоппера")

        with self.assertRaises(ValidationError):
            Steps.save_hopper(hopper=self.invalid_hopper)

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertFalse(Hopper.objects.exists())

    # endregion


class HopperCreateViewTest(UserTestCase):
    username = "u"
    password = "pass"

    def setUp(self):
        super().setUp()
        self.login_as_user()

    # region === Позитивные сценарии ===

    def test_create_hopper_success(self):
        """BE_P_23 Проверяет создание хоппера через HTTP-эндпоинт."""
        # Arrange
        Steps.step(message="Готовим данные для создания хоппера")

        # Act
        Steps.step(message="Создаём хоппера через форму")
        response = Steps.create_hopper_via_endpoint(client=self.client,
                                                    name="Test",
                                                    mass_kg=250.0)

        # Assert
        Steps.step(message="Проверяем ответ, сохранённые имя и массу хоппера")
        self.assertEqual(first=response.status_code, second=HttpStatus.OK)
        self.assertTrue(Hopper.objects.filter(user=self.user, name="Test").exists())
        hopper = Hopper.objects.get(user=self.user, name="Test")
        Steps.assert_hopper_state(test_case=self,
                                  hopper=hopper,
                                  expected_name="Test",
                                  expected_mass_kg=250.0)

    # endregion

    # region === Негативные сценарии ===

    def test_empty_name_returns_error(self):
        """BE_N_25 Проверяет ошибку при пустом имени хоппера."""
        # Arrange
        Steps.step(message="Готовим имя из пробелов для формы создания")

        # Act
        Steps.step(message="Пытаемся создать хоппера через форму")
        response = Steps.create_hopper_via_endpoint(client=self.client,
                                                    name="   ",
                                                    mass_kg=HopperData.DEFAULT_MASS_KG)

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие записи")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertIn(member="Имя не может быть пустым",
                      container=response.context["error"])
        self.assertContains(response=response,
                            text="Имя не может быть пустым",
                            status_code=HttpStatus.BAD_REQUEST)
        self.assertFalse(Hopper.objects.exists())

    def test_mass_below_minimum(self):
        """BE_N_26 Проверяет ошибку формы при массе ниже допустимой."""
        # Arrange
        Steps.step(message="Готовим массу ниже минимума")

        # Act
        Steps.step(message="Пытаемся создать хоппера через форму")

        response = Steps.create_hopper_via_endpoint(client=self.client,
                                                    name="Test",
                                                    mass_kg=50.0)

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertIn(member="Масса должна быть в диапазоне",
                      container=response.context["error"])
        self.assertFalse(Hopper.objects.exists())

    def test_mass_above_maximum(self):
        """BE_N_27 Проверяет ошибку формы при массе выше допустимой."""
        # Arrange
        Steps.step(message="Готовим массу выше максимума")

        # Act
        Steps.step(message="Пытаемся создать хоппера через форму")

        response = Steps.create_hopper_via_endpoint(client=self.client,
                                                    name="Test",
                                                    mass_kg=600.0)

        # Assert
        Steps.step(message="Проверяем ошибку и отсутствие нежелательных изменений")
        self.assertEqual(first=response.status_code, second=HttpStatus.BAD_REQUEST)
        self.assertIn(member="Масса должна быть в диапазоне",
                      container=response.context["error"])
        self.assertFalse(Hopper.objects.exists())

    # endregion
