# Правила написания автотестов (АТ)

Документ обязателен для всех новых и изменяемых автотестов проекта.

## 1. Стек и общие принципы

- Используем штатный Django: `django.test.TestCase`, `django.test.Client`, `reverse`, тестовую БД.
- Не используем pytest, pytest-фикстуры и Allure.
- Главный критерий — читаемость. Тест должен читаться как сценарий на языке предметной области, а не как набор технических вызовов.
- Один тест проверяет одно поведение или один сценарий.
- Тест — это документация. По docstring и шагам должно быть понятно, что проверяется и почему.
- Инфраструктурные детали (HTTP, ORM, URL, cookies) прячем в общий `Steps`.
- Ожидания и проверки остаются в тесте: тест должен явно показывать, что именно он проверяет.

## 2. Docstring для каждого теста

У каждого теста обязателен docstring на русском языке. Он заменяет `allure.title` и объясняет сценарий без чтения кода.

Шаблон:

```python
def test_basic_jump_success(self):
    """Проверяет, что обычный прыжок увеличивает дистанцию на 10 м.

    Предусловия:
        Хоппер на поверхности, сила 100, дистанция 0.
    Шаги:
        1. Выполнить обычный прыжок.
    Ожидаемый результат:
        distance=10.0, strength=95.0, best_distance=10.0.
    """
```

Требования:

- Язык — русский.
- Docstring короткий: 3–8 строк.
- В docstring описываем поведение, а не перечисление вызовов.
- Не дублируем имя теста дословно, а объясняем суть.

## 3. Структура теста: Arrange / Act / Assert

Каждый тест обязан иметь три явные части:

```python
# Arrange
# Act
# Assert
```

- `Arrange` — подготовка пользователя, хоппера, состояния БД.
- `Act` — одно бизнес-действие.
- `Assert` — проверка ответа, состояния объекта и записей в БД.

Нельзя смешивать подготовку и проверки. Если в `Assert` нужно изменить данные — это уже другой сценарий.

## 4. Именованные аргументы

Если у вызова больше одного аргумента, передаём их по имени.

Правильно:

```python
Steps.create_hopper(
    user=self.user,
    name="Крот-1",
    mass_kg=200.0,
)
```

Неправильно:

```python
Steps.create_hopper(self.user, "Крот-1", 200.0)
```

Правила:

- Для методов `Steps`, `Client`, `reverse`, assertion-методов используем именованные аргументы.
- Исключение: вызовы с одним аргументом и стандартные языковые конструкции.
- Для `assertEqual` используем `first=` и `second=`, для `assertContains` — `response=` и `text=`, для `assertIn` — `member=` и `container=` и т.д.

Примеры:

```python
response = Steps.post_action(
    client=self.client,
    hopper_id=self.hopper.id,
    action_type="basic_jump",
)

self.assertEqual(first=response.status_code, second=200)
self.assertContains(
    response=response,
    text="Дистанция: 10,0",
)
```

## 5. Доменные имена переменных

Запрещены безликие имена: `resp`, `h`, `obj`, `tmp`, `data2`, `x`.

Используем:

| Плохо | Хорошо |
|---|---|
| `resp` | `response` |
| `h` | `hopper` |
| `updated` | `updated_hopper` |
| `created` | `created_hopper` |
| `d` | `distance` |
| `e` | `error` / `exception` |
| `flag` | `is_available` / `has_energy` |

Правила:

- Имя переменной должно объяснять её роль в сценарии.
- Для фактических и ожидаемых значений используем `actual_*` и `expected_*`.
- Для ответов сервера — `response`, для объектов БД — `hopper`, `user`, `created_hopper`.

## 6. Позитивные и негативные сценарии

Позитивные и негативные сценарии не смешиваем.

Внутри одного класса используем регионы:

```python
# region === Позитивные сценарии ===

def test_basic_jump_success(self):
    ...

# endregion

# region === Негативные сценарии ===

def test_basic_jump_underground_raises(self):
    ...

# endregion
```

Если тестов много, выносим негативные сценарии в отдельный класс:

