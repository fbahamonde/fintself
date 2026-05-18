"""Host OS detection + browser/context/init-script config for stealth scraping.

Pure module: no Playwright import. Returns dicts and strings only.
"""
from __future__ import annotations

import platform

CHROME_MAJOR = "131"
CHROME_FULL = "131.0.6778.86"


def host_profile() -> dict:
    """Detect host OS, return a dict with consistent fingerprint dimensions."""
    sysname = platform.system()
    if sysname == "Darwin":
        mac_v = platform.mac_ver()[0] or "15.0.0"
        machine = platform.machine() or "arm64"
        return {
            "sysname": "Darwin",
            "ua_os": "Macintosh; Intel Mac OS X 10_15_7",
            "ch_platform": '"macOS"',
            "ch_platform_version": f'"{mac_v}"',
            "nav_platform": "MacIntel",
            "arch": '"arm64"' if machine == "arm64" else '"x86"',
            "is_mac": True,
        }
    if sysname == "Windows":
        return {
            "sysname": "Windows",
            "ua_os": "Windows NT 10.0; Win64; x64",
            "ch_platform": '"Windows"',
            "ch_platform_version": '"15.0.0"',
            "nav_platform": "Win32",
            "arch": '"x86"',
            "is_mac": False,
        }
    return {
        "sysname": "Linux",
        "ua_os": "X11; Linux x86_64",
        "ch_platform": '"Linux"',
        "ch_platform_version": '""',
        "nav_platform": "Linux x86_64",
        "arch": '"x86"',
        "is_mac": False,
    }


def browser_launch_kwargs(*, headless: bool | None = None) -> dict:
    """Return kwargs for `chromium.launch()`.

    headless=None  -> auto: True on Linux, False on Darwin/Windows
    headless=True  -> use --headless=new on Linux; no offscreen on mac
    headless=False -> on mac, render offscreen via --window-position
    """
    sys = platform.system()
    if headless is None:
        headless = (sys == "Linux")

    args = ["--disable-blink-features=AutomationControlled"]
    if headless and sys == "Linux":
        args.append("--headless=new")
    elif not headless and sys == "Darwin":
        args += ["--window-position=-2400,-2400", "--window-size=1440,900"]

    return {
        "channel": "chrome",
        "headless": headless,
        "args": args,
        "ignore_default_args": ["--enable-automation"],
    }
