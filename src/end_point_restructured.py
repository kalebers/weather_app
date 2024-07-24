import requests
import yaml
import logging
import json
from typing import Optional, Dict, Any
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class WeatherEndPoint:
    """
    End point class to retrieve the weather data.
    """

    def __init__(self, config_path: str) -> None:
        self.config = self.load_config(config_path)
        self.api_key = self.config["api_key"]
        self.current_cast_url = self.config["current_cast_url"]
        self.forecast_url = self.config["forecast_url"]
        self.weather_maps_url = self.config["weather_maps_url"]
        self.air_pollution_url = self.config["air_pollution_url"]
        self.api_call_count = 0
        self.random_phrases()

    @staticmethod
    def load_config(config_path: str) -> Dict[str, str]:
        """
        Passes the string for the YAML configuration file that contains the API urls and
                the API key.

        :param config_path: string for the config file path.
        :type config_path: str
        :return: dict containing the strings for each param (KEY and URLs).
        :rtype: Dict[str, str]
        """
        with open(config_path, "r") as config_file:
            return yaml.safe_load(config_file)

    def increment_api_call_count(self) -> None:
        """
        Counter for how many times the API was requested.
        """
        self.api_call_count += 1

    def get_weather(self, city_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the current weather data for a specified city and include air pollution data.

        :param city_name: The name of the city to get the weather conditions.
        :type city_name: str
        :return: A dictionary containing the combined weather and air pollution data,
                        or None if an error occurred.
        :rtype: Optional[Dict[str, Any]]
        """
        self.increment_api_call_count()
        url = f"{self.current_cast_url}q={city_name}&appid={self.api_key}&units=metric"
        try:
            response = requests.get(url)
            logging.info(
                f"API Call {self.api_call_count}: Status Code {response.status_code}"
            )
            response.raise_for_status()
            weather_data = response.json()
            lat, lon = weather_data["coord"]["lat"], weather_data["coord"]["lon"]
            weather_data["air_pollution"] = self.get_air_pollution(lat, lon)
            return weather_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching weather data: {e}")
        return None

    def get_air_pollution(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get the air pollution data for a specified location.

        :param lat: The latitude of the location.
        :type lat: float
        :param lon: The longitude of the location.
        :type lon: float
        :return: The response object containing the air pollution data,
                                     or None if an error occurred.
        :rtype: Optional[Dict[str, Any]]
        """
        self.increment_api_call_count()
        url = f"{self.air_pollution_url}lat={lat}&lon={lon}&appid={self.api_key}"
        try:
            response = requests.get(url)
            logging.info(
                f"API Call {self.api_call_count}: Status Code {response.status_code}"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching air pollution data: {e}")
        return None

    def get_forecast(self, city_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the 5-day weather forecast for a specified city.

        :param city_name: The name of the city to get the weather conditions.
        :type city_name: str
        :return: The response object containing the forecast data,
                                     or None if an error occurred.
        :rtype: Optional[Dict[str, Any]]
        """
        self.increment_api_call_count()
        url = f"{self.forecast_url}q={city_name}&appid={self.api_key}&units=metric"
        try:
            response = requests.get(url)
            logging.info(
                f"API Call {self.api_call_count}: Status Code {response.status_code}"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching forecast data: {e}")
        return None

    @staticmethod
    def save_to_file(data: Dict[str, Any], filename: str) -> None:
        """
        Function that saves the data from the requests into the respective JSON files.

        :param data: Passes the dict containing the weather data to be saved.
        :type data: Dict[str, Any]
        :param filename: String of the file to get the data saved.
        :type filename: str
        """
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def random_phrases(self) -> None:
        """
        Initializes the lists of random phrases.
        """
        self.phrases_light_rain = [
            "Bring me an umbrella!",
            "Sing in the rain!",
            "How about a popcorn, some blankets and a good movie for a rainy day?",
            "Have good dreams while rains!",
        ]

        self.phrases_heavy_rain = ["Be careful, weather is getting tough!"]

        self.phrases_sunny = [
            "Today is a good day to run!",
            "Let's go to the beach!",
            "Some ICE ICE baby!",
        ]

    def display_weather(self, data: Optional[Dict[str, Any]]) -> None:
        """
        Display the current weather data and air pollution data from the response object.

        :param data: The dictionary containing the combined weather and air pollution data,
                               or None if an error occurred.
        :type data: Optional[Dict[str, Any]]
        """
        if data is None:
            logging.warning("No weather data available.")
            return

        self.save_to_file(data, "data_files/data_display_current_weather.json")

        if data.get("cod") == 200:
            main = data["main"]
            wind = data["wind"]
            weather = data["weather"][0]
            air_pollution = data.get("air_pollution", {}).get("list", [{}])[0]

            print(f"Temperature: {main['temp']}°C")
            print(f"Pressure: {main['pressure']} hPa")
            print(f"Humidity: {main['humidity']}%")
            print(f"Weather Description: {weather['description']}")
            print(f"Wind Speed: {wind['speed']} m/s")

            weather_description = weather["description"]
            if weather_description == "light rain":
                print(random.choice(self.phrases_light_rain))
            elif weather_description == "rain":
                print(random.choice(self.phrases_heavy_rain))
            elif weather_description == "clear sky":
                print(random.choice(self.phrases_sunny))

            if air_pollution:
                print(
                    f"Air Quality Index (AQI): {air_pollution.get('main', {}).get('aqi', 'N/A')}"
                )
                for component, value in air_pollution.get("components", {}).items():
                    print(f"  {component}: {value} µg/m³")
        else:
            logging.error(
                f"Error {data.get('cod')}: {data.get('message', 'An error occurred')}"
            )

    def display_forecast(self, data: Optional[Dict[str, Any]]) -> None:
        """
        Display the 5-day weather forecast data from the response object.

        :param data: The response object containing the forecast data,
                                                or None if an error occurred.
        :type data: Optional[Dict[str, Any]]
        """
        if data is None:
            logging.warning("No forecast data available.")
            return

        self.save_to_file(data, "data_files/data_display_forecast.json")

        if data.get("cod") == "200":
            print("5-Day Weather Forecast:")
            for forecast in data["list"]:
                dt_txt = forecast["dt_txt"]
                main = forecast["main"]
                weather = forecast["weather"][0]
                weather_description = weather["description"]

                if weather_description == "light rain":
                    print(random.choice(self.phrases_light_rain))
                elif weather_description == "rain":
                    print(random.choice(self.phrases_heavy_rain))
                elif weather_description == "clear sky":
                    print(random.choice(self.phrases_sunny))

                print(f"{dt_txt}: {main['temp']}°C, {weather['description']}")
        else:
            logging.error(
                f"Error {data.get('cod')}: {data.get('message', 'An error occurred')}"
            )


def main() -> None:
    """
    Main function to run the weather application.
    """
    end_point = WeatherEndPoint("src/config.yaml")
    while True:
        choice = input(
            "Enter 'current' for current weather, 'forecast' for 5-day forecast, 'exit' to quit: "
        ).lower()
        if choice == "exit":
            print(f"Total API calls made: {end_point.api_call_count}")
            break
        city_name = input("Enter city name: ")
        if choice == "current":
            data = end_point.get_weather(city_name)
            end_point.display_weather(data)
        elif choice == "forecast":
            data = end_point.get_forecast(city_name)
            end_point.display_forecast(data)
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
