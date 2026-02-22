"""
One-time form discovery: open BELSSB meter readings page and print form structure
(including shadow DOM) to document field names and selectors for submit_readings.py.
Run: python discover_form.py
"""
import json
import sys
from playwright.sync_api import sync_playwright

URL = "https://www.belssb.ru/individuals/pokaz/"

JS_COLLECT_FORM = """
() => {
  const result = { inputs: [], buttons: [], iframes: [], shadowHosts: [] };
  function walk(root, depth) {
    if (!root || depth > 20) return;
    try {
      const inputs = root.querySelectorAll('input:not([type=hidden]), select, textarea');
      inputs.forEach(el => {
        const label = el.labels && el.labels[0] ? el.labels[0].textContent.trim() : '';
        const placeholder = el.placeholder || '';
        const name = el.name || el.id || '';
        result.inputs.push({
          tag: el.tagName,
          type: el.type || '',
          name,
          id: el.id || '',
          placeholder: placeholder.slice(0, 80),
          label: label.slice(0, 120),
          required: el.required
        });
      });
      root.querySelectorAll('button, [type=submit], input[type=submit]').forEach(el => {
        result.buttons.push({
          tag: el.tagName,
          type: el.type || '',
          text: (el.textContent || el.value || '').trim().slice(0, 80)
        });
      });
      root.querySelectorAll('iframe').forEach(iframe => {
        result.iframes.push({ src: iframe.src || '', id: iframe.id || '' });
      });
      root.querySelectorAll('*').forEach(el => {
        if (el.shadowRoot) {
          result.shadowHosts.push(el.tagName + (el.id ? '#' + el.id : ''));
          walk(el.shadowRoot, depth + 1);
        }
      });
    } catch (e) {}
  }
  walk(document, 0);
  return result;
}
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(URL, wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(5000)  # allow Formy widget to load
            data = page.evaluate(JS_COLLECT_FORM)
            print(json.dumps(data, ensure_ascii=False, indent=2))
            # Also try within any iframe
            for frame in page.frames:
                if frame != page.main_frame and "formy" in (frame.url or ""):
                    try:
                        iframe_data = frame.evaluate(JS_COLLECT_FORM)
                        print("\n--- Inside iframe ---\n", json.dumps(iframe_data, ensure_ascii=False, indent=2))
                    except Exception as e:
                        print("Frame eval error:", e)
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
