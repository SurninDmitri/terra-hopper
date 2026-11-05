from __future__ import annotations

import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import Browser, BrowserContext, Page, Playwright
from playwright.sync_api import sync_playwright

from apps.common.testing.constants import ServiceAccount
from apps.common.testing.steps import Steps
from apps.common.testing.ui.steps import StepsUI


def _env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


class PlaywrightLiveServerTestCase(StaticLiveServerTestCase):
    """Django-тест с временной БД, live-сервером и браузером Playwright.

    Sync Playwright запускает event loop в текущем потоке, из-за чего Django
    запрещает синхронный ORM. На время UI-тестов защита отключается.

    Окружение:
        UI_HEADLESS=false — показать окно браузера.
        UI_SLOW_MO=500 — замедлить действия Playwright на 500 мс.

    Значения можно задать в `.env` или в терминале. Переменные терминала
    имеют приоритет над `.env`.
    """

    headless = _env_flag(name="UI_HEADLESS", default=True)
    slow_mo = int(os.environ.get("UI_SLOW_MO", "0"))
    viewport = {"width": 1440, "height": 900}

    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page
    ui: StepsUI
    _async_unsafe_was_set: bool
    _async_unsafe_value: str | None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._async_unsafe_was_set = "DJANGO_ALLOW_ASYNC_UNSAFE" in os.environ
        cls._async_unsafe_value = os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE")
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=cls.headless,
            slow_mo=cls.slow_mo,
        )

    @classmethod
    def tearDownClass(cls):
        try:
            cls.browser.close()
            cls.playwright.stop()
        finally:
            if cls._async_unsafe_was_set:
                os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = cls._async_unsafe_value or ""
            else:
                os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)
            super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.context = self.browser.new_context(
            base_url=self.live_server_url,
            viewport=self.viewport,
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(7000)
        self.ui = StepsUI(
            page=self.page,
            base_url=self.live_server_url,
        )

    def tearDown(self):
        self.context.close()
        super().tearDown()


class ServiceUserUiTestCase(PlaywrightLiveServerTestCase):
    """UI-тест с готовой сервисной учётной записью.

    Пользователь создаётся перед каждым тестом, поэтому тесты остаются
    изолированными, но всегда используют одинаковые логин и пароль.
    """

    def setUp(self):
        super().setUp()
        self.service_user = Steps.create_user(
            username=ServiceAccount.USERNAME,
            password=ServiceAccount.PASSWORD,
        )

    def login_as_service_user(self) -> None:
        """Авторизует сервисную учётку через форму входа."""
        self.ui.login(
            username=ServiceAccount.USERNAME,
            password=ServiceAccount.PASSWORD,
        )
