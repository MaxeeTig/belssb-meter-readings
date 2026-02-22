# BELSSB meter readings submission

Submit electricity meter readings to **ЗАО «Балашихинская Электросеть»** (BELSSB) via the official form at [belssb.ru/individuals/pokaz/](https://www.belssb.ru/individuals/pokaz/).

The script uses browser automation (Playwright) to fill and submit the Formy-hosted form. Readings submitted **after the 25th** of the month are not accepted for the current billing period (only for the next).

**Repository:** [github.com/MaxeeTig/belssb-meter-readings](https://github.com/MaxeeTig/belssb-meter-readings)

```bash
git clone https://github.com/MaxeeTig/belssb-meter-readings.git
cd belssb-meter-readings
```

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. (Optional) Copy `config.example.yaml` to `config.yaml` and set your account number and default tariff. Or use CLI flags and environment variables.

## Usage

**Minimal (account and readings via CLI):**

```bash
python submit_readings.py --account 12345678 --day 100.5 --tariff single
```

**Two-zone tariff:**

```bash
python submit_readings.py --account 12345678 --day 200 --night 50 --tariff two-zone
```

**Three-zone tariff:**

```bash
python submit_readings.py --account 12345678 --day 150 --night 80 --peak 120 --tariff three-zone
```

**With config file:** put `account` and `tariff` in `config.yaml`, then pass only readings:

```bash
python submit_readings.py --day 100 --night 50
```

**Environment variables:** `BELSSB_ACCOUNT`, `BELSSB_TARIFF`, `BELSSB_DAY`, `BELSSB_NIGHT`, `BELSSB_PEAK`, `BELSSB_EMAIL`, `BELSSB_PHONE` override config when set.

**Headed mode (visible browser):** use if the form shows a captcha:

```bash
python submit_readings.py --account 12345678 --day 100 --headed
```

**Suppress “after 25th” warning:**

```bash
python submit_readings.py --account 12345678 --day 100 --no-warn-date
```

## Tariff types and fields

- **single** — only “Показания общие (день)” (`--day`).
- **two-zone** — day + night: `--day`, `--night`.
- **three-zone** — semi-peak + night + peak: `--day` (полупик), `--night`, `--peak`.

## Form structure

The form is hosted by Formy (ru.formy.app) and rendered inside shadow DOM. Field names and selectors are documented in [FORM_STRUCTURE.md](FORM_STRUCTURE.md). To re-discover the form (e.g. after a site change), run:

```bash
python discover_form.py
```

## Exit codes

- `0` — success.
- `1` — submission failed (e.g. success message not found, timeout).
- `2` — invalid arguments or missing required data.
