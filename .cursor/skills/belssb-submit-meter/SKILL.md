---
name: belssb-submit-meter
description: Submits electricity meter readings to BELSSB (Balašihinskaja Elektrosjet) via submit_readings.py. Use when the user wants to submit meter readings, send readings to belssb.ru, or submit показания to BELSSB.
---

# BELSSB Meter Readings Submission

## When to use

- User asks to submit meter readings, send readings to BELSSB, or submit показания.
- User provides or has configured account number and readings (day, and optionally night/peak by tariff).

## How to run

Execute the project script from the repository root:

```bash
python submit_readings.py [options]
```

**Do not invent account or reading values.** Use `config.yaml`, CLI args, or environment variables. If required values are missing, ask the user.

## Arguments by tariff

| Tariff     | Required args        | Optional |
|-----------|----------------------|----------|
| single    | `--day`              | —        |
| two-zone  | `--day`, `--night`   | —        |
| three-zone| `--day`, `--night`, `--peak` | —   |

- **Account**: `--account` / `-a` or `config.account` or `BELSSB_ACCOUNT`.
- **Tariff**: `--tariff` / `-t` with `single` | `two-zone` | `three-zone`. Default from config/env or `single`.
- **Contact** (optional): `--email` / `-e`, `--phone`; or config / `BELSSB_EMAIL`, `BELSSB_PHONE`.
- **Config file**: `--config` / `-c` (default `config.yaml`).

## Examples

**Single tariff (minimal):**
```bash
python submit_readings.py --account 12345678 --day 100.5 --tariff single
```

**Two-zone (with config for account/tariff):**
```bash
python submit_readings.py --day 200 --night 50
```

**Three-zone:**
```bash
python submit_readings.py --account 12345678 --day 150 --night 80 --peak 120 --tariff three-zone
```

**Headed mode** (visible browser; use if captcha appears):
```bash
python submit_readings.py --account 12345678 --day 100 --headed
```

**Suppress “after 25th” warning:**
```bash
python submit_readings.py --day 100 --no-warn-date
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | Success; form submitted, success message received. |
| 1    | Submission failed (timeout, success message not found). Suggest `--headed` or retry. |
| 2    | Invalid or missing input (e.g. no account, invalid/missing readings). |

## Important notes

- **Date rule**: Readings after the 25th of the month are not accepted for the current billing period (only the next). Script warns unless `--no-warn-date` is used.
- **Captcha**: If submission fails or captcha is likely, run again with `--headed`.
- **Debug**: Use `--debug` to print frame URLs and form-field discovery to stderr when diagnosing form issues.
- **Config**: Copy `config.example.yaml` to `config.yaml` and set `account`, `tariff`, and optionally contact. CLI and env override config.

## Prerequisites

- Dependencies installed: `pip install -r requirements.txt` and `playwright install chromium`.
- Script must be run from the project root (or ensure `config.yaml` path and imports resolve).
