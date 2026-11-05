"""Общие константы автотестов."""


class Users:
    """Часто используемые логины тестовых пользователей."""

    TEST_DRIVER = "testdriver"
    ACCOUNT = "driver"


class Passwords:
    """Часто используемые пароли тестовых пользователей."""

    DEFAULT = "password"
    STRONG = "StrongPass123"


class ServiceAccount:
    """Сервисная учётка для UI-тестов без проверки авторизации."""

    USERNAME = "ui-service"
    PASSWORD = Passwords.STRONG


class HopperData:
    """Часто используемые данные хоппера."""

    DEFAULT_NAME = "Крот-1"
    DEFAULT_MASS_KG = 200.0


class HttpStatus:
    """HTTP-статусы, используемые в проверках."""

    OK = 200
    FOUND = 302
    BAD_REQUEST = 400
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
