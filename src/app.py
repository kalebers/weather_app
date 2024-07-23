import requests
import yaml
import logging
from typing import Optional, Dict
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_config() -> Dict[str, str]:
    """
    Load the configuration from a YAML file.

    Returns:
        Dict[str, str]: A dictionary containing the API key and various base URLs from the configuration file.
    """
    with open("src/config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
    return {
        "api_key": config["api_key"],
        "current_cast_url": config["current_cast_url"],
        "forecast_url": config["forecast_url"],
        "weather_maps_url": config["weather_maps_url"],
        "air_polution_url": config["air_polution_url"],
    }


config = load_config()
API_KEY = config["api_key"]
CURRENT_CAST_URL = config["current_cast_url"]
FORECAST_URL = config["forecast_url"]
WEATHER_MAPS_URL = config["weather_maps_url"]
AIR_POLUTION_URL = config["air_polution_url"]
api_call_count = 0  # Initialize API call count


def get_weather(city_name: str) -> Optional[Dict]:
    """
    Get the current weather data for a specified city and include air pollution data.

    Args:
        city_name (str): The name of the city to get the weather for.

    Returns:
        Optional[Dict]: A dictionary containing the combined weather and air pollution data,
                        or None if an error occurred.
    """
    global api_call_count
    api_call_count += 1  # Increment API call count
    complete_url = f"{CURRENT_CAST_URL}q={city_name}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(complete_url)
        logging.info(f"API Call {api_call_count}: Status Code {response.status_code}")
        response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code

        weather_data = response.json()
        lat = weather_data["coord"]["lat"]
        lon = weather_data["coord"]["lon"]

        # Fetch air pollution data using the coordinates from the weather data
        air_pollution_response = get_air_pollution(lat, lon)
        if air_pollution_response:
            weather_data["air_pollution"] = air_pollution_response.json()

        return weather_data
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")
    return None


def get_air_pollution(lat: float, lon: float) -> Optional[requests.Response]:
    """
    Get the air pollution data for a specified location.

    Args:
        lat (float): The latitude of the location.
        lon (float): The longitude of the location.

    Returns:
        Optional[requests.Response]: The response object containing the air pollution data,
                                     or None if an error occurred.
    """
    global api_call_count
    api_call_count += 1  # Increment API call count
    complete_url = f"{AIR_POLUTION_URL}lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        response = requests.get(complete_url)
        logging.info(f"API Call {api_call_count}: Status Code {response.status_code}")
        response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
        return response
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")
    return None


def display_weather(data: Optional[Dict]) -> None:
    """
    Display the current weather data and air pollution data from the response object.

    Args:
        data (Optional[Dict]): The dictionary containing the combined weather and air pollution data,
                               or None if an error occurred.
    """
    if data is None:
        logging.warning("Response has no data!")
        return

    with open(
        "data_files/data_display_current_weather.json", "w", encoding="utf-8"
    ) as file:
        json.dump(data, file)

    match data.get("cod", 0):
        case 200:
            main = data["main"]
            wind = data["wind"]
            weather = data["weather"][0]
            air_pollution = data.get("air_pollution", {}).get("list", [{}])[0]

            temperature = main["temp"]
            pressure = main["pressure"]
            humidity = main["humidity"]
            weather_description = weather["description"]
            wind_speed = wind["speed"]

            print(f"Temperature: {temperature}°C")
            print(f"Pressure: {pressure} hPa")
            print(f"Humidity: {humidity}%")
            print(f"Weather Description: {weather_description}")
            print(f"Wind Speed: {wind_speed} m/s")

            if air_pollution:
                air_quality = air_pollution.get("main", {}).get("aqi", "N/A")
                components = air_pollution.get("components", {})

                print(f"Air Quality Index (AQI): {air_quality}")
                print("Components Air quality:")
                for component, value in components.items():
                    print(f"  {component}: {value} µg/m³ (micrograms/cubic meter air)")
        case 404:
            logging.error("City Not Found (Error 404)")
        case 401:
            logging.error("Invalid API key (Error 401)")
        case 500:
            logging.error("Internal Server Error (Error 500)")
        case _:
            logging.error(f"An error occurred (Error {data.get('cod')})")


def get_forecast(city_name: str) -> Optional[requests.Response]:
    """
    Get the 5-day weather forecast for a specified city.

    Args:
        city_name (str): The name of the city to get the forecast for.

    Returns:
        Optional[requests.Response]: The response object containing the forecast data,
                                     or None if an error occurred.
    """
    global api_call_count
    api_call_count += 1  # Increment API call count
    complete_url = f"{FORECAST_URL}q={city_name}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(complete_url)
        logging.info(f"API Call {api_call_count}: Status Code {response.status_code}")
        response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
        return response
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")
    return None


def display_forecast(response: Optional[requests.Response]) -> None:
    """
    Display the 5-day weather forecast data from the response object.

    Args:
        response (Optional[requests.Response]): The response object containing the forecast data,
                                                or None if an error occurred.
    """
    if response is None:
        logging.warning("Response has no data!")
        return

    data = response.json()
    with open("data_files/data_display_forecast.json", "w", encoding="utf-8") as file:
        json.dump(data, file)

    match response.status_code:
        case 200:
            print("5-Day Weather Forecast:")
            for forecast in data["list"]:
                dt_txt = forecast["dt_txt"]
                main = forecast["main"]
                weather = forecast["weather"][0]

                temperature = main["temp"]
                weather_description = weather["description"]

                print(f"{dt_txt}: {temperature}°C, {weather_description} \n")
        case 404:
            logging.error("City Not Found (Error 404)")
        case 401:
            logging.error("Invalid API key (Error 401)")
        case 500:
            logging.error("Internal Server Error (Error 500)")
        case _:
            logging.error(f"An error occurred (Error {response.status_code})")


def main() -> None:
    """
    Main function to run the weather application.
    """
    global api_call_count  # Ensure global variable is updated within the main function
    while True:
        choice = input(
            "Enter 'current' for current weather, 'forecast' for 5-day forecast, 'exit' to quit: "
        ).lower()
        if choice == "exit":
            print(f"Total API calls made: {api_call_count}")
            break
        city_name = input("Enter city name: ")
        if choice == "current":
            data = get_weather(city_name)
            display_weather(data)
        elif choice == "forecast":
            response = get_forecast(city_name)
            display_forecast(response)
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
