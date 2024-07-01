import requests
import json

# Load API key from config.json
def load_config():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    return config['api_key']

API_KEY = load_config()
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather?'

def get_weather(city_name):
    complete_url = BASE_URL + 'q=' + city_name + '&appid=' + API_KEY + '&units=metric'
    response = requests.get(complete_url)
    return response.json()

def display_weather(data):
    if data['cod'] != '404':
        main = data['main']
        wind = data['wind']
        weather = data['weather'][0]
        
        temperature = main['temp']
        pressure = main['pressure']
        humidity = main['humidity']
        weather_description = weather['description']
        wind_speed = wind['speed']

        print(f"Temperature: {temperature}°C")
        print(f"Pressure: {pressure} hPa")
        print(f"Humidity: {humidity}%")
        print(f"Weather Description: {weather_description}")
        print(f"Wind Speed: {wind_speed} m/s")
    else:
        print("City Not Found")

def main():
    city_name = input("Enter city name: ")
    weather_data = get_weather(city_name)
    display_weather(weather_data)

if __name__ == "__main__":
    main()
