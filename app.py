import os
import sys
import logging
import redis
import json
from datetime import datetime
from flask import Flask, request, render_template_string
import jinja2

# Configuration variables
LOG_FILE_DIRECTORY = "/var/log/chimera"
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
DATA_FOLDER = os.getenv("DATA_FOLDER")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", 5001))

# Ensure logging directory is writable
if not os.access(LOG_FILE_DIRECTORY, os.W_OK):
    print(f"Error opening log file directory: '{LOG_FILE_DIRECTORY}'. Directory must exist and be writable.")
    sys.exit(1)

# Set up logging
log_file_path = os.path.join(LOG_FILE_DIRECTORY, f'webapp-{datetime.now().strftime("%Y.%m.%d")}.log')
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)
log_level = os.getenv("LOG_LEVEL")
if log_level:
    logging.getLogger().setLevel(log_level)
logging.info(f"Logging to '{LOG_FILE_DIRECTORY}'")

# Flask setup
app = Flask(__name__)

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
        logging.error(f"Error loading dataset: {str(e)}")
        return None

    return None

def render_template(dataset, data):
    template = '''
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.6.0/dist/leaflet.css" integrity="sha512-xwE/Az9zrjBIphAcBb3F6JVqxf46+CDLwfLMHloNu6KEQCAWi6HcDUbeOfBIptF7tcCzusKFjFw2yuvEpDL9wQ==" crossorigin="" />
        <script src="https://unpkg.com/leaflet@1.6.0/dist/leaflet.js" integrity="sha512-gZwIG9x3wUXg2hdXF6+rVkLF/0Vi9U8D2Ntg4Ga5I5BZpVkVxlJWbSQtXPSiUTtC0TjtGOmxa1AJPuV0CPthew==" crossorigin=""></script>
        <link href="data:image/x-icon;base64,AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAABILAAASCwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP74zAv++Mwn/vjMMf74zDH++Mwm//jMCQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD++c0d/vnNROPLnGDw4bRX/vnNQ/75zRkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACFKwBThSsAQgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACFLQABhSwAvIUsAKyGLgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAhS0AYYUtAP+FLQD+hS0AUgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACGLgAAhi4AYYUtAPmFLQD/hS0A/4UtAPWGLgBVhi4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACHLwABhi4AkoUuAP+MMQD/uEQA/7ZDAP+LMAD/hS4A/oYuAIONNAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAhzAAWoYvAP/DTQD//8Ay///mSP//5Uj//7ov/7dHAP+FLwD+hi8ASgAAAAAAAAAAAAAAAAAAAAAAAAAAiC0AAIYwAM2UNgD//888///pS///6Uv//+lL///pS///xjf/jTMA/4UwAL0AAAAAAAAAAAAAAAAAAAAAAAAAAIYxAAmGMAD66WQN///qTP//6Uz//+lM///pTP//6Uz//+pM/9NYCP+FMADxhTAAAwAAAAAAAAAAAAAAAAAAAACFMQALhTEA/PduE///6k3//+pN///qTf//6k3//+pN///qTf/iYg7/hTEA84MxAAMAAAAAAAAAAAAAAAAAAAAAhDEAAYQxANemQwH//+RK///qTf//6k3//+pN///qTf//30j/mjwA/4UxAMcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACEMgBshDEA//93Gf//50z//+tO///rTv//5Ev/8W0V/4QxAP+EMgBbAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgzIAA4MyAK+CMQD/tEwH//+AH///fh7/rUgF/4IxAP+BMQCggDEAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACDMgAEgjIAc4MyAOCDMgD+gzIA/oEyANyCMgBqgDEAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB+MAACgTIAFn4xABV/MQABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA+B8AAPgfAAD+fwAA/D8AAPw/AADwDwAA4AcAAOAHAADABwAAwAMAAMADAADABwAA4AcAAOAHAADwDwAA/D8AAA==" rel="icon" type="image/x-icon">
        <title>Chimera</title>
    </head>
    <body>
        <div style="width:100%; height:100%; font-family: Arial, Helvetica, sans-serif;">
            <div style="width:100%; height:90px">
                <h1>Chimera Reporting Server</h1>
                <h2>Current dataset: {{title}} (dataset generated: {{time}})</h2>
            </div>
            <div id="map" style="width:100%; height:calc(100% - 90px); text-align: center;">Loading...</div>
        </div>
        <script>
            var map = L.map('map', {
                center: {{centre}},
                zoom: {{zoom}}
            });
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            function addEarthQuake(lat, long, note) {
                L.marker([lat, long]).addTo(map).bindPopup(note);
            }

            function getData() {
                return {{data}};
            }

            async function makeGraph() {
                const data = getData() || [];
                data.forEach(element => addEarthQuake(element.lat, element.long, element.comment));
            }

            makeGraph();
        </script>
    </body>
    </html>
    '''
    view = {
        "title": dataset,
        "time": datetime.fromtimestamp(data['generationTime'] / 1000).strftime("%H:%M:%S"),
        "centre": data.get('centre', '[0, 0]'),
        "zoom": data.get('zoom', 2),
        "data": json.dumps(data['data'])
    }
    return jinja2.Template(template).render(view)

@app.route("/<dataset>", methods=["GET"])
@app.route("/", methods=["GET"])
def handle_dataset(dataset=None):
    logging.info(f"Called with dataset: {dataset}")
    data = load_dataset(dataset)
    if data is None:
        return "Dataset not found!"
    return render_template(dataset, data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=WEBAPP_PORT, debug=True)
