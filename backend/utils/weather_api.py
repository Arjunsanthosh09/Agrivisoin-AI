"""
Weather integration using Open-Meteo API (free, no API key).
Docs: https://open-meteo.com/en/docs
"""
import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes → condition + emoji + color
WEATHER_CODES = {
    0:  ("Clear sky", "☀️", "#FFC107"),
    1:  ("Mainly clear", "🌤️", "#FFC107"),
    2:  ("Partly cloudy", "⛅", "#90A4AE"),
    3:  ("Overcast", "☁️", "#607D8B"),
    45: ("Fog", "🌫️", "#90A4AE"),
    48: ("Depositing rime fog", "🌫️", "#90A4AE"),
    51: ("Light drizzle", "🌦️", "#42A5F5"),
    53: ("Moderate drizzle", "🌦️", "#42A5F5"),
    55: ("Dense drizzle", "🌧️", "#1E88E5"),
    61: ("Slight rain", "🌧️", "#1E88E5"),
    63: ("Moderate rain", "🌧️", "#1565C0"),
    65: ("Heavy rain", "🌧️", "#0D47A1"),
    71: ("Slight snow", "🌨️", "#B0BEC5"),
    73: ("Moderate snow", "🌨️", "#B0BEC5"),
    75: ("Heavy snow", "❄️", "#90A4AE"),
    80: ("Rain showers", "🌦️", "#1E88E5"),
    81: ("Moderate showers", "🌧️", "#1565C0"),
    82: ("Violent showers", "⛈️", "#0D47A1"),
    95: ("Thunderstorm", "⛈️", "#6A1B9A"),
    96: ("Thunderstorm + hail", "⛈️", "#4A148C"),
    99: ("Severe thunderstorm", "⛈️", "#4A148C"),
}


def describe_code(code):
    """Return (label, emoji, color) for a WMO weather code."""
    return WEATHER_CODES.get(code, ("Unknown", "🌡️", "#888"))


def geocode_location(name):
    """
    Convert a place name → {name, latitude, longitude, country, admin1}.
    Returns None if not found.
    """
    if not name or len(name.strip()) < 2:
        return None
    try:
        r = requests.get(
            GEOCODE_URL,
            params={"name": name.strip(), "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("results") or []
        if not results:
            return None
        top = results[0]
        return {
            "name": top.get("name"),
            "latitude": top.get("latitude"),
            "longitude": top.get("longitude"),
            "country": top.get("country"),
            "admin1": top.get("admin1"),   # state
            "admin2": top.get("admin2"),   # district
        }
    except Exception as e:
        print(f"⚠️ geocode error: {e}")
        return None


def fetch_weather(latitude, longitude, location_name=None):
    """
    Fetch current weather + 5-day forecast.
    Returns a dict, or None on failure.
    """
    try:
        r = requests.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,"
                           "wind_speed_10m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                         "relative_humidity_2m_mean,weather_code",
                "timezone": "Asia/Kolkata",
                "forecast_days": 5,
            },
            timeout=12,
        )
        if r.status_code != 200:
            print(f"⚠️ weather API status {r.status_code}: {r.text[:200]}")
            return None
        data = r.json()

        current = data.get("current", {})
        daily = data.get("daily", {})

        # Current weather
        code = current.get("weather_code", 0)
        label, emoji, color = describe_code(code)
        current_out = {
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": current.get("precipitation"),
            "wind_speed": current.get("wind_speed_10m"),
            "code": code,
            "label": label,
            "emoji": emoji,
            "color": color,
        }

        # Forecast
        forecast = []
        days = daily.get("time", [])
        for i in range(len(days)):
            d_code = (daily.get("weather_code") or [])[i] if i < len(daily.get("weather_code", [])) else 0
            d_label, d_emoji, d_color = describe_code(d_code)
            forecast.append({
                "date": days[i],
                "temp_max": (daily.get("temperature_2m_max") or [])[i],
                "temp_min": (daily.get("temperature_2m_min") or [])[i],
                "precipitation": (daily.get("precipitation_sum") or [])[i],
                "humidity": (daily.get("relative_humidity_2m_mean") or [])[i],
                "code": d_code,
                "label": d_label,
                "emoji": d_emoji,
                "color": d_color,
            })

        return {
            "location_name": location_name or "Current location",
            "latitude": latitude,
            "longitude": longitude,
            "current": current_out,
            "forecast": forecast,
        }
    except Exception as e:
        print(f"⚠️ fetch_weather error: {e}")
        return None