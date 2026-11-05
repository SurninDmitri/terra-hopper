from __future__ import annotations

import contextvars
import functools
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from apps.hopper.models import Hopper
from apps.hopper.services import (
    compute_action_availability,
    create_hopper_for_user as create_hopper_service,
    execute_hopper_action,
    start_race as start_race_service,
)


_LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
_LOGGER_NAME = "terra_hopper.at"
_INDENT = contextvars.ContextVar("at_indent", default=0)
_LOGGER: logging.Logger | None = None


def _format_duration(seconds: float) -> str:
    total_seconds = int(seconds)
    minutes, seconds_rest = divmod(total_seconds, 60)
    hours, minutes_rest = divmod(minutes, 60)
    return f"{hours}:{minutes_rest:02d}:{seconds_rest:02d}"


def _get_logger() -> logging.Logger:
    global _LOGGER

    if _LOGGER is not None:
        return _LOGGER

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_name = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}_None.log"
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(filename=_LOG_DIR / log_name, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(fmt="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)

    _LOGGER = logger
    return logger


def logged_method(method: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(method)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = _get_logger()
        indent = _INDENT.get()
        prefix = "  " * indent
        method_name = method.__name__
        started_at = time.perf_counter()

        logger.info("%s%s...", prefix, method_name)
        token = _INDENT.set(indent + 1)
        try:
            result = method(*args, **kwargs)
        except Exception as error:
            duration = _format_duration(time.perf_counter() - started_at)
            logger.info(
                "%s%s -> FAILED [%s] %s: %s",
                prefix,
                method_name,
                duration,
                type(error).__name__,
                error,
            )
            raise
        else:
            duration = _format_duration(time.perf_counter() - started_at)
            logger.info("%s%s -> [%s]", prefix, method_name, duration)
            return result
        finally:
            _INDENT.reset(token)

    return wrapper


class Steps:
    """Общий фасад для автотестов проекта."""

    @staticmethod
    def step(message: str) -> None:
        """Аналог allure_step: единая точка для логирования шагов."""
        indent = "  " * _INDENT.get()
        _get_logger().info("%s<< %s >>", indent, message)

    @staticmethod
    @logged_method
    def create_user(username: str, password: str) -> User:
        return User.objects.create_user(username=username, password=password)

    @staticmethod
    @logged_method
    def create_access_token(user: User) -> str:
        return str(RefreshToken.for_user(user).access_token)

    @staticmethod
    @logged_method
    def login(client: Client, username: str, password: str) -> bool:
        return client.login(username=username, password=password)

    @staticmethod
    @logged_method
    def logout_session(client: Client) -> None:
        client.logout()

    @staticmethod
    @logged_method
    def register(
        client: Client,
        username: str,
        password: str,
        password_confirm: str,
    ) -> HttpResponse:
        return client.post(
            path=reverse("register"),
            data={
                "username": username,
                "password": password,
                "password_confirm": password_confirm,
            },
        )

    @staticmethod
    @logged_method
    def login_user(client: Client, username: str, password: str) -> HttpResponse:
        return client.post(
            path=reverse("login"),
            data={"username": username, "password": password},
        )

    @staticmethod
    @logged_method
    def logout_user(client: Client) -> HttpResponse:
        return client.post(path=reverse("logout"))

    @staticmethod
    @logged_method
    def get_index(
        client: Client,
        headers: dict[str, str] | None = None,
        **extra: Any,
    ) -> HttpResponse:
        return client.get(
            path=reverse("index"),
            headers=headers or {},
            **extra,
        )

    @staticmethod
    @logged_method
    def build_hopper(
        user: User,
        name: str,
        mass_kg: float,
        **overrides: Any,
    ) -> Hopper:
        fields: dict[str, Any] = {
            "strength": 100.0,
            "reactor_energy": 100.0,
            "location_state": "surface",
            "distance": 0.0,
            "best_distance": 0.0,
        }
        fields.update(overrides)
        return Hopper(
            user=user,
            name=name,
            mass_kg=mass_kg,
            **fields,
        )

    @staticmethod
    @logged_method
    def create_hopper(
        user: User,
        name: str,
        mass_kg: float,
        **overrides: Any,
    ) -> Hopper:
        hopper = Steps.build_hopper(
            user=user,
            name=name,
            mass_kg=mass_kg,
            **overrides,
        )
        hopper.save()
        return hopper

    @staticmethod
    @logged_method
    def save_hopper(hopper: Hopper) -> Hopper:
        hopper.save()
        return hopper

    @staticmethod
    @logged_method
    def create_hopper_for_user(user: User, name: str, mass_kg: float) -> Hopper:
        return create_hopper_service(user=user, name=name, mass_kg=mass_kg)

    @staticmethod
    @logged_method
    def update_hopper(hopper: Hopper, **fields: Any) -> Hopper:
        for field_name, value in fields.items():
            setattr(hopper, field_name, value)
        hopper.save()
        return hopper

    @staticmethod
    @logged_method
    def reload_hopper(hopper: Hopper) -> Hopper:
        hopper.refresh_from_db()
        return hopper

    @staticmethod
    @logged_method
    def create_hopper_via_endpoint(
        client: Client,
        name: str,
        mass_kg: float | str,
    ) -> HttpResponse:
        return client.post(
            path=reverse("hopper:create_hopper"),
            data={"name": name, "mass_kg": mass_kg},
        )

    @staticmethod
    @logged_method
    def get_dashboard(client: Client) -> HttpResponse:
        return client.get(path=reverse("hopper:dashboard"))

    @staticmethod
    @logged_method
    def get_game_screen(client: Client, hopper_id: int) -> HttpResponse:
        return client.get(path=reverse("hopper:game", args=[hopper_id]))

    @staticmethod
    @logged_method
    def get_state(client: Client, hopper_id: int) -> HttpResponse:
        return client.get(path=reverse("hopper:state_api", args=[hopper_id]))

    @staticmethod
    @logged_method
    def get_action(client: Client, hopper_id: int) -> HttpResponse:
        return client.get(path=reverse("hopper:action", args=[hopper_id]))

    @staticmethod
    @logged_method
    def post_action(
        client: Client,
        hopper_id: int,
        action_type: str,
        use_reactor: bool = False,
        source: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        payload: dict[str, str] = {"action_type": action_type}
        if use_reactor:
            payload["use_reactor"] = "true"
        if source is not None:
            payload["source"] = source

        return client.post(
            path=reverse("hopper:action", args=[hopper_id]),
            data=payload,
            headers=headers or {},
        )

    @staticmethod
    @logged_method
    def perform_action(
        hopper_id: int,
        user: User,
        action_type: str,
        use_reactor: bool = False,
    ) -> Hopper:
        return execute_hopper_action(
            hopper_id=hopper_id,
            user=user,
            action_type=action_type,
            use_reactor=use_reactor,
        )

    @staticmethod
    @logged_method
    def start_race(hopper_id: int, user: User) -> Hopper:
        return start_race_service(hopper_id=hopper_id, user=user)

    @staticmethod
    @logged_method
    def get_action_availability(hopper: Hopper) -> dict[str, bool]:
        return compute_action_availability(hopper=hopper)
