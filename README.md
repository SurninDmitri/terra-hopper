# Crazy Transport

[![CI](https://github.com/SurninDmitri/terra-hopper/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SurninDmitri/terra-hopper/actions/workflows/ci.yml)

## CI

При каждом push в `main` и pull request GitHub Actions устанавливает зависимости и Chromium,
после чего запускает все тесты проекта.

## Установка и запуск

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

6. Открыть в браузере: `http://127.0.0.1:8000/`
