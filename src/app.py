import requests
import yaml
import logging
import json
from flask import Flask, request, jsonify, render_template
from typing import Optional, Dict, Any
import sqlite3

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Flask app setup
app = Flask(__name__)


class WeatherEndPoint:
    """
    End point class to retrieve the weather data.
    """

    _config = None  # Class variable to store configuration

    def __init__(self, config_path: str, db_connection: sqlite3.Connection) -> None:
        if WeatherEndPoint._config is None:
            WeatherEndPoint._config = self.load_config(config_path)
        self.config = WeatherEndPoint._config
        self.api_key = self.config["api_key"]
        self.current_cast_url = self.config["current_cast_url"]
        self.forecast_url = self.config["forecast_url"]
        self.weather_maps_url = self.config["weather_maps_url"]
        self.air_pollution_url = self.config["air_pollution_url"]
        self.conn = db_connection
        self.cursor = self.conn.cursor()
        self.init_db()

    @staticmethod
    def load_config(config_path: str) -> Dict[str, str]:
        """
        Loads the YAML configuration file that contains the API urls and API key.

        :param config_path: string for the config file path.
        :type config_path: str
        :return: dict containing the strings for each param (KEY and URLs).
        :rtype: Dict[str, str]
        """
        with open(config_path, "r") as config_file:
            return yaml.safe_load(config_file)

    def init_db(self) -> None:
        """
        Initialize the SQLite database and create tables if they don't exist.
        """
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS api_calls (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                endpoint TEXT,
                                city_name TEXT,
                                response_code INTEGER,
                                data TEXT,
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                               )"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS api_call_count (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                               )"""
        )
        self.conn.commit()

    def save_to_db(
        self, endpoint: str, city_name: str, response_code: int, data: Dict[str, Any]
    ) -> None:
        """
        Save the API call data to the SQLite database.

        :param endpoint: The API endpoint called.
        :type endpoint: str
        :param city_name: The name of the city for which the data was requested.
        :type city_name: str
        :param response_code: The HTTP response code from the API call.
        :type response_code: int
        :param data: The data returned from the API call.
        :type data: Dict[str, Any]
        """
        self.cursor.execute(
            """INSERT INTO api_calls (endpoint, city_name, response_code, data)
                               VALUES (?, ?, ?, ?)""",
            (endpoint, city_name, response_code, json.dumps(data)),
        )
        self.conn.commit()

    def increment_api_call_count(self) -> None:
        """
        Counter for how many times the API was requested.
        """
        self.cursor.execute("""INSERT INTO api_call_count DEFAULT VALUES""")
        self.conn.commit()

    def get_api_call_count(self, start_time: str, end_time: str) -> int:
        """
        Get the number of API calls made within a certain time frame.

        :param start_time: The start time in 'YYYY-MM-DD HH:MM:SS' format.
        :type start_time: str
        :param end_time: The end time in 'YYYY-MM-DD HH:MM:SS' format.
        :type end_time: str
        :return: The number of API calls made in the specified time frame.
        :rtype: int
        """
        self.cursor.execute(
            """SELECT COUNT(*) FROM api_call_count WHERE timestamp BETWEEN ? AND ?""",
            (start_time, end_time),
        )
        return self.cursor.fetchone()[0]

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
            logging.info(f"API Call: Status Code {response.status_code}")
            response.raise_for_status()
            weather_data = response.json()
            lat, lon = weather_data["coord"]["lat"], weather_data["coord"]["lon"]
            weather_data["air_pollution"] = self.get_air_pollution(lat, lon)
            self.save_to_db(
                "current_weather", city_name, response.status_code, weather_data
            )
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
            logging.info(f"API Call: Status Code {response.status_code}")
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
            logging.info(f"API Call: Status Code {response.status_code}")
            response.raise_for_status()
            forecast_data = response.json()
            self.save_to_db("forecast", city_name, response.status_code, forecast_data)
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


# Initialize the database connection once
db_connection = sqlite3.connect("weather_data.db", check_same_thread=False)
end_point = WeatherEndPoint("src/config.yaml", db_connection)

# Flask Routes
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/weather/<string:city_name>")
def current_weather(city_name: str):
    data = end_point.get_weather(city_name)
    return jsonify(data)


@app.route("/forecast/<string:city_name>/<int:days>")
@app.route("/forecast/<string:city_name>", defaults={"days": 1})
def weather_forecast(city_name: str, days: int):
    data = end_point.get_forecast(city_name, days)
    return jsonify(data)


@app.route("/api_call_count", methods=["GET"])
def api_call_count():
    start_time = request.args.get("start_time")
    end_time = request.args.get("end_time")
    count = end_point.get_api_call_count(start_time, end_time)
    return jsonify({"api_call_count": count})


def main() -> None:
    """
    Main function to run the weather application.
    """
    app.run(debug=True)


if __name__ == "__main__":
    main()
