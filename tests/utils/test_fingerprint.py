from unittest.mock import patch

from fintself.utils import fingerprint


def _with_platform(sysname: str, machine: str = "arm64", mac_ver: str = "15.0.0"):
    p1 = patch("fintself.utils.fingerprint.platform.system", return_value=sysname)
    p2 = patch("fintself.utils.fingerprint.platform.machine", return_value=machine)
    p3 = patch("fintself.utils.fingerprint.platform.mac_ver", return_value=(mac_ver, ("", "", ""), ""))
    return p1, p2, p3


class TestHostProfile:
    def test_darwin_returns_mac_fields(self):
        p1, p2, p3 = _with_platform("Darwin", machine="arm64", mac_ver="15.0.0")
        with p1, p2, p3:
            prof = fingerprint.host_profile()
        assert prof["sysname"] == "Darwin"
        assert "Macintosh" in prof["ua_os"]
        assert prof["ch_platform"] == '"macOS"'
        assert prof["ch_platform_version"] == '"15.0.0"'
        assert prof["nav_platform"] == "MacIntel"
        assert prof["arch"] == '"arm64"'
        assert prof["is_mac"] is True

    def test_windows_returns_win_fields(self):
        p1, p2, p3 = _with_platform("Windows", machine="AMD64")
        with p1, p2, p3:
            prof = fingerprint.host_profile()
        assert prof["sysname"] == "Windows"
        assert "Windows NT 10.0" in prof["ua_os"]
        assert prof["ch_platform"] == '"Windows"'
        assert prof["nav_platform"] == "Win32"
        assert prof["arch"] == '"x86"'
        assert prof["is_mac"] is False

    def test_linux_returns_linux_fields(self):
        p1, p2, p3 = _with_platform("Linux", machine="x86_64")
        with p1, p2, p3:
            prof = fingerprint.host_profile()
        assert prof["sysname"] == "Linux"
        assert "X11; Linux x86_64" in prof["ua_os"]
        assert prof["ch_platform"] == '"Linux"'
        assert prof["nav_platform"] == "Linux x86_64"
        assert prof["is_mac"] is False


class TestBrowserLaunchKwargs:
    def test_macos_default_uses_offscreen_window(self):
        p1, p2, p3 = _with_platform("Darwin")
        with p1, p2, p3:
            kw = fingerprint.browser_launch_kwargs()
        assert kw["channel"] == "chrome"
        assert kw["headless"] is False
        assert "--disable-blink-features=AutomationControlled" in kw["args"]
        assert "--window-position=-2400,-2400" in kw["args"]
        assert "--window-size=1440,900" in kw["args"]
        assert kw["ignore_default_args"] == ["--enable-automation"]
        assert "--headless=new" not in kw["args"]

    def test_linux_default_uses_new_headless(self):
        p1, p2, p3 = _with_platform("Linux", machine="x86_64")
        with p1, p2, p3:
            kw = fingerprint.browser_launch_kwargs()
        assert kw["channel"] == "chrome"
        assert kw["headless"] is True
        assert "--headless=new" in kw["args"]
        assert "--window-position=-2400,-2400" not in kw["args"]

    def test_explicit_headless_true_on_mac_respected(self):
        p1, p2, p3 = _with_platform("Darwin")
        with p1, p2, p3:
            kw = fingerprint.browser_launch_kwargs(headless=True)
        assert kw["headless"] is True
        assert "--window-position=-2400,-2400" not in kw["args"]

    def test_explicit_headless_false_on_linux_adds_offscreen_on_mac_only(self):
        p1, p2, p3 = _with_platform("Linux", machine="x86_64")
        with p1, p2, p3:
            kw = fingerprint.browser_launch_kwargs(headless=False)
        assert kw["headless"] is False
        assert "--window-position=-2400,-2400" not in kw["args"]


class TestContextKwargs:
    def test_mac_user_agent_contains_macintosh(self):
        p1, p2, p3 = _with_platform("Darwin")
        with p1, p2, p3:
            ck = fingerprint.context_kwargs()
        assert "Macintosh" in ck["user_agent"]
        assert "Chrome/131" in ck["user_agent"]

    def test_sec_ch_ua_platform_matches_ua(self):
        p1, p2, p3 = _with_platform("Darwin")
        with p1, p2, p3:
            ck = fingerprint.context_kwargs()
        assert ck["extra_http_headers"]["sec-ch-ua-platform"] == '"macOS"'
        assert ck["extra_http_headers"]["sec-ch-ua-mobile"] == "?0"

    def test_mac_uses_retina_scale_factor(self):
        p1, p2, p3 = _with_platform("Darwin")
        with p1, p2, p3:
            ck = fingerprint.context_kwargs()
        assert ck["device_scale_factor"] == 2

    def test_non_mac_uses_scale_factor_one(self):
        p1, p2, p3 = _with_platform("Windows")
        with p1, p2, p3:
            ck = fingerprint.context_kwargs()
        assert ck["device_scale_factor"] == 1
        assert "Windows NT 10.0" in ck["user_agent"]

    def test_passes_locale_and_timezone(self):
        p1, p2, p3 = _with_platform("Darwin")
        with p1, p2, p3:
            ck = fingerprint.context_kwargs(locale="es-CL", timezone="America/Santiago")
        assert ck["locale"] == "es-CL"
        assert ck["timezone_id"] == "America/Santiago"

    def test_viewport_and_screen_consistent(self):
        p1, p2, p3 = _with_platform("Darwin")
        with p1, p2, p3:
            ck = fingerprint.context_kwargs()
        assert ck["viewport"] == ck["screen"]