```python
class HopperActionsPositiveTest(TestCase):
    ...

class HopperActionsNegativeTest(TestCase):
    ...
```

Требования к негативным тестам:

- Проверяем тип исключения или HTTP-статус.
- Проверяем текст ошибки, если он является частью контракта.
- Проверяем, что нежелательные изменения в БД не произошли.

## 7. Общий Steps

Общий фасад для всего проекта: `apps/common/testing/steps.py`.

Импорт:

```python
from apps.common.testing.steps import Steps
```

Правила:

- Все бизнес-действия в тестах выполняем через `Steps`.
- В тестах не должно быть «сырых» `self.client.post`, `reverse`, `execute_hopper_action`, `Hopper.objects.create`, если для этого есть метод `Steps`.
- `Steps` скрывает инфраструктуру, но не скрывает ожидания: проверки остаются в тесте.
- Новые методы добавляем в `Steps` по мере необходимости, а не дублируем код в тестах.

Основные методы:

```python
Steps.step(message="...")

Steps.create_user(username="driver", password="StrongPass123")
Steps.login(client=self.client, username="driver", password="StrongPass123")
Steps.logout_session(client=self.client)

Steps.register(
    client=self.client,
    username="driver",
    password="StrongPass123",
    password_confirm="StrongPass123",
)
Steps.login_user(client=self.client, username="driver", password="StrongPass123")
Steps.logout_user(client=self.client)
Steps.get_index(client=self.client)

Steps.create_hopper(user=self.user, name="Крот-1", mass_kg=200.0)
Steps.create_hopper_for_user(user=self.user, name="Крот-1", mass_kg=200.0)
Steps.update_hopper(hopper=self.hopper, distance=95.0)
Steps.reload_hopper(hopper=self.hopper)
Steps.create_hopper_via_endpoint(client=self.client, name="Крот-1", mass_kg=200.0)

Steps.get_dashboard(client=self.client)
Steps.get_game_screen(client=self.client, hopper_id=self.hopper.id)
Steps.get_state(client=self.client, hopper_id=self.hopper.id)
Steps.get_action(client=self.client, hopper_id=self.hopper.id)

Steps.post_action(
    client=self.client,
    hopper_id=self.hopper.id,
    action_type="basic_jump",
)
Steps.perform_action(
    hopper_id=self.hopper.id,
    user=self.user,
    action_type="basic_jump",
)
Steps.start_race(hopper_id=self.hopper.id, user=self.user)
Steps.get_action_availability(hopper=self.hopper)
```

## 8. Аналог allure_step и логирование

Вместо `allure_step` используем:

```python
Steps.step(message="Создаём хоппера с массой 200 кг")
```

`Steps.step` — единая точка для будущего логирования. Сейчас он пишет шаг в лог, позже сюда можно подключить Allure или другой репортер.

Требования:

- Каждый логический шаг теста сопровождается `Steps.step(...)`.
- Сообщения — на русском, короткие и по делу.
- В сообщениях не должно быть секретов, токенов и лишних технических деталей.
- Не используем `print` для логирования.

Логи пишутся в `logs/` в корне проекта. Формат — дерево вызовов методов `Steps` с длительностью и признаком успеха/ошибки:

```text
10:00:00 | << Создаём пользователя >>
10:00:00 | create_user...
10:00:00 | create_user -> [0:00:00]
10:00:00 | << Выполняем обычный прыжок >>
10:00:00 | perform_action...
10:00:00 | perform_action -> [0:00:00]
```

При ошибке:

```text
10:00:00 | perform_action -> FAILED [0:00:00] InvalidLocationError: Прыжок невозможен
```

Ничего лишнего в лог не пишем: только шаги, вызовы методов, длительность и успех/ошибка.

## 9. Проверки ответа и БД

- Для HTML используем `assertContains` / `assertNotContains`, а не `assertIn` по `response.content.decode()`.
- Для JSON используем `response.json()` или `assertJSONEqual`.
- Для редиректов используем `assertRedirects`.
- Для шаблонов — `assertTemplateUsed`.
- Для состояния БД — `refresh_from_db()` через `Steps.reload_hopper(...)` или ORM-запросы.
- Для проверки существования записи — `Model.objects.filter(...).exists()`.

