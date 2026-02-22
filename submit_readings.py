#!/usr/bin/env python3
"""
Submit electricity meter readings to BELSSB (Balašihinskaja Elektrosjet) via the
official form at https://www.belssb.ru/individuals/pokaz/.

Uses Playwright to fill and submit the Formy-hosted form (shadow DOM or iframe).
Readings after the 25th of the month are not accepted for the current period.
"""

import argparse
import os
import re
import sys
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

URL = "https://www.belssb.ru/individuals/pokaz/"
SUCCESS_TEXT = "Сообщение успешно отправлено"
FORM_WAIT_TIMEOUT_MS = 20000
SUBMIT_WAIT_TIMEOUT_MS = 15000

TARIFF_SINGLE = "single"
TARIFF_TWO_ZONE = "two-zone"
TARIFF_THREE_ZONE = "three-zone"
TARIFFS = (TARIFF_SINGLE, TARIFF_TWO_ZONE, TARIFF_THREE_ZONE)


def load_config(config_path):
    """Load optional YAML config. Returns dict (possibly empty)."""
    path = Path(config_path)
    if not path.is_file():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Submit electricity meter readings to BELSSB (belssb.ru)."
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Path to YAML config file (default: config.yaml)",
    )
    parser.add_argument(
        "--account",
        "-a",
        help="Account / contract number (лицевой счёт). Overrides config.",
    )
    parser.add_argument(
        "--tariff",
        "-t",
        choices=TARIFFS,
        help="Tariff type: single, two-zone, three-zone. Overrides config.",
    )
    parser.add_argument(
        "--day",
        "-d",
        help="Показания общие (день) / day / semi-peak reading",
    )
    parser.add_argument(
        "--night",
        "-n",
        help="Показания ночь (night). Required for two-zone and three-zone.",
    )
    parser.add_argument(
        "--peak",
        "-p",
        help="Показания пик (peak). Required for three-zone only.",
    )
    parser.add_argument(
        "--email",
        "-e",
        help="Email for contact. Overrides config.",
    )
    parser.add_argument(
        "--phone",
        help="Phone number (e.g. 9123456789). Overrides config.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode (visible window). Use if captcha appears.",
    )
    parser.add_argument(
        "--no-warn-date",
        action="store_true",
        help="Do not warn when run after the 25th of the month.",
    )
    return parser.parse_args()


def validate_readings(tariff, day, night, peak):
    """Validate readings per tariff. Returns (True, None) or (False, error_msg)."""
    def numeric(s):
        if s is None:
            return False
        s = str(s).strip().replace(",", ".")
        return bool(s) and (s.isdigit() or (s.replace(".", "", 1).isdigit() and "." in s))

    if not day or not numeric(day):
        return False, "Missing or invalid --day (general/day/semi-peak reading)."
    if tariff in (TARIFF_TWO_ZONE, TARIFF_THREE_ZONE):
        if not night or not numeric(night):
            return False, "Missing or invalid --night for two-zone/three-zone tariff."
    if tariff == TARIFF_THREE_ZONE:
        if not peak or not numeric(peak):
            return False, "Missing or invalid --peak for three-zone tariff."
    return True, None


def warn_after_25th():
    """Warn if current date is after 25th."""
    from datetime import date
    today = date.today()
    if today.day > 25:
        print(
            "Warning: Readings submitted after the 25th are not accepted for the "
            "current billing period (only for the next).",
            file=sys.stderr,
        )


