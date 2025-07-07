import os
import json
import requests
from typing import List, Dict
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# #############################################################################
# This is the new, standard way to create the app object for deployment
# #############################################################################
app = FastAPI()
# #############################################################################

WEATHER_DIR = "weather"

# Get port from environment variable (Render sets this, defaults to 8001 for local dev)
PORT = int(os.environ.get("PORT", 8001))

# Initialize FastMCP server
# We no longer pass host/port here as Uvicorn will handle it
mcp = FastMCP("weather")

# Mount the MCP server onto the main FastAPI app
# This makes it accessible to Uvicorn
app.mount("/", mcp)


@mcp.tool()
def get_current_weather(location: str) -> str:
    """
    Get current weather information for a specific location.

    Args:
        location: The city name or location to get weather for

    Returns:
        JSON string with current weather information
    """
    try:
        # Using wttr.in - a free weather API that requires no API key
        url = f"https://wttr.in/{location}?format=j1"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        weather_data = response.json()
        
        # Extract current conditions
        current = weather_data.get('current_condition', [{}])[0]
        
        weather_info = {
            'location': location,
            'temperature_c': current.get('temp_C', 'N/A'),
            'temperature_f': current.get('temp_F', 'N/A'),
            'condition': current.get('weatherDesc', [{}])[0].get('value', 'N/A'),
            'humidity': current.get('humidity', 'N/A'),
            'wind_speed_kmh': current.get('windspeedKmph', 'N/A'),
            'wind_direction': current.get('winddir16Point', 'N/A'),
            'feels_like_c': current.get('FeelsLikeC', 'N/A'),
            'feels_like_f': current.get('FeelsLikeF', 'N/A'),
            'visibility': current.get('visibility', 'N/A'),
            'pressure': current.get('pressure', 'N/A'),
            'uv_index': current.get('uvIndex', 'N/A')
        }
        
        # Save weather data
        save_weather_data(location, weather_info)
        
        return json.dumps(weather_info, indent=2)
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"
    except Exception as e:
        return f"Error processing weather data: {str(e)}"

@mcp.tool()
def get_weather_forecast(location: str, days: int = 3) -> str:
    """
    Get weather forecast for a specific location.

    Args:
        location: The city name or location to get forecast for
        days: Number of days to forecast (default: 3, max: 3)

    Returns:
        JSON string with weather forecast information
    """
    try:
        # Limit days to maximum of 3 for free API
        days = min(days, 3)
        
        url = f"https://wttr.in/{location}?format=j1"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        weather_data = response.json()
        
        # Extract forecast data
        forecast_days = weather_data.get('weather', [])[:days]
        
        forecast_info = {
            'location': location,
            'forecast_days': days,
            'forecast': []
        }
        
        for day_data in forecast_days:
            day_info = {
                'date': day_data.get('date', 'N/A'),
                'max_temp_c': day_data.get('maxtempC', 'N/A'),
                'max_temp_f': day_data.get('maxtempF', 'N/A'),
                'min_temp_c': day_data.get('mintempC', 'N/A'),
                'min_temp_f': day_data.get('mintempF', 'N/A'),
                'condition': day_data.get('hourly', [{}])[0].get('weatherDesc', [{}])[0].get('value', 'N/A'),
                'wind_speed_kmh': day_data.get('hourly', [{}])[0].get('windspeedKmph', 'N/A'),
                'humidity': day_data.get('hourly', [{}])[0].get('humidity', 'N/A'),
                'chance_of_rain': day_data.get('hourly', [{}])[0].get('chanceofrain', 'N/A')
            }
            forecast_info['forecast'].append(day_info)
        
        # Save forecast data
        save_weather_data(f"{location}_forecast", forecast_info)
        
        return json.dumps(forecast_info, indent=2)
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching forecast data: {str(e)}"
    except Exception as e:
        return f"Error processing forecast data: {str(e)}"

@mcp.tool()
def get_weather_history(location: str) -> List[str]:
    """
    Get previously saved weather data for a location.

    Args:
        location: The city name or location to get history for

    Returns:
        List of saved weather data filenames for the location
    """
    try:
        if not os.path.exists(WEATHER_DIR):
            return []
        
        history_files = []
        location_lower = location.lower().replace(" ", "_")
        
        for filename in os.listdir(WEATHER_DIR):
            if location_lower in filename.lower() and filename.endswith('.json'):
                history_files.append(filename)
        
        return history_files
        
    except Exception as e:
        return [f"Error reading weather history: {str(e)}"]

def save_weather_data(location: str, weather_info: Dict) -> None:
    """Save weather data to a file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(WEATHER_DIR, exist_ok=True)
        
        # Create filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        location_clean = location.lower().replace(" ", "_")
        filename = f"{location_clean}_{timestamp}.json"
        filepath = os.path.join(WEATHER_DIR, filename)
        
        # Add timestamp to weather info
        weather_info['saved_at'] = datetime.now().isoformat()
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(weather_info, f, indent=2)
            
        print(f"Weather data saved to: {filepath}")
        
    except Exception as e:
        print(f"Error saving weather data: {str(e)}")

# NOTE: We no longer need the if __name__ == "__main__" block
# Uvicorn will run the 'app' object directly
