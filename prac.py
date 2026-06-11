#This module provides functionality to fetch and process weather data from the OpenWeatherMap API. It includes a function to retrieve weather information for a specified city, handling potential errors gracefully. The API key is securely loaded from an environment variable, ensuring that sensitive information is not hardcoded in the codebase.
from datetime import datetime as dt
import requests
#pip install python-dotenv
from dotenv import load_dotenv
import os

load_dotenv()

#Declare the API key as a global variable
#This allows us to access the API key throughout the module without needing to pass it as a parameter to functions.
api_key = os.getenv("WEATHER_API_KEY")

def get_weather(city):
    #Error handling is crucial when working with external APIs, as it helps to manage unexpected issues gracefully. In this function, we wrap the API call in a try-except block to catch any exceptions that may occur during the request or data processing. If an error occurs, we print a message indicating the error and return None, allowing the calling code to handle the situation appropriately.
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            #metric units will return temperature in Celsius, wind speed in meters per second, and other measurements in their respective metric units. This is often more convenient for users in many parts of the world, as it provides a more familiar and easily interpretable format for weather data.
            "units": "metric"
        }
    
        response = requests.get(url, params=params)
        
        #200--> ok
        if response.status_code == 200:
            data = response.json()
            print(data)
            weather = {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "sunrise": dt.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M:%S"),
                "sunset": dt.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M:%S")
            }
            
            return weather
        else:
            return None
        
    except Exception as e:
        print(f"Error occurred in {e}")
        
print(get_weather("Nyeri"))