def _fill_form_via_js(eval_target, account, tariff, day, night, peak, email, phone):
    """Fill Formy form (shadow DOM or iframe) via JavaScript. eval_target is page or frame.
    Returns dict with filled count and submitClicked."""
    phone_digits = re.sub(r"\D", "", str(phone or ""))[-10:]
    args = {
        "input-account": str(account),
        "c_day": str(day),
        "c_night": str(night) if night else "",
        "c_peak": str(peak) if peak else "",
        "email": email or "",
        "phone": phone_digits,
        "phoneCountry": "7" if phone_digits else "",
    }
    script = """
    (args) => {
        function createEvent(type) {
            return new Event(type, { bubbles: true });
        }
        function findAndFill(root, depth) {
            if (!root || depth > 25) return { filled: 0, submit: null };
            const acc = root.querySelector('input[name="input-account"]') || root.getElementById('input-account');
            if (acc) {
                const container = acc.closest('form') || acc.closest('div') || root;
                let filled = 0;
                container.querySelectorAll('input[name], select[name]').forEach(el => {
                    const name = el.getAttribute('name');
                    const val = args[name] !== undefined ? String(args[name]) : null;
                    if (val !== null && val !== '') {
                        el.value = val;
                        el.dispatchEvent(createEvent('input'));
                        el.dispatchEvent(createEvent('change'));
                        filled++;
                    }
                });
                const submit = container.querySelector('button[type=submit]');
                return { filled, submit };
            }
            const list = root.querySelectorAll('*');
            for (let i = 0; i < list.length; i++) {
                const el = list[i];
                if (el.shadowRoot) {
                    const r = findAndFill(el.shadowRoot, depth + 1);
                    if (r.filled > 0) return r;
                }
            }
            return { filled: 0, submit: null };
        }
        const r = findAndFill(document, 0);
        if (r.submit) { r.submit.click(); return { filled: r.filled, submitClicked: true }; }
        return { filled: r.filled, submitClicked: false };
    }
    """
    return eval_target.evaluate(script, args)


def run_submit(account, tariff, day, night, peak, email, phone, headed):
    """Open page, fill form, submit, check success. Returns (success: bool, message: str)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        try:
            page = browser.new_page()
            page.goto(URL, wait_until="networkidle", timeout=FORM_WAIT_TIMEOUT_MS)
            # Formy widget can load in shadow DOM or in an iframe; give it time to appear
            page.wait_for_timeout(8000)
            result = _fill_form_via_js(
                page, account, tariff, day, night, peak, email, phone
            )
            fill_target = page
            if result.get("filled", 0) < 2:
                # Try inside Formy iframe (form may be embedded there)
                for frame in page.frames:
                    if frame != page.main_frame and "formy" in (frame.url or ""):
                        result = _fill_form_via_js(
                            frame, account, tariff, day, night, peak, email, phone
                        )
                        if result.get("filled", 0) >= 2:
                            fill_target = frame
                            break
            if result.get("filled", 0) < 2:
                return False, "Could not find form fields (form may have changed or not loaded)."
            if not result.get("submitClicked"):
                try:
                    if fill_target == page:
                        page.locator("button[type=submit]").nth(1).click(timeout=5000)
                    else:
                        fill_target.locator("button[type=submit]").first.click(timeout=5000)
                except Exception:
                    return False, "Could not find or click submit button."
            try:
                fill_target.wait_for_selector(
                    f"text={SUCCESS_TEXT}",
                    timeout=SUBMIT_WAIT_TIMEOUT_MS,
                )
                return True, SUCCESS_TEXT
            except PlaywrightTimeout:
                body = fill_target.locator("body").inner_text()
                if SUCCESS_TEXT in body:
                    return True, SUCCESS_TEXT
                snippet = body[:500] if body else "No content"
                return False, f"Success message not found. Page snippet: {snippet}"
        finally:
            browser.close()


def main():
    args = parse_args()
    config = load_config(args.config)

    account = args.account or config.get("account") or os.environ.get("BELSSB_ACCOUNT")
    tariff = args.tariff or config.get("tariff") or os.environ.get("BELSSB_TARIFF") or TARIFF_SINGLE
    day = args.day or config.get("day") or os.environ.get("BELSSB_DAY")
    night = args.night or config.get("night") or os.environ.get("BELSSB_NIGHT")
    peak = args.peak or config.get("peak") or os.environ.get("BELSSB_PEAK")
    email = args.email or config.get("email") or os.environ.get("BELSSB_EMAIL") or ""
    phone = args.phone or config.get("phone") or os.environ.get("BELSSB_PHONE") or ""

    if not account:
        print("Error: Account number is required (--account or config.account).", file=sys.stderr)
        return 2

    ok, err = validate_readings(tariff, day, night, peak)
    if not ok:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    if not args.no_warn_date:
        warn_after_25th()

    try:
        success, message = run_submit(
            account=account,
            tariff=tariff,
            day=day,
            night=night or "",
            peak=peak or "",
            email=email,
            phone=phone,
            headed=args.headed,
        )
    except PlaywrightTimeout as e:
        print(f"Error: Timeout while loading or submitting the form. Try --headed or run again. ({e})", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if success:
        print(message)
        return 0
    print(f"Error: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
