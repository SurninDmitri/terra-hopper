from __future__ import annotations

from playwright.sync_api import Page

from apps.common.testing.ui.base_element import BaseElement


class BasePage:
    """Базовая страница: открытие URL и поиск элементов."""

    def __init__(
        self,
        page: Page,
        base_url: str,
        path: str | None = None,
    ):
        self.page = page
        self.base_url = base_url
        self.path = path

    @property
    def url(self) -> str:
        return self.page.url

    def open(self) -> None:
        if not self.path:
            raise ValueError("Для страницы не задан path")
        self.page.goto(url=f"{self.base_url}{self.path}", wait_until="domcontentloaded")

    def sleep(self, seconds: float = 1) -> None:
        self.page.wait_for_timeout(seconds * 1000)

    def find_by_css(self, selector: str, description: str | None = None) -> BaseElement:
        return BaseElement(
            locator=self.page.locator(selector),
            description=description or selector,
        )

    def find_by_xpath(self, selector: str, description: str | None = None) -> BaseElement:
        return BaseElement(
            locator=self.page.locator(f"xpath={selector}"),
            description=description or selector,
        )

    def find_by_label(self, label: str, description: str | None = None) -> BaseElement:
        return BaseElement(
            locator=self.page.get_by_label(label),
            description=description or label,
        )

    def find_by_test_id(
        self,
        test_id: str,
        description: str | None = None,
    ) -> BaseElement:
        return BaseElement(
            locator=self.page.get_by_test_id(test_id),
            description=description or test_id,
        )

    def find_by_role(
        self,
        role: str,
        name: str | None = None,
        description: str | None = None,
    ) -> BaseElement:
        return BaseElement(
            locator=self.page.get_by_role(role, name=name),
            description=description or name or role,
        )

    def assert_url_contains(self, expected: str, timeout_ms: int = 5000) -> None:
        self.page.wait_for_url(f"**{expected}**", timeout=timeout_ms)
