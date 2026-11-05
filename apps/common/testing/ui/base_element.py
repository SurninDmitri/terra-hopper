from __future__ import annotations

from playwright.sync_api import Locator, expect


class BaseElement:
    """Обёртка над Playwright Locator с явными действиями и проверками."""

    def __init__(
        self,
        locator: Locator,
        description: str,
        timeout_ms: int = 5000,
    ):
        self._locator = locator
        self.description = description
        self.timeout_ms = timeout_ms

    @property
    def locator(self) -> Locator:
        return self._locator

    @property
    def text(self) -> str:
        return self._locator.inner_text()

    @property
    def is_visible(self) -> bool:
        return self._locator.is_visible()

    @property
    def is_enabled(self) -> bool:
        return self._locator.is_enabled()

    @property
    def count(self) -> int:
        return self._locator.count()

    @property
    def first(self) -> BaseElement:
        return self.nth(index=0)

    def nth(self, index: int) -> BaseElement:
        return BaseElement(
            locator=self._locator.nth(index),
            description=f"{self.description}[{index}]",
            timeout_ms=self.timeout_ms,
        )

    def click(self) -> None:
        self._locator.click()

    def fill(self, text: str) -> None:
        self._locator.fill(str(text))

    def press(self, key: str) -> None:
        self._locator.press(key)

    def get_attribute(self, name: str) -> str | None:
        return self._locator.get_attribute(name)

    def wait_for_visible(self, timeout_ms: int | None = None) -> None:
        expect(self._locator).to_be_visible(timeout=timeout_ms or self.timeout_ms)

    def wait_for_hidden(self, timeout_ms: int | None = None) -> None:
        expect(self._locator).to_be_hidden(timeout=timeout_ms or self.timeout_ms)

    def wait_for_detached(self, timeout_ms: int | None = None) -> None:
        expect(self._locator).to_have_count(0, timeout=timeout_ms or self.timeout_ms)

    def assert_visible(self, timeout_ms: int | None = None) -> None:
        expect(self._locator).to_be_visible(timeout=timeout_ms or self.timeout_ms)

    def assert_hidden(self, timeout_ms: int | None = None) -> None:
        expect(self._locator).to_be_hidden(timeout=timeout_ms or self.timeout_ms)

    def assert_text(self, expected_text: str, timeout_ms: int | None = None) -> None:
        expect(self._locator).to_have_text(
            expected_text,
            timeout=timeout_ms or self.timeout_ms,
        )

    def assert_contains_text(
        self,
        expected_text: str,
        timeout_ms: int | None = None,
    ) -> None:
        expect(self._locator).to_contain_text(
            expected_text,
            timeout=timeout_ms or self.timeout_ms,
        )

    def assert_enabled(self, timeout_ms: int | None = None) -> None:
        expect(self._locator).to_be_enabled(timeout=timeout_ms or self.timeout_ms)

    def assert_disabled(self, timeout_ms: int | None = None) -> None:
        expect(self._locator).to_be_disabled(timeout=timeout_ms or self.timeout_ms)

    def assert_count(self, expected_count: int, timeout_ms: int | None = None) -> None:
        expect(self._locator).to_have_count(
            expected_count,
            timeout=timeout_ms or self.timeout_ms,
        )
