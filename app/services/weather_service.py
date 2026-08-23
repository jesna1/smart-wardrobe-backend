import httpx
from typing import Dict, Any, Optional
from app.core.config import settings


class WeatherService:
    def __init__(self):
        self.api_key = settings.WEATHER_API_KEY
        self.base_url = "http://api.weatherapi.com/v1/current.json"

    async def get_current_weather(
        self, lat: float, lon: float
    ) -> Dict[str, Any]:
        """
        Fetches current weather for given GPS coordinates.
        Returns parsed weather state or fallback defaults on failure/timeout.
        """
        if not self.api_key:
            return self._fallback_weather("API key missing")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "key": self.api_key,
                        "q": f"{lat},{lon}",
                        "aqi": "no",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    current = data.get("current", {})
                    condition = current.get("condition", {}).get("text", "Clear")
                    temp_c = current.get("temp_c", 25.0)

                    return {
                        "temperature_c": temp_c,
                        "temperature_f": current.get("temp_f", 77.0),
                        "condition": condition,
                        "humidity": current.get("humidity", 50),
                        "wind_kph": current.get("wind_kph", 10.0),
                        "season_category": self._map_temp_to_season(temp_c),
                        "location": data.get("location", {}).get("name", "Current Location"),
                        "is_fallback": False,
                    }
                else:
                    return self._fallback_weather(f"API Error: {response.status_code}")

        except (httpx.TimeoutException, httpx.RequestError) as e:
            print(f"[Weather API Warning] Request failed: {e}")
            return self._fallback_weather("Network or timeout error")

    def _map_temp_to_season(self, temp_c: float) -> str:
        if temp_c >= 28:
            return "Summer"
        elif temp_c <= 15:
            return "Winter"
        else:
            return "Spring/Autumn"

    def _fallback_weather(self, reason: str = "") -> Dict[str, Any]:
        return {
            "temperature_c": 25.0,
            "temperature_f": 77.0,
            "condition": "Partly cloudy",
            "humidity": 50,
            "wind_kph": 10.0,
            "season_category": "Spring/Autumn",
            "location": "Default Location",
            "is_fallback": True,
            "reason": reason,
        }


weather_service = WeatherService()