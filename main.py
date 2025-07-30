import tkinter as tk
from tkinter import messagebox
import requests
import random
import csv
import os
from datetime import datetime

# Config
OPENWEATHER_API_KEY = '4042dd5dd87af4d62b49c34b3a884cac'
CLOTHES_CSV = 'clothes_outerwear.csv'
WEATHER_CSV = 'weather_data.csv'

TEMPERATURE_RANGES = {
    'hot': (25, float('inf')),
    'warm': (15, 24.9),
    'cool': (5, 14.9),
    'cold': (-5, 4.9),
    'very_cold': (-15, -5.1),
    'freezing': (float('-inf'), -15.1),
}
RAIN_CATEGORY = 'rain'

# Helper functions
def get_lat_lon_from_city(city, api_key):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if data:
            return data[0]['lat'], data[0]['lon']
    except Exception as e:
        print("Error getting lat/lon:", e)
    return None, None

def get_weather_data(lat, lon, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

def save_weather_data(weather_data):
    date = datetime.utcfromtimestamp(weather_data['dt']).strftime('%Y-%m-%d %H:%M:%S')
    temp = weather_data['main']['temp']
    feels_like_temp = weather_data['main']['feels_like']
    precipitation = weather_data['weather'][0]['main']

    file_exists = os.path.isfile(WEATHER_CSV)
    with open(WEATHER_CSV, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['date', 'temperature', 'feels_like_temperature', 'precipitation'])
        writer.writerow([date, temp, feels_like_temp, precipitation])

def load_clothes_data(csv_file):
    clothes_data = []
    try:
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                clothes_data.append(row)
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found.")
    return clothes_data

def suggest_clothes_for_weather(temp, feels_like, precipitation, clothes_data, gender):
    suitable = {"top": [], "bottom": [], "outerwear": [], "accessory": []}
    effective_temp = min(temp, feels_like)

    for item in clothes_data:
        item_gender = item.get('Gender', 'Unisex').lower()
        if item_gender != 'unisex' and item_gender != gender.lower():
            continue
        if 'rain' in precipitation.lower() and item['Category'].lower() == RAIN_CATEGORY:
            if item['Type'] in suitable:
                suitable[item['Type']].append(item)
        else:
            for key, (min_temp, max_temp) in TEMPERATURE_RANGES.items():
                if min_temp <= effective_temp <= max_temp and item['Category'].lower() == key:
                    if item['Type'] in suitable:
                        suitable[item['Type']].append(item)

    for clothing_type in suitable:
        if not suitable[clothing_type]:
            fallback = [item for item in clothes_data if item['Type'] == clothing_type and item.get('Gender', 'Unisex').lower() in [gender.lower(), 'unisex']]
            suitable[clothing_type] = fallback

    chosen = {k: (random.choice(v)['Item'] if v else "None") for k, v in suitable.items()}
    return chosen

# GUI Logic
def generate_outfit():
    city = city_entry.get().strip()
    gender = gender_var.get().strip()

    if not city:
        messagebox.showwarning("❗ Input Missing", "Please enter a city name.")
        return
    if gender not in ['Male', 'Female']:
        messagebox.showwarning("❗ Input Missing", "Please select your gender.")
        return

    lat, lon = get_lat_lon_from_city(city, OPENWEATHER_API_KEY)
    if lat is None or lon is None:
        messagebox.showerror("❌ Error", "Could not find location.")
        return

    weather_data = get_weather_data(lat, lon, OPENWEATHER_API_KEY)
    if not weather_data:
        messagebox.showerror("❌ API Error", "Failed to fetch weather data.")
        return

    save_weather_data(weather_data)

    temp = weather_data['main']['temp']
    feels_like = weather_data['main']['feels_like']
    precipitation = weather_data['weather'][0]['main']

    outfit = suggest_clothes_for_weather(temp, feels_like, precipitation, clothes_data, gender)

    result = f"""🧭 Weather Summary:
🌆 City: {city}
🌡️ Temp: {temp}°C | Feels like: {feels_like}°C
☁️ Condition: {precipitation}

👗 Suggested Outfit:
👕 Top: {outfit['top']}
👖 Bottom: {outfit['bottom']}
🧥 Outerwear: {outfit['outerwear']}
🧣 Accessory: {outfit['accessory']}
"""
    output_label.config(text=result)

# Load clothes data
clothes_data = load_clothes_data(CLOTHES_CSV)

# GUI Setup
root = tk.Tk()
root.title("🧥 What to Wear - Weather-based Outfit Suggester")
root.geometry("550x600")
root.configure(bg="#f0f8ff")  # light sky blue

# Widgets
tk.Label(root, text="🌇 Enter Your City:", font=("Helvetica", 14, "bold"), bg="#f0f8ff").pack(pady=10)
city_entry = tk.Entry(root, font=("Helvetica", 13), width=30)
city_entry.pack()

tk.Label(root, text="🧑 Select Gender:", font=("Helvetica", 14, "bold"), bg="#f0f8ff").pack(pady=10)
gender_var = tk.StringVar()
gender_menu = tk.OptionMenu(root, gender_var, "Male", "Female")
gender_menu.config(font=("Helvetica", 12), width=10, bg="lightblue")
gender_menu.pack()

tk.Button(root, text="🎯 Get Outfit Suggestion", command=generate_outfit, bg="#4CAF50", fg="white", font=("Helvetica", 13, "bold"), padx=10, pady=5).pack(pady=20)

output_label = tk.Label(root, text="", wraplength=500, justify="left", font=("Helvetica", 12), bg="#f0f8ff", fg="#333")
output_label.pack(pady=20)

# Start GUI loop
root.mainloop()
