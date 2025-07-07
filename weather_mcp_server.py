import requests
import json
import os
from typing import List, Dict
from mcp.server.fastmcp import FastMCP

WEATHER_DIR = "weather"

# Get port from environment variable (Render sets this, defaults to 8001 for local dev)
PORT = int(os.environ.get("PORT", 8001))

# Initialize FastMCP server with host and port in constructor
mcp = FastMCP("weather", host="0.0.0.0", port=PORT)

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

@mcp.resource("weather://locations")
def get_saved_locations() -> str:
    """
    List all locations with saved weather data.

    This resource provides a simple list of all locations with weather history.
    """
    try:
        if not os.path.exists(WEATHER_DIR):
            return "# No Weather Data\n\nNo weather data has been saved yet."
        
        locations = set()
        
        for filename in os.listdir(WEATHER_DIR):
            if filename.endswith('.json'):
                # Extract location from filename
                location_part = filename.split('_')[0]
                locations.add(location_part.replace("_", " ").title())
        
        content = "# Saved Weather Locations\n\n"
        if locations:
            for location in sorted(locations):
                content += f"- {location}\n"
            content += f"\nTotal locations: {len(locations)}\n"
        else:
            content += "No locations found.\n"
        
        return content
        
    except Exception as e:
        return f"# Error\n\nError reading weather locations: {str(e)}"

@mcp.resource("weather://{location}")
def get_location_weather_history(location: str) -> str:
    """
    Get detailed weather history for a specific location.

    Args:
        location: The location to retrieve weather history for
    """
    try:
        if not os.path.exists(WEATHER_DIR):
            return f"# No Weather Data for {location.title()}\n\nNo weather data found."
        
        location_clean = location.lower().replace(" ", "_")
        weather_files = []
        
        for filename in os.listdir(WEATHER_DIR):
            if filename.startswith(location_clean) and filename.endswith('.json'):
                filepath = os.path.join(WEATHER_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    weather_files.append((filename, data))
                except:
                    continue
        
        if not weather_files:
            return f"# No Weather Data for {location.title()}\n\nNo weather history found for this location."
        
        # Sort by filename (which includes timestamp)
        weather_files.sort(key=lambda x: x[0], reverse=True)
        
        content = f"# Weather History for {location.title()}\n\n"
        content += f"Total records: {len(weather_files)}\n\n"
        
        for filename, data in weather_files[:5]:  # Show last 5 records
            content += f"## {data.get('saved_at', 'Unknown time')}\n"
            
            if 'forecast' in data:
                content += f"**Forecast Data**\n"
                content += f"- Days: {data.get('forecast_days', 'N/A')}\n"
                for forecast in data.get('forecast', [])[:2]:  # Show first 2 days
                    content += f"- {forecast.get('date', 'N/A')}: {forecast.get('max_temp_c', 'N/A')}°C / {forecast.get('condition', 'N/A')}\n"
            else:
                content += f"**Current Weather**\n"
                content += f"- Temperature: {data.get('temperature_c', 'N/A')}°C / {data.get('temperature_f', 'N/A')}°F\n"
                content += f"- Condition: {data.get('condition', 'N/A')}\n"
                content += f"- Humidity: {data.get('humidity', 'N/A')}%\n"
                content += f"- Wind: {data.get('wind_speed_kmh', 'N/A')} km/h {data.get('wind_direction', 'N/A')}\n"
            
            content += "\n---\n\n"
        
        return content
        
    except Exception as e:
        return f"# Error\n\nError reading weather history for {location}: {str(e)}"

@mcp.prompt()
def generate_weather_prompt(location: str, forecast_days: int = 3) -> str:
    """Generate a prompt for getting comprehensive weather information for a location."""
    return f"""Get comprehensive weather information for '{location}' using the weather tools.

    Follow these instructions:
    1. First, get current weather using get_current_weather(location='{location}')
    2. Then, get the forecast using get_weather_forecast(location='{location}', days={forecast_days})
    3. Check if there's any weather history using get_weather_history(location='{location}')

    4. Provide a comprehensive weather report that includes:
       - Current weather conditions with temperature, humidity, wind
       - Weather forecast for the next {forecast_days} days
       - Any notable weather patterns or recommendations
       - Comparison with recent historical data if available

    5. Format your response in a clear, readable format with sections for:
       - Current Conditions
       - {forecast_days}-Day Forecast
       - Weather Summary & Recommendations

    Present the information in a way that's useful for planning activities or travel."""

if __name__ == "__main__":
    # This block runs when you execute `python weather_mcp_server.py`
    print(f"Starting Weather MCP server on 0.0.0.0:{PORT}")

    # Explicitly tell .run() which host and port to use, which fixes the Render port detection issue
    mcp.run(host="0.0.0.0", port=PORT)
