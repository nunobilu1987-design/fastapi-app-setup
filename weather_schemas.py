from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LocationInfo(BaseModel):
    name: str
    country: str
    admin1: Optional[str] = None
    latitude: float
    longitude: float

class CurrentWeather(BaseModel):
    temperature: float
    humidity: int
    weather_description: str
    wind_speed: float
    wind_direction: int
    timestamp: datetime

class DailyForecast(BaseModel):
    date: str
    max_temp: float
    min_temp: float
    weather_description: str
    precipitation: float

class HourlyForecast(BaseModel):
    time: str
    temperature: float
    weather_description: str

class WeatherDashboard(BaseModel):
    location: LocationInfo
    current_weather: CurrentWeather
    hourly_forecast: List[HourlyForecast]
    daily_forecast: List[DailyForecast]

class CityWeatherRequest(BaseModel):
    city: str
