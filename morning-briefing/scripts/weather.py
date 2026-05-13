#!/usr/bin/env python3
"""
weather.py - Daily DC weather brief.

Live data comes from api.weather.gov for Washington, DC. The job degrades to
explicit unavailable fields when the network or source is unavailable.

Dry-run: python morning-briefing/scripts/weather.py --dry-run
JSON:    python morning-briefing/scripts/weather.py --dry-run --json
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

DC_LAT = "38.9072"
DC_LON = "-77.0369"
POINTS_URL = f"https://api.weather.gov/points/{DC_LAT},{DC_LON}"
DEFAULT_TIMEOUT_SECONDS = 8
DEFAULT_USER_AGENT = "MT-Morning-Briefing/1.0 (weather.py; no contact configured)"
LOCAL_TZ = ZoneInfo("America/New_York")

SAMPLE_POINT = {
    "properties": {
        "forecast": "https://api.weather.gov/gridpoints/LWX/97,71/forecast",
        "forecastHourly": "https://api.weather.gov/gridpoints/LWX/97,71/forecast/hourly",
    }
}

SAMPLE_HOURLY = {
    "properties": {
        "periods": [
            {
                "name": "This Hour",
                "startTime": "2026-05-13T06:00:00-04:00",
                "temperature": 63,
                "temperatureUnit": "F",
                "shortForecast": "Partly Cloudy",
                "windSpeed": "5 mph",
                "windDirection": "NW",
                "probabilityOfPrecipitation": {"value": 20},
            },
            {
                "name": "7 AM",
                "startTime": "2026-05-13T07:00:00-04:00",
                "temperature": 65,
                "temperatureUnit": "F",
                "shortForecast": "Partly Cloudy",
                "windSpeed": "5 mph",
                "windDirection": "NW",
                "probabilityOfPrecipitation": {"value": 20},
            },
            {
                "name": "8 AM",
                "startTime": "2026-05-13T08:00:00-04:00",
                "temperature": 69,
                "temperatureUnit": "F",
                "shortForecast": "Mostly Sunny",
                "windSpeed": "6 mph",
                "windDirection": "NW",
                "probabilityOfPrecipitation": {"value": 10},
            },
        ]
    }
}

SAMPLE_DAILY = {
    "properties": {
        "periods": [
            {
                "name": "Today",
                "temperature": 78,
                "temperatureUnit": "F",
                "shortForecast": "Mostly Sunny",
                "isDaytime": True,
                "probabilityOfPrecipitation": {"value": 15},
            },
            {
                "name": "Tonight",
                "temperature": 61,
                "temperatureUnit": "F",
                "shortForecast": "Partly Cloudy",
                "isDaytime": False,
                "probabilityOfPrecipitation": {"value": 10},
            },
        ]
    }
}


class WeatherFetchError(Exception):
    """Raised when the weather source cannot provide usable live data."""


def fetch_json(url, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/geo+json, application/json",
            "User-Agent": os.environ.get("WEATHER_USER_AGENT", DEFAULT_USER_AGENT),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except (
        TimeoutError,
        urllib.error.URLError,
        urllib.error.HTTPError,
        json.JSONDecodeError,
    ) as exc:
        raise WeatherFetchError from exc


def live_payload(timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    point = fetch_json(POINTS_URL, timeout_seconds)
    properties = point.get("properties") or {}
    hourly_url = properties.get("forecastHourly")
    forecast_url = properties.get("forecast")
    if not hourly_url or not forecast_url:
        raise WeatherFetchError
    return point, fetch_json(hourly_url, timeout_seconds), fetch_json(forecast_url, timeout_seconds)


def sample_payload():
    return SAMPLE_POINT, SAMPLE_HOURLY, SAMPLE_DAILY


def percent_value(period):
    value = (period.get("probabilityOfPrecipitation") or {}).get("value")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def int_value(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def format_temp(value):
    return "unavailable" if value is None else f"{value}F"


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def max_wind_mph(periods):
    speeds = []
    for period in periods:
        speeds.extend(
            int(match.group(1))
            for match in re.finditer(r"\b(\d+)\s*mph\b", period.get("windSpeed", ""))
        )
    return max(speeds) if speeds else None


def has_wet_forecast(periods):
    wet_terms = (
        "rain",
        "showers",
        "thunderstorm",
        "drizzle",
        "snow",
        "sleet",
        "freezing rain",
    )
    text = " ".join(
        str(period.get("shortForecast") or "") + " " + str(period.get("detailedForecast") or "")
        for period in periods
    ).lower()
    return any(term in text for term in wet_terms)


def first_period(periods, daytime):
    for period in periods:
        if period.get("isDaytime") is daytime:
            return period
    return None


def high_low(hourly_periods, daily_periods):
    day_period = first_period(daily_periods, True)
    night_period = first_period(daily_periods, False)
    high = int_value(day_period.get("temperature")) if day_period else None
    low = int_value(night_period.get("temperature")) if night_period else None

    temps_24h = [int_value(period.get("temperature")) for period in hourly_periods[:24]]
    temps_24h = [temp for temp in temps_24h if temp is not None]
    if high is not None or low is not None:
        return (
            high if high is not None else max(temps_24h, default=None),
            low if low is not None else min(temps_24h, default=None),
        )

    if temps_24h:
        return max(temps_24h), min(temps_24h)
    return None, None


def umbrella_guidance(max_pop, wet_forecast):
    if max_pop is None:
        return "maybe" if wet_forecast else "check before leaving"
    if max_pop >= 50:
        return "yes"
    if max_pop >= 30 or wet_forecast:
        return "maybe"
    return "no"


def stroller_guidance(current_temp, max_pop, max_wind, conditions, wet_forecast):
    condition_text = (conditions or "").lower()
    if "thunder" in condition_text:
        return "indoor backup advised"
    if max_pop is not None and max_pop >= 60:
        return "rain cover and backup plan"
    if wet_forecast or (max_pop is not None and max_pop >= 30):
        return "pack rain cover"
    if current_temp is not None and current_temp <= 32:
        return "bundle layers; watch icy sidewalks"
    if current_temp is not None and current_temp < 45:
        return "bundle kid layers"
    if current_temp is not None and current_temp >= 90:
        return "early outing; heat breaks"
    if max_wind is not None and max_wind >= 20:
        return "secure stroller cover"
    return "good to go"


def build_brief(point, hourly, daily, status="ok"):
    hourly_periods = ((hourly.get("properties") or {}).get("periods") or [])
    daily_periods = ((daily.get("properties") or {}).get("periods") or [])
    current = hourly_periods[0] if hourly_periods else {}
    next_12h = hourly_periods[:12]

    current_temp = int_value(current.get("temperature"))
    current_conditions = current.get("shortForecast") or "unavailable"
    high, low = high_low(hourly_periods, daily_periods)

    pop_values = [percent_value(period) for period in next_12h]
    pop_values = [value for value in pop_values if value is not None]
    max_pop = max(pop_values) if pop_values else None
    wet_forecast = has_wet_forecast(next_12h or daily_periods[:2])
    max_wind = max_wind_mph(next_12h)
    current_time = parse_time(current.get("startTime"))
    if current_time:
        current_time = current_time.astimezone(LOCAL_TZ).isoformat(timespec="minutes")

    source_office = ((point.get("properties") or {}).get("gridId")) or "api.weather.gov"
    umbrella = umbrella_guidance(max_pop, wet_forecast)

    return {
        "location": "Washington, DC",
        "status": status,
        "source": source_office,
        "current_time": current_time,
        "current_temp_f": current_temp,
        "current_conditions": current_conditions,
        "high_f": high,
        "low_f": low,
        "precip_next_12h_pct": max_pop,
        "umbrella": umbrella,
        "stroller": stroller_guidance(
            current_temp, max_pop, max_wind, current_conditions, wet_forecast
        ),
        "aqi": "unavailable",
        "pollen": "unavailable",
        "material_alert": material_alert(current_conditions, max_pop, current_temp, max_wind),
    }


def material_alert(conditions, max_pop, current_temp, max_wind):
    condition_text = (conditions or "").lower()
    if "thunder" in condition_text:
        return "thunderstorms possible"
    if max_pop is not None and max_pop >= 70:
        return "high rain chance"
    if current_temp is not None and current_temp >= 95:
        return "heat caution"
    if current_temp is not None and current_temp <= 25:
        return "cold caution"
    if max_wind is not None and max_wind >= 25:
        return "wind caution"
    return "none"


def unavailable_brief():
    return {
        "location": "Washington, DC",
        "status": "degraded",
        "source": "api.weather.gov unavailable",
        "current_time": None,
        "current_temp_f": None,
        "current_conditions": "unavailable",
        "high_f": None,
        "low_f": None,
        "precip_next_12h_pct": None,
        "umbrella": "check before leaving",
        "stroller": "check live conditions before stroller plans",
        "aqi": "unavailable",
        "pollen": "unavailable",
        "material_alert": "weather source unavailable",
    }


def format_percent(value):
    return "unavailable" if value is None else f"{value}%"


def format_plain(brief, dry_run=False):
    prefix = "[DRY RUN] " if dry_run else ""
    lines = [
        f"{prefix}DC Weather - {brief['status']}",
        f"Now: {format_temp(brief['current_temp_f'])}, {brief['current_conditions']}",
        f"High {format_temp(brief['high_f'])} / Low {format_temp(brief['low_f'])}",
        (
            f"Precip next 12h: {format_percent(brief['precip_next_12h_pct'])}. "
            f"Umbrella: {brief['umbrella']}."
        ),
        f"Stroller: {brief['stroller']}.",
        f"AQI: {brief['aqi']} | Pollen: {brief['pollen']}",
        f"Alert: {brief['material_alert']} | Source: {brief['source']}",
    ]
    return "\n".join(lines)


def get_brief(dry_run=False, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    try:
        point, hourly, daily = sample_payload() if dry_run else live_payload(timeout_seconds)
        return build_brief(point, hourly, daily, status="sample" if dry_run else "ok")
    except WeatherFetchError:
        return unavailable_brief()


def main():
    parser = argparse.ArgumentParser(description="Daily Washington, DC weather brief")
    parser.add_argument("--dry-run", action="store_true", help="Use deterministic sample data")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Network timeout in seconds for live weather.gov calls",
    )
    args = parser.parse_args()

    if args.timeout <= 0:
        print("ERROR: --timeout must be positive.", file=sys.stderr)
        sys.exit(2)

    brief = get_brief(dry_run=args.dry_run, timeout_seconds=args.timeout)
    if args.json:
        print(json.dumps(brief, sort_keys=True))
    else:
        print(format_plain(brief, dry_run=args.dry_run))
    sys.exit(0)


if __name__ == "__main__":
    main()
