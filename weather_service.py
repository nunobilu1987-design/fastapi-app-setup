import httpx
from datetime import datetime
from typing import Optional

# Using Open-Meteo API (free, no API key required)
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"

async def get_coordinates(city: str) -> Optional[dict]:
    """Fetch coordinates for a city using Open-Meteo Geocoding API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                GEOCODING_API_URL,
                params={"name": city, "count": 1, "language": "en", "format": "json"}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                return {
                    "latitude": result["latitude"],
                    "longitude": result["longitude"],
                    "name": result["name"],
                    "country": result.get("country", ""),
                    "admin1": result.get("admin1", "")
                }
            return None
        except Exception as e:
            print(f"Error fetching coordinates: {e}")
            return None

async def get_weather(latitude: float, longitude: float) -> Optional[dict]:
    """Fetch weather data from Open-Meteo API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                WEATHER_API_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m",
                    "hourly": "temperature_2m,weather_code",
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
                    "timezone": "auto"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return None

def interpret_weather_code(code: int) -> str:
    """Convert WMO weather code to human-readable description"""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Foggy",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(code, "Unknown")
