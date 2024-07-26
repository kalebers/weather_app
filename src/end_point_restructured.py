import requests
import yaml
import logging
import json
from typing import Optional, Dict, Any
import random
import io
import pathlib

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

    def get_forecast(self, city_name: str, days: int) -> Optional[Dict[str, Any]]:
        """
        Get the weather forecast for a specified city and number of days.

        :param city_name: The name of the city to get the weather conditions.
        :type city_name: str
        :param days: The number of days for the forecast (maximum 5).
        :type days: int
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
            forecast_data = response.json()
            if forecast_data.get("cod") == "200":
                # Filter the forecast to include only the specified number of days
                filtered_forecast = {
                    "cod": forecast_data["cod"],
                    "message": forecast_data["message"],
                    "cnt": min(days * 8, len(forecast_data["list"])),
                    "list": forecast_data["list"][: days * 8],
                    "city": forecast_data["city"],
                }
                return filtered_forecast
            return forecast_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching forecast data: {e}")
        return None

    @staticmethod
    def write(data: Dict[str, Any], file: io.TextIOWrapper) -> None:
        """
        Function that write the data from the requests into the respective JSON files.

        :param data: Passes the dict containing the weather data to be saved.
        :type data: Dict[str, Any]
        :param fie: String of the file to get the data saved.
        :type file: io.TextIOWrapper
        """
        json.dump(data, file, indent=4)

    @classmethod
    def save_to_file(cls, data: Dict[str, Any], path: pathlib.Path) -> None:
        """
        Function that write and saves the data into the json file.

        :param data:  Passes the dict containing the weather data to be saved.
        :type data: Dict[str, Any]
        :param path: Passes the path for the saved file.
        :type path: pathlib.Path
        """
        with open(path, "w", encoding="utf-8") as file:
            cls.write(data, file)

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

        self.phrases_few_clouds = [
            "Good weather for a nice walk!",
        ]

        self.scattered_cloud = [
            "Let's guess what image the clouds make?!",
            "Look! The sky seems like a cottom candy!",
        ]

        self.phrases_broken_clouds = [
            "Nice sky for a few photos!",
            "Let's exercise outside?",
        ]

        self.phrases_overcast_clouds = [
            "Grey days can be fun!",
            "Chill day for you today!",
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

        self.save_to_file(
            data, pathlib.Path("data_files") / "data_display_current_weather.json"
        )

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
            elif weather_description == "moderate rain":
                print(random.choice(self.phrases_light_rain))
            elif weather_description == "rain":
                print(random.choice(self.phrases_heavy_rain))
            elif weather_description == "clear sky":
                print(random.choice(self.phrases_sunny))
            elif weather_description == "few clouds":
                print(random.choice(self.phrases_few_clouds))
            elif weather_description == "scattered clouds":
                print(random.choice(self.scattered_cloud))
            elif weather_description == "broken clouds":
                print(random.choice(self.phrases_broken_clouds))
            elif weather_description == "overcast clouds":
                print(random.choice(self.phrases_overcast_clouds))

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

        self.save_to_file(
            data, pathlib.Path("data_files") / "data_display_forecast.json"
        )

        if data.get("cod") == "200":
            print("5-Day Weather Forecast:")
            for forecast in data["list"]:
                dt_txt = forecast["dt_txt"]
                main = forecast["main"]
                weather = forecast["weather"][0]
                weather_description = weather["description"]

                if weather_description == "light rain":
                    print(random.choice(self.phrases_light_rain))
                elif weather_description == "moderate rain":
                    print(random.choice(self.phrases_light_rain))
                elif weather_description == "rain":
                    print(random.choice(self.phrases_heavy_rain))
                elif weather_description == "clear sky":
                    print(random.choice(self.phrases_sunny))
                elif weather_description == "few clouds":
                    print(random.choice(self.phrases_few_clouds))
                elif weather_description == "scattered clouds":
                    print(random.choice(self.scattered_cloud))
                elif weather_description == "broken clouds":
                    print(random.choice(self.phrases_broken_clouds))
                elif weather_description == "overcast clouds":
                    print(random.choice(self.phrases_overcast_clouds))

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
            "Enter 'current' for current weather, 'forecast' for weather forecast, 'exit' to quit: "
        ).lower()
        if choice == "exit":
            print(f"Total API calls made: {end_point.api_call_count}")
            break
        city_name = input("Enter city name: ")
        if choice == "current":
            data = end_point.get_weather(city_name)
            end_point.display_weather(data)
        elif choice == "forecast":
            days = int(input("Enter the number of days for the forecast (1-5): "))
            if 1 <= days <= 5:
                data = end_point.get_forecast(city_name, days)
                end_point.display_forecast(data)
            else:
                print("Invalid number of days. Please enter a number between 1 and 5.")
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
