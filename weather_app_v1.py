import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

# MY TOKEN
API_TOKEN = ""
# WEATHER API KEY
RSA_KEY = ""

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def get_weather(url):
    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        return json.loads(response.text)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response




@app.route("/")
def home_page():
    return '''<body>
    <h1>Python SaaS: Weather App</h1>

    <label for="location">Location:</label>
    <input type="text" id="location" placeholder="Enter location" required>
    <input type="text" id="requester" placeholder="Enter requester name" required>

    <label for="date">Date:</label>
    <input type="date" id="date" required>

    <button onclick="fetchWeather()">Fetch Weather</button><br>
    Try API at:<br>
    <code>http://51.20.123.138:8000/weather/api/v1/ - POST</code>
    <code>
    {
    "token": "<your_token>",
    "requester_name": "Whatever",
    "location": "City,Country", 
    "date": "YYYY-MM-DD"
    }
    </code>

    <div id="weatherInfo"></div>

    <script>
        async function fetchWeather() {
            const location = document.getElementById('location').value;
            const date = document.getElementById('date').value;
            const requester = document.getElementById('requester').value;

            const apiUrl = `https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/${location}/${date}/${date}?unitGroup=metric&key=Q2UBER6BGWFHL9MBR585VRNXJ&contentType=json`;

            try {
                const response = await fetch(apiUrl);
                const data = await response.json();

                const weatherInfo = `
                    <p>Date: ${date}</p>
                    <p>Requester: ${requester}</p>
                    <p>Location: ${location}</p>
                    <p>Temperature: ${data.days[0].temp}</p>
                    <p>Description: ${data.days[0].description}</p>
                `;

                document.getElementById('weatherInfo').innerHTML = weatherInfo;
            } catch (error) {
                console.error('Error fetching weather:', error);
                document.getElementById('weatherInfo').innerHTML = '<p>Error fetching weather information.</p>';
            }
        }
    </script>
</body>'''
    

@app.route("/weather/api/v1/", methods=["POST"])
def weather_endpoint():
    start_dt = dt.datetime.now()
    json_data = request.get_json()

    # Check token
    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    # Retrive variables from request body
    location = json_data.get("location")
    requester_name = json_data.get("requester_name")
    date = json_data.get("date")

    if date is None or location is None: raise InvalidUsage("missing required parameters", status_code=400)

    weather_request = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"+location+"/"+date+"/"+date+"?unitGroup=metric&key="+RSA_KEY+"&contentType=json"

    weather = get_weather(weather_request)
    end_dt = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    result = {"requester_name": requester_name, 
        "timestamp": end_dt, 
        "location": location, 
        "date": date, 
        "weather": {
            "temp_c": weather.get("days")[0].get("temp"),
            "wind_kph": weather.get("days")[0].get("windspeed"),
            "pressure_mb": weather.get("days")[0].get("pressure"),
            "humidity": weather.get("days")[0].get("humidity"),
            "description": weather.get("days")[0].get("description")
        }
    }

    return result