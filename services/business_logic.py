from datetime import datetime, timezone


def _add_months(dt: datetime, months: int) -> datetime:
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(
        dt.day,
        [
            31,
            29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31,
        ][month - 1],
    )
    return dt.replace(year=year, month=month, day=day)


def _month_labels(start: datetime, count: int) -> list[str]:
    return [_add_months(start, idx).strftime("%b %Y") for idx in range(count)]


def _simple_holt_winters_like(history: list[float], periods: int) -> list[float]:
    level = history[0]
    trend = history[1] - history[0] if len(history) > 1 else 0.0
    alpha = 0.45
    beta = 0.25

    for value in history[1:]:
        previous_level = level
        level = alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - previous_level) + (1 - beta) * trend

    return [round(level + trend * (idx + 1), 2) for idx in range(periods)]


def generate_forecast(profile: dict, current_premium: float):
    past_months = 24
    start_date = datetime.now(timezone.utc)
    age_factor = profile["age"] / 1000
    smoker_factor = 0.04 if profile["smoker_status"] else 0.0
    hospital_factor = profile["recent_hospitalizations"] * 0.01
    monthly_growth = 0.01 + age_factor + smoker_factor + hospital_factor

    base_past = current_premium * 0.82
    history = []
    for idx in range(past_months):
        smoothing = 1 + (((idx % 6) - 2) * 0.003)
        value = base_past + (current_premium - base_past) * (idx / max(past_months - 1, 1))
        history.append(round(value * smoothing, 2))

    forecast = _simple_holt_winters_like(history, 36)
    forecast = [round(value * (1 + monthly_growth), 2) for value in forecast]

    return {
        "historical_premiums": history,
        "forecast_premiums": forecast,
        "history_labels": _month_labels(_add_months(start_date, -past_months), past_months),
        "forecast_labels": _month_labels(start_date, 36),
        "trend_summary": (
            f"Projected premium change over 3 years is "
            f"${round(forecast[-1] - current_premium, 2)} based on current risk factors."
        ),
    }
