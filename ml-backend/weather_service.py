"""
Tomorrow.io Weather Service for UV forecast integration.
Fetches hourly UV index predictions to proactively warn users.
"""

import os
import httpx
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

TOMORROW_IO_KEY = os.getenv("TOMORROW_IO_KEY")

# Tomorrow.io Realtime + Forecast API base
BASE_URL = "https://api.tomorrow.io/v4/weather/forecast"


async def get_uv_forecast(lat: float, lon: float, hours: int = 12) -> dict:
    """
    Fetch hourly UV index forecast from Tomorrow.io.
    Returns structured data with hourly UV values and a summary warning level.
    """
    if not TOMORROW_IO_KEY:
        return {
            "error": "TOMORROW_IO_KEY not configured",
            "hourly": [],
            "warning_level": "unknown"
        }

    params = {
        "location": f"{lat},{lon}",
        "apikey": TOMORROW_IO_KEY,
        "timesteps": "1h",
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        # Parse hourly UV values from the response
        hourly_forecasts = []
        timelines = data.get("timelines", {})
        hourly_data = timelines.get("hourly", [])

        for entry in hourly_data[:hours]:
            time_str = entry.get("time", "")
            values = entry.get("values", {})
            uv_index = values.get("uvIndex", 0)
            
            hourly_forecasts.append({
                "time": time_str,
                "uv_index": uv_index,
                "temperature": values.get("temperature"),
                "humidity": values.get("humidity"),
                "cloud_cover": values.get("cloudCover"),
            })

        # Determine warning level based on peak UV
        peak_uv = max((h["uv_index"] for h in hourly_forecasts), default=0)
        
        if peak_uv >= 8:
            warning_level = "extreme"
            warning_message = f"Extreme UV alert! Peak UV index of {peak_uv} expected. Avoid direct sunlight and apply SPF 50+."
        elif peak_uv >= 6:
            warning_level = "high"
            warning_message = f"High UV warning. Peak UV index of {peak_uv}. Sunscreen and protective clothing recommended."
        elif peak_uv >= 3:
            warning_level = "moderate"
            warning_message = f"Moderate UV levels expected (peak {peak_uv}). Consider sunscreen if outdoors."
        else:
            warning_level = "low"
            warning_message = f"Low UV conditions (peak {peak_uv}). Minimal protection needed."

        return {
            "location": {"lat": lat, "lon": lon},
            "peak_uv_index": peak_uv,
            "warning_level": warning_level,
            "warning_message": warning_message,
            "hourly": hourly_forecasts,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    except httpx.HTTPStatusError as e:
        return {
            "error": f"Tomorrow.io API error: {e.response.status_code}",
            "hourly": [],
            "warning_level": "unknown"
        }
    except httpx.RequestError as e:
        return {
            "error": f"Network error: {str(e)}",
            "hourly": [],
            "warning_level": "unknown"
        }
