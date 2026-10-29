# Техническое задание: Инициализация Django-проекта и система аутентификации (JWT + HTMX/Templates)

## 1. Цель
Создать базовый Django-проект с настроенной системой регистрации, входа и выхода пользователей на основе JSON Web Tokens (JWT) с использованием `djangorestframework-simplejwt`. Аутентификация должна быть интегрирована с классическими шаблонами Django и подготовить основу для SPA/HTMX-взаимодействия через HTTP-only Cookies.

---

## 2. Стек и библиотеки
- **Python**: 3.10+
- **Django**: 5.x
- **Django REST Framework**: latest
- **djangorestframework-simplejwt**: latest
- **HTMX** (опционально для асинхронной отправки форм через CDN)

---

## 3. Структура проекта

Проект должен быть организован со следующей структурой каталогов:

```text
crazy_transport/
├── config/                  # Основной модуль настроек Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/                    # Пакет для Django-приложений
│   ├── __init__.py
│   └── accounts/            # Приложение аутентификации и профиля
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── urls.py
│       ├── views.py
│       ├── serializers.py   # JWT serializers (при необходимости)
│       └── forms.py         # Формы Django для входа/регистрации
├── templates/               # Глобальные HTML-шаблоны
│   ├── base.html
│   ├── index.html           # Главная страница (landing/dashboard redirect)
│   └── accounts/
│       ├── login.html
│       └── register.html
├── static/                  # Статические файлы (CSS/JS)
├── manage.py
├── requirements.txt
└── README.md
```

---

## 4. Требования к функционалу

### 4.1. Главная страница (`/`)
- Доступна по маршруту `''` (name: `index`).
- Если пользователь **авторизован** (в сессии / по JWT): отображает приветствие, имя пользователя и кнопку «Выйти».
- Если пользователь **не авторизован**: автоматически перенаправляет на страницу входа (`/accounts/login/`) либо отображает приветственную страницу с ссылками на Вход / Регистрацию.

### 4.2. Регистрация (`/accounts/register/`)
- Доступна по маршруту `/accounts/register/` (name: `register`).
- Принимает `username`, `password`, `password_confirm`.
- Проверяет совпадение паролей и уникальность `username`.
- После успешной регистрации автоматически аутентифицирует пользователя (выдает JWT-токены в HTTP-only cookies) и перенаправляет на главную страницу (`/`).
- В случае ошибки валидации возвращает форму с понятными сообщениями об ошибках.

### 4.3. Авторизация (`/accounts/login/`)
- Доступна по маршруту `/accounts/login/` (name: `login`).
- Принимает `username` и `password`.
- При успешном входе генерирует пары токенов `access` и `refresh` через `SimpleJWT`.
- Сохраняет `access_token` и `refresh_token` в **HTTP-only Cookies** (для защиты от XSS-атак).
- Выполняет редирект на главную страницу (`/`).

### 4.4. Выход из системы (`/accounts/logout/`)
- Доступен по маршруту `/accounts/logout/` (name: `logout`).
- Удаляет JWT-куки (`access_token`, `refresh_token`) и завершает сессию.
- Выполняет редирект на страницу входа.

---

## 5. Архитектурные детали JWT и Cookie Authentication

Чтобы JWT работали прозрачно с HTML-шаблонами Django и HTMX:
1. Написать кастомный Middleware (`JWTInCookieMiddleware` или аутентификатор DRF/Django), который извлекает `access_token` из HTTP-only куки запроса (`request.COOKIES.get('access_token')`) и аутентифицирует пользователя (`request.user`).
2. Настройки cookie:
   - `httponly=True`
   - `samesite='Lax'`
   - `max_age` соответствует сроку жизни токена (например, 15 минут для access, 7 дней для refresh).

---

## 6. Требования к UI/Шаблонам

1. **`base.html`**:
   - Подключает базовые стили (Bootstrap 5 via CDN или простой чистый CSS).
   - Подключает HTMX via CDN (`<script src="https://unpkg.com/htmx.org@1.9.10"></script>`).
   - Содержит блок `{% block content %}{% endblock %}`.
2. **`login.html` & `register.html`**:
   - Чистые, аккуратные формы по центру экрана.
   - Валидационные сообщения под полями ввода.

---

## 7. Файл зависимости (`requirements.txt`)

```text
Django>=5.0,<6.0
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.0
python-dotenv>=1.0.0
```

---

## 8. Инструкция по запуску (для файла README.md)

1. Клонировать репозиторий и перейти в директорию проекта.
2. Создать и активировать виртуальное окружение:
   ```bash
   python -m venv venv
   # Linux/macOS:
   source venv/bin/activate
   # Windows:
   venv\Scripts\activate
   ```
3. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Выполнить миграции:
   ```bash
   python manage.py migrate
   ```
5. Запустить сервер разработки:
   ```bash
   python manage.py runserver
   ```
6. Открыть в браузере: `http://127.0.0.1:8000/`.

---

## 9. Ограничения (Чего делать НЕ нужно)
- **НЕ** создавать никаких дополнительных сущностей, кроме стандартного `User` (или минимальной кастомной модели, если необходимо).
- **НЕ** писать бизнес-логику для транспорта, гаража и игр (это будет сделано на следующих этапах).
- **НЕ** перегружать интерфейс лишней версткой.