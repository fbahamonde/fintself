"""Manual verifier: launch a stealth browser, hit sannysoft + creepjs,
save screenshots, print URLs. Run via:

    uv run python scripts/verify_fingerprint.py

Then open /tmp/sannysoft.png and /tmp/creepjs.png to inspect.
"""
from patchright.sync_api import sync_playwright

from fintself.utils import fingerprint


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(**fingerprint.browser_launch_kwargs())
        ctx = browser.new_context(**fingerprint.context_kwargs())
        ctx.add_init_script(fingerprint.init_script())
        page = ctx.new_page()
        page.set_default_timeout(30000)

        print("Loading bot.sannysoft.com ...")
        page.goto("https://bot.sannysoft.com/")
        page.wait_for_timeout(2000)
        page.screenshot(path="/tmp/sannysoft.png", full_page=True)

        print("Loading creepjs ...")
        page.goto("https://abrahamjuliot.github.io/creepjs/")
        page.wait_for_timeout(10000)
        page.screenshot(path="/tmp/creepjs.png", full_page=True)

        browser.close()
    print("Screenshots saved: /tmp/sannysoft.png, /tmp/creepjs.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
