"""Tests for the 4 opt-in hooks on BaseScraper.

Default behavior must preserve legacy: same kwargs to launch/new_context
and the same single-line navigator.webdriver init script.
"""
from unittest.mock import MagicMock

import pytest

from fintself.scrapers.base import BaseScraper


class _DummyScraper(BaseScraper):
    """Minimal concrete subclass to instantiate BaseScraper for tests."""

    def _get_bank_id(self) -> str:
        return "test_dummy"

    def _login(self) -> None:
        pass

    def _scrape_movements(self):
        return []


@pytest.fixture
def scraper():
    return _DummyScraper(headless=True, debug_mode=False)


class TestDefaultHooks:
    def test_default_browser_launch_kwargs_preserves_legacy(self, scraper):
        kw = scraper._browser_launch_kwargs()
        assert "headless" in kw
        assert "slow_mo" in kw
        assert "channel" not in kw
        assert "ignore_default_args" not in kw

    def test_default_browser_context_kwargs_preserves_legacy(self, scraper):
        kw = scraper._browser_context_kwargs()
        assert "user_agent" in kw
        assert "viewport" in kw
        assert "locale" in kw
        assert "timezone_id" in kw
        assert "extra_http_headers" not in kw
        assert "device_scale_factor" not in kw

    def test_default_browser_init_script_is_legacy_one_liner(self, scraper):
        s = scraper._browser_init_script()
        assert s is not None
        assert "webdriver" in s
        assert "\n" not in s.strip()

    def test_default_playwright_factory_returns_playwright_sync(self, scraper):
        factory = scraper._playwright_factory()
        cm = factory()
        assert "playwright" in type(cm).__module__
        assert "patchright" not in type(cm).__module__


class TestSubclassOverrides:
    def test_subclass_can_override_launch_kwargs(self):
        class Custom(_DummyScraper):
            def _browser_launch_kwargs(self):
                return {"channel": "chrome", "headless": False, "args": ["--x"]}

        s = Custom()
        assert s._browser_launch_kwargs() == {"channel": "chrome", "headless": False, "args": ["--x"]}

    def test_subclass_can_override_init_script(self):
        class Custom(_DummyScraper):
            def _browser_init_script(self):
                return "console.log('custom');"

        s = Custom()
        assert s._browser_init_script() == "console.log('custom');"

    def test_subclass_can_override_playwright_factory(self):
        sentinel = MagicMock()

        class Custom(_DummyScraper):
            def _playwright_factory(self):
                return sentinel

        s = Custom()
        assert s._playwright_factory() is sentinel
