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


def context_kwargs(*, locale: str = "es-CL",
                   timezone: str = "America/Santiago") -> dict:
    """Return kwargs for `browser.new_context()` with OS-consistent fingerprint."""
    p = host_profile()
    ua = (f"Mozilla/5.0 ({p['ua_os']}) AppleWebKit/537.36 "
          f"(KHTML, like Gecko) Chrome/{CHROME_FULL} Safari/537.36")
    is_mac = p["is_mac"]
    viewport = {"width": 1440, "height": 900} if is_mac \
        else {"width": 1536, "height": 864}
    return {
        "user_agent": ua,
        "locale": locale,
        "timezone_id": timezone,
        "viewport": viewport,
        "screen": viewport,
        "device_scale_factor": 2 if is_mac else 1,
        "is_mobile": False,
        "has_touch": False,
        "color_scheme": "light",
        "extra_http_headers": {
            "sec-ch-ua": (f'"Chromium";v="{CHROME_MAJOR}", '
                          f'"Google Chrome";v="{CHROME_MAJOR}", '
                          f'"Not_A Brand";v="24"'),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": p["ch_platform"],
            "sec-ch-ua-platform-version": p["ch_platform_version"],
            "sec-ch-ua-arch": p["arch"],
            "accept-language": "es-CL,es;q=0.9,en;q=0.8",
        },
    }


def init_script() -> str:
    """Return a JS string to inject via `page.add_init_script()` for stealth."""
    p = host_profile()
    is_mac = p["is_mac"]
    webgl_vendor = "Google Inc. (Apple)" if is_mac else "Google Inc. (Intel)"
    webgl_renderer = (
        "ANGLE (Apple, ANGLE Metal Renderer: Apple M1, Unspecified Version)"
        if is_mac
        else "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"
    )
    hw_concurrency = 8 if is_mac else 12
    return f"""
Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
Object.defineProperty(navigator, 'platform', {{ get: () => '{p["nav_platform"]}' }});
Object.defineProperty(navigator, 'languages', {{ get: () => ['es-CL', 'es', 'en'] }});
Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hw_concurrency} }});
Object.defineProperty(navigator, 'deviceMemory', {{ get: () => 8 }});
Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => 0 }});

if (typeof window.chrome === 'undefined' || !window.chrome.runtime) {{
    window.chrome = window.chrome || {{}};
    window.chrome.runtime = window.chrome.runtime || {{}};
    window.chrome.loadTimes = window.chrome.loadTimes || (() => ({{}}));
    window.chrome.csi = window.chrome.csi || (() => ({{}}));
}}

const _origGetParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(param) {{
    if (param === 37445) return '{webgl_vendor}';
    if (param === 37446) return '{webgl_renderer}';
    return _origGetParameter.call(this, param);
}};
if (typeof WebGL2RenderingContext !== 'undefined') {{
    WebGL2RenderingContext.prototype.getParameter = WebGLRenderingContext.prototype.getParameter;
}}

const _origQuery = navigator.permissions.query.bind(navigator.permissions);
navigator.permissions.query = (descriptor) => (
    descriptor && descriptor.name === 'notifications'
        ? Promise.resolve({{ state: Notification.permission }})
        : _origQuery(descriptor)
);

if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {{
    const _origHE = navigator.userAgentData.getHighEntropyValues.bind(navigator.userAgentData);
    navigator.userAgentData.getHighEntropyValues = (hints) => Promise.resolve({{
        platform: {p["ch_platform"]},
        platformVersion: {p["ch_platform_version"]},
        architecture: {p["arch"]},
        bitness: "64",
        model: "",
        mobile: false,
        uaFullVersion: "{CHROME_FULL}",
        brands: navigator.userAgentData.brands,
    }});
}}
""".strip()
