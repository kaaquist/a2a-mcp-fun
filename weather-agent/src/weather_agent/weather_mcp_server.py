import httpx
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from langchain_core.tools import tool

logger = logging.getLogger(__name__)
geolocator = Nominatim(user_agent="city_weather_app")


def get_coordinates(city_name: str):
    """
    Convert a city name to latitude and longitude coordinates.

    Args:
        city_name (str): Name of the city (e.g., 'London, UK').

    Returns:
        tuple: (latitude, longitude) if successful, None otherwise.

    Raises:
        ValueError: If city_name is empty or invalid.
    """
    if not city_name or not isinstance(city_name, str):
        logger.error(
            "Please provide a city name and country. E.g. Copenhagen, DK or London, UK"
        )
        raise ValueError("City name must be a non-empty string")

    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        else:
            logger.warning(f"Could not find coordinates for city: {city_name}")
            return None
    except (GeocoderServiceError, GeocoderTimedOut) as e:
        logger.error(f"Geocoding error: {e}")
        return None


def get_weather_daily(city_name, daily_params=None, timezone="auto"):
    """
    Fetch weather data for a city using Open-Meteo API.

    Args:
        city_name (str): Name of the city (e.g., 'London, UK').
        daily_params (list): List of daily weather variables (e.g., ['temperature_2m_max', 'precipitation_sum']).
        timezone (str): Timezone for the forecast (default: 'auto').

    Returns:
        dict: Weather data from Open-Meteo API if successful, None otherwise.
    """
    # Default parameters if none provided
    daily_params = daily_params or ["temperature_2m_max", "precipitation_sum"]

    # Get coordinates
    coordinates = get_coordinates(city_name)
    if not coordinates:
        return None

    latitude, longitude = coordinates

    # Build API request parameters
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "daily": ",".join(daily_params),
    }

    try:
        with httpx.Client() as client:
            response = client.get(
                "https://api.open-meteo.com/v1/forecast", params=params, timeout=None
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error fetching weather data: {e}")
        return None


@tool()
def get_weather(city_name):
    """
    Fetch and display weather data for a city in a readable format.

    Args:
        city_name (str): Name of the city (e.g., 'London, UK').
    """
    weather_data = get_weather_daily(
        city_name, ["temperature_2m_max", "precipitation_sum"], "auto"
    )
    if not weather_data:
        logger.warning(f"No weather data available for {city_name}")
        return None

    logger.info(f"Weather data for {city_name}:")
    logger.info(f"Latitude: {weather_data.get('latitude')}")
    logger.info(f"Longitude: {weather_data.get('longitude')}")
    logger.info(f"Timezone: {weather_data.get('timezone')}")
    json_weather_data = {
        "city_name": city_name,
        "latitude": weather_data.get("latitude"),
        "longitude": weather_data.get("longitude"),
        "timezone": weather_data.get("timezone"),
    }

    # Display daily data if available
    daily_weather = []
    if "daily" in weather_data:
        json_daily_weather = {}
        logger.info("\nDaily Forecast:")
        for i, time in enumerate(weather_data["daily"]["time"]):
            json_daily_weather[time] = {}
            logger.info(f"Date: {time}")
            for param in weather_data["daily"]:
                if param != "time":
                    unit = weather_data.get("daily_units", {}).get(param, "")
                    logger.info(f"{param}: {weather_data['daily'][param][i]} {unit}")
                    json_daily_weather[time][
                        param
                    ] = f"{weather_data['daily'][param][i]} {unit}"
            logger.info(f"{'-' * 60}")
        daily_weather.append(json_daily_weather)
    json_weather_data["daily_forcast"] = daily_weather
    return json_weather_data


# Example usage
if __name__ == "__main__":
    get_weather("Copenhagen, DK")
