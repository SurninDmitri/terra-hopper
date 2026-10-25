# Crazy Transport

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
