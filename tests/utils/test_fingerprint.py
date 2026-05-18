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