Пример:

```python
# Assert
self.assertEqual(first=response.status_code, second=200)
self.assertContains(
    response=response,
    text="Дистанция: 10,0",
)

updated_hopper = Steps.reload_hopper(hopper=self.hopper)
self.assertEqual(first=updated_hopper.distance, second=10.0)
```

## 10. URL и HTTP-клиент

- URL получаем через `reverse`, а не хардкодим строкой.
- Для запросов используем методы `Steps`, а не `self.client` напрямую.
- Заголовки передаём явно: `headers={"HX-Request": "true"}`.
- Для JWT в cookie допускается `HTTP_COOKIE=f"access_token={token}"`.

## 11. Пример правильного теста

```python
def test_basic_jump_success(self):
    """Проверяет, что обычный прыжок увеличивает дистанцию на 10 м.

    Предусловия:
        Хоппер на поверхности, сила 100, дистанция 0.
    Шаги:
        1. Выполнить обычный прыжок.
    Ожидаемый результат:
        distance=10.0, strength=95.0, best_distance=10.0.
    """
    # Arrange
    Steps.step(message="Создаём хоппера для прыжка")
    hopper = Steps.create_hopper(
        user=self.user,
        name="Крот-1",
        mass_kg=200.0,
    )

    # Act
    Steps.step(message="Выполняем обычный прыжок")
    updated_hopper = Steps.perform_action(
        hopper_id=hopper.id,
        user=self.user,
        action_type="basic_jump",
    )

    # Assert
    Steps.step(message="Проверяем дистанцию, силу и рекорд")
    self.assertEqual(first=updated_hopper.distance, second=10.0)
    self.assertEqual(first=updated_hopper.strength, second=95.0)
    self.assertEqual(first=updated_hopper.best_distance, second=10.0)
```

## 12. Чек-лист нового АТ

- [ ] Есть docstring на русском.
- [ ] Есть `# Arrange`, `# Act`, `# Assert`.
- [ ] Все многоаргументные вызовы используют именованные аргументы.
- [ ] Переменные названы по-доменному.
- [ ] Позитивные и негативные сценарии не смешаны.
- [ ] Используется `Steps`, а не сырые вызовы инфраструктуры.
- [ ] На каждом логическом шаге вызван `Steps.step(...)`.
- [ ] URL получен через `reverse`.
- [ ] HTML проверяется через `assertContains`, JSON — через `response.json()` / `assertJSONEqual`.
- [ ] Состояние БД проверено через `refresh_from_db()` или ORM.
- [ ] Негативный тест проверяет и ошибку, и отсутствие нежелательных изменений.

## 13. Запуск тестов

Все тесты:

```bash
python manage.py test apps.accounts apps.hopper -v 2
```

Отдельный модуль:

```bash
python manage.py test apps.hopper.tests.test_actions -v 2
```

Отдельный класс:

```bash
python manage.py test apps.hopper.tests.test_actions.HopperActionsServiceTest -v 2
```

Отдельный тест:

```bash
python manage.py test apps.hopper.tests.test_actions.HopperActionsServiceTest.test_basic_jump_success -v 2
```

Полезные флаги:

- `--keepdb` — не пересоздавать тестовую БД.
- `--parallel` — параллельный запуск.
- `--failfast` — остановиться на первом падении.
- `--durations 10` — показать самые медленные тесты.

## 14. Запуск в PyCharm

Через `manage.py`:

1. `Run` → `Edit Configurations…` → `+` → `Python`.
2. Указать:
   - **Script path**: `<корень проекта>/manage.py`
   - **Parameters**: `test apps.accounts apps.hopper -v 2`
   - **Working directory**: корень проекта
   - **Python interpreter**: `.venv`
3. Запуск — `Shift+F10`, отладка — `Shift+F9`.

Через Django tests:

