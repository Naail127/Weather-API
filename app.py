import time
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

CACHE_DURATION = 600
weather_cache = {}

def get_weather_data(lat, lon):
    cache_key = f"{lat},{lon}"
    current_time = time.time()

    if cache_key in weather_cache:
        timestamp, data = weather_cache[cache_key]
        if current_time - timestamp < CACHE_DURATION:
            return data

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m",
            "timezone": "auto"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        raw_data = response.json()

        current = raw_data.get("current_weather", {})
        hourly = raw_data.get("hourly", {})
        
        avg_humidity = 0
        if "relativehumidity_2m" in hourly:
            next_12_hours = hourly["relativehumidity_2m"][:12]
            avg_humidity = sum(next_12_hours) / len(next_12_hours)

        processed_data = {
            "temperature": current.get("temperature"),
            "windspeed": current.get("windspeed"),
            "winddirection": current.get("winddirection"),
            "is_day": current.get("is_day"),
            "avg_humidity_12h": round(avg_humidity, 1),
            "source": "API (Fresh)"
        }

        weather_cache[cache_key] = (current_time, processed_data)
        return processed_data

    except requests.exceptions.RequestException:
        return {"error": "Failed to fetch weather data"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/weather', methods=['GET'])
def weather_api():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not lat or not lon:
        return jsonify({"error": "Missing latitude or longitude"}), 400
        
    data = get_weather_data(lat, lon)
    
    if data.get("source") != "API (Fresh)":
        data["source"] = "Cache (Saved)"
        
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
