# BELSSB meter readings form structure (discovered)

Page: https://www.belssb.ru/individuals/pokaz/

Form is rendered inside **shadow DOM** (Formy widget). Playwright pierces shadow by default.

## Field names (from discover_form.py)

| Purpose | Selector / name | Notes |
|--------|-----------------|--------|
| Account number (лицевой счёт) | `input#input-account` or `input[name="input-account"]` | Required |
| Показания общие (день) | `input[name="c_day"]` | Day / general / semi-peak depending on tariff |
| Показания ночь | `input[name="c_night"]` | For 2-zone and 3-zone |
| Показания пик | `input[name="c_peak"]` | For 3-zone only |
| Email | `input[name="email"]` | Contact, may be required |
| Phone country | `select[name="phoneCountry"]` | |
| Phone | `input[name="phone"]` (type=tel) | Contact |

## Submit

- `button[type=submit]` — there are two (site search + form). The form submit button is inside the Formy widget; use the one that is a descendant of the form container or the one with visible text like "Отправить показания".

## Success

- Text on page after success: **«Сообщение успешно отправлено»**

## Captcha

- Not observed in discovery; if present, run in headed mode for manual solve.
