from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import uvicorn

from weather_service import get_coordinates, get_weather, interpret_weather_code
from weather_schemas import (
    WeatherDashboard, 
    LocationInfo, 
    CurrentWeather,
    DailyForecast,
    HourlyForecast,
    CityWeatherRequest
)

# Database setup
DATABASE_URL = "sqlite:///./weather_app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Weather search history model
class WeatherSearch(Base):
    __tablename__ = "weather_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    temperature = Column(Float)
    weather_description = Column(String)
    searched_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Weather Dashboard API",
    description="A weather dashboard that fetches data from Open-Meteo API",
    version="1.0.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {
        "message": "Welcome to Weather Dashboard API",
        "endpoints": {
            "current_weather": "/weather/{city}",
            "search_history": "/history",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/weather", response_model=WeatherDashboard)
async def get_weather_dashboard(request: CityWeatherRequest, db: Session = Depends(get_db)):
    """
    Fetch complete weather dashboard for a city
    """
    city = request.city.strip()
    
    if not city:
        raise HTTPException(status_code=400, detail="City name cannot be empty")
    
    # Get coordinates for the city
    location_data = await get_coordinates(city)
    if not location_data:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    
    # Get weather data
    weather_data = await get_weather(location_data["latitude"], location_data["longitude"])
    if not weather_data:
        raise HTTPException(status_code=500, detail="Failed to fetch weather data")
    
    # Parse current weather
    current = weather_data["current"]
    current_weather = CurrentWeather(
        temperature=current["temperature_2m"],
        humidity=current["relative_humidity_2m"],
        weather_description=interpret_weather_code(current["weather_code"]),
        wind_speed=current["wind_speed_10m"],
        wind_direction=current["wind_direction_10m"],
        timestamp=datetime.fromisoformat(current["time"].replace("Z", "+00:00"))
    )
    
    # Parse hourly forecast (next 24 hours)
    hourly = weather_data["hourly"]
    hourly_forecast = []
    for i in range(min(24, len(hourly["time"]))):
        hourly_forecast.append(
            HourlyForecast(
                time=hourly["time"][i],
                temperature=hourly["temperature_2m"][i],
                weather_description=interpret_weather_code(hourly["weather_code"][i])
            )
        )
    
    # Parse daily forecast (next 7 days)
    daily = weather_data["daily"]
    daily_forecast = []
    for i in range(len(daily["time"])):
        daily_forecast.append(
            DailyForecast(
                date=daily["time"][i],
                max_temp=daily["temperature_2m_max"][i],
                min_temp=daily["temperature_2m_min"][i],
                weather_description=interpret_weather_code(daily["weather_code"][i]),
                precipitation=daily["precipitation_sum"][i]
            )
        )
    
    # Save search to database
    search_record = WeatherSearch(
        city=city,
        latitude=location_data["latitude"],
        longitude=location_data["longitude"],
        temperature=current_weather.temperature,
        weather_description=current_weather.weather_description
    )
    db.add(search_record)
    db.commit()
    
    # Build response
    return WeatherDashboard(
        location=LocationInfo(**location_data),
        current_weather=current_weather,
        hourly_forecast=hourly_forecast,
        daily_forecast=daily_forecast
    )

@app.get("/weather/{city}", response_model=WeatherDashboard)
async def get_weather_by_city(city: str, db: Session = Depends(get_db)):
    """
    Fetch weather dashboard for a city (GET endpoint)
    """
    request = CityWeatherRequest(city=city)
    return await get_weather_dashboard(request, db)

@app.get("/history")
async def get_search_history(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get recent weather searches
    """
    searches = db.query(WeatherSearch).order_by(WeatherSearch.searched_at.desc()).limit(limit).all()
    return [
        {
            "city": s.city,
            "temperature": s.temperature,
            "weather": s.weather_description,
            "location": {"latitude": s.latitude, "longitude": s.longitude},
            "searched_at": s.searched_at
        }
        for s in searches
    ]

@app.delete("/history")
async def clear_search_history(db: Session = Depends(get_db)):
    """
    Clear all search history
    """
    db.query(WeatherSearch).delete()
    db.commit()
    return {"message": "Search history cleared"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
