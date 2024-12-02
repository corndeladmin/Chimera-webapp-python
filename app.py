import os
import sys
import logging
import redis
import json
from datetime import datetime
from flask import Flask, render_template

# Configuration variables
LOG_FILE_DIRECTORY = os.getenv("LOG_FOLDER", "/var/log/chimera")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
DATA_FOLDER = os.getenv("DATA_FOLDER")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", 5001))

# Ensure logging directory is writable
if not os.access(LOG_FILE_DIRECTORY, os.W_OK):
    print(f"Error opening log file directory: '{LOG_FILE_DIRECTORY}'. Directory must exist and be writable.")
    sys.exit(1)

# Flask setup
app = Flask(__name__)

# Set up logging
log_file_path = os.path.join(LOG_FILE_DIRECTORY, f'webapp-{datetime.now().strftime("%Y.%m.%d")}.log')
file_logging_handler = logging.FileHandler(log_file_path)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_logging_handler.setFormatter(formatter)
app.logger.addHandler(file_logging_handler)

log_level = os.getenv("LOG_LEVEL")
if log_level:
    app.logger.setLevel(log_level)
app.logger.info(f"Logging to '{LOG_FILE_DIRECTORY}'")

# Redis setup (if required)
using_redis = REDIS_HOST and REDIS_PORT
if using_redis:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

def load_dataset(dataset):
    default_data = {
        "datasetName": "matter-mood-copy",
        "data": [
            {"comment": "56 km S of Whites City, New Mexico", "long": -104.4225, "lat": 31.6701, "magnitude": 1},
            {"comment": "30 km SE of Mina, Nevada", "long": -117.8687, "lat": 38.1882, "magnitude": 4.5},
            {"comment": "33 km NW of Willow, Alaska", "long": -150.5008, "lat": 61.9583},
            {"comment": "14km SE of Ocotillo Wells, CA", "long": -116.0133333, "lat": 33.0595},
            {"comment": "7 km WNW of Four Mile Road, Alaska", "long": -149.2703, "lat": 64.6186}
        ],
        "generationTime": 1596450405247,
        "centre": "[0, 0]",
        "zoom": None
    }

    if not dataset:
        return default_data

    try:
        if using_redis:
            data = redis_client.get(dataset)
            if data:
                return json.loads(data)
        else:
            file_path = os.path.join(DATA_FOLDER, dataset)
            with open(file_path, 'r') as file:
                return json.load(file)
    except Exception as e:
        app.logger.error(f"Error loading dataset: {str(e)}")
        return None

    return None


@app.route("/<dataset>", methods=["GET"])
@app.route("/", methods=["GET"])
def index(dataset=None):
    app.logger.info(f"Called with {f"dataset: {dataset}"}")
    data = load_dataset(dataset)
    if data is None:
        return "Dataset not found!"
    
    view = {
        "title": dataset,
        "time": datetime.fromtimestamp(data['generationTime'] / 1000).strftime("%H:%M:%S"),
        "centre": data.get('centre', '[0, 0]'),
        "zoom": data.get('zoom', 2),
        "data": json.dumps(data['data'])
    }

    return render_template("index.html.jinja", **view)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=WEBAPP_PORT, debug=True)