1. `Settings` → `Languages & Frameworks` → `Django` → включить поддержку.
2. Указать `config/settings.py` и `manage.py`.
3. `Run` → `Edit Configurations…` → `+` → `Django tests`.
4. В **Target** указать `apps.hopper.tests` или конкретный класс/метод.

## 15. UI-тесты на Playwright

UI-тесты используют Django `StaticLiveServerTestCase`: поднимается локальный сервер и временная тестовая БД, реальная `db.sqlite3` не затрагивается.

Установка:

```bash
pip install -r requirements.txt
playwright install chromium
```

Структура инфраструктуры:

```text
apps/common/testing/ui/
├── base_element.py      # действия и проверки над элементом
├── base_page.py         # открытие страницы и поиск элементов
├── pages/               # страницы и их элементы
│   ├── login_page.py
│   ├── dashboard_page.py
│   └── game_page.py
├── steps.py             # StepsUI — действия для АТ
└── test_case.py         # PlaywrightLiveServerTestCase
```

Правила:

- Элементы и селекторы храним только в классах страниц `apps/common/testing/ui/pages/`.
- В тестах не должно быть `page.locator(...)`, CSS-селекторов и `get_by_role(...)`.
- Пользовательские действия оформляем методами `StepsUI`: `login`, `start_race`, `perform_basic_jump` и т.д.
- Проверки UI оформляем методами `StepsUI` или страниц: `assert_distance`, `assert_hopper_visible`.
- Каждый логический шаг теста сопровождаем `Steps.step(...)`.
- Тестовые данные создаём через обычный `Steps` до начала UI-сценария.
- UI-тест наследуем от `PlaywrightLiveServerTestCase`, браузер и `self.ui` создаются автоматически.

Пример:

```python
from apps.common.testing.steps import Steps
from apps.common.testing.ui.test_case import PlaywrightLiveServerTestCase


class HopperGameUiTest(PlaywrightLiveServerTestCase):
    def setUp(self):
        super().setUp()
        self.user = Steps.create_user(
            username="ui-driver",
            password="StrongPass123",
        )
        self.hopper = Steps.create_hopper(
            user=self.user,
            name="Крот-UI",
            mass_kg=200.0,
        )

    def test_basic_jump_from_game_screen(self):
        """Проверяет обычный прыжок через игровой интерфейс."""
        # Arrange
        Steps.step(message="Готовим пользователя и хоппера")

        # Act
        Steps.step(message="Авторизуемся через форму входа")
        self.ui.login(
            username="ui-driver",
            password="StrongPass123",
        )

        Steps.step(message="Запускаем заезд с дашборда")
        self.ui.start_race(hopper_name=self.hopper.name)

        Steps.step(message="Выполняем обычный прыжок")
        self.ui.perform_basic_jump()

        # Assert
        Steps.step(message="Проверяем дистанцию и рекорд")
        self.ui.assert_distance(expected_distance="10.0")
        self.ui.assert_record(expected_record="10.0")
```

Запуск:

```bash
python manage.py test apps.hopper.tests.test_ui -v 2
```

Настройка через `.env`:

```bash
cp .env.example .env
```

В `.env`:

```dotenv
UI_HEADLESS=false
UI_SLOW_MO=500
```

`config/settings.py` загружает `.env` через `python-dotenv`. Переменные, заданные
в терминале или CI, имеют приоритет над значениями из `.env`.

Посмотреть, как работает браузер:

```bash
UI_HEADLESS=false UI_SLOW_MO=500 \
  python manage.py test apps.hopper.tests.test_ui -v 2
```

Переменные окружения:

- `UI_HEADLESS` — `true` по умолчанию, `false` показывает окно браузера.
- `UI_SLOW_MO` — задержка действий Playwright в миллисекундах, по умолчанию `0`.

Особенность: sync Playwright запускает event loop в текущем потоке, поэтому `PlaywrightLiveServerTestCase` на время UI-тестов выставляет `DJANGO_ALLOW_ASYNC_UNSAFE=true` и восстанавливает прежнее значение после класса.
