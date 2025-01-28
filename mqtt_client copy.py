# mqtt_client.py
import paho.mqtt.client as mqtt
from flask import Flask, jsonify
import threading
import json

app = Flask(__name__)

# Initialize data storage for multiple sensors
iot_data = {
    "nongseua": {
        "airquality": {},
        "smellfamale": {},
        "smellmale": {},
        "doors": {},
        "peoplecounter": {},
        "gps": {}
    },
    "supanburi": {
        "airquality": {},
        "smellfamale": {},
        "smellmale": {},
        "doors": {},
        "peoplecounter": {},
        "gps": {}
    }
}

# MQTT settings
BROKER = 'broker.emqx.io'
PORT = 1883
SENSORS = ["nongseua", "supanburi"]

# Generate topics for all sensors
TOPICS = []
for sensor in SENSORS:
    sensor_topics = [
        (f"raaspal/{sensor}/airquality", 0),
        (f"raaspal/{sensor}/smellfamale", 0),
        (f"raaspal/{sensor}/smellmale", 0),
        (f"raaspal/{sensor}/peoplecounter", 0),
        (f"raaspal/{sensor}/gps", 0)
    ]
    TOPICS.extend(sensor_topics)
    # If you have multiple doors per sensor, include them as well
    for door_num in range(1, 5):  # Example: 4 doors
        TOPICS.append((f"raaspal/{sensor}/door{door_num}", 0))

# MQTT Callback when connecting to the broker
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    for topic in TOPICS:
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic[0]}")

# MQTT Callback when receiving a message
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"Received `{payload}` from `{topic}` topic")

    try:
        # Parse the payload as JSON safely
        data = json.loads(payload)

        # Extract sensor ID and data type from the topic
        parts = topic.split('/')
        if len(parts) != 3:
            print(f"Unexpected topic format: {topic}")
            return

        _, sensor_id, data_type = parts

        if sensor_id not in iot_data:
            print(f"Unknown sensor ID: {sensor_id}")
            return

        if data_type == "airquality":
            iot_data[sensor_id]["airquality"] = data
        elif data_type == "smellfamale":
            iot_data[sensor_id]["smellfamale"] = data
        elif data_type == "smellmale":
            iot_data[sensor_id]["smellmale"] = data
        elif data_type == "peoplecounter":
            iot_data[sensor_id]["peoplecounter"] = data
        elif data_type == "gps":
            # Assuming GPS data has 'latitude' and 'longitude'
            iot_data[sensor_id]["gps"] = data
            # Optionally, update airquality data with GPS
            iot_data[sensor_id]["airquality"]["latitude"] = data.get("latitude", iot_data[sensor_id]["airquality"].get("latitude", -37.8136))
            iot_data[sensor_id]["airquality"]["longitude"] = data.get("longitude", iot_data[sensor_id]["airquality"].get("longitude", 144.9631))
        elif data_type.startswith("door"):
            iot_data[sensor_id]["doors"][data_type] = data
        else:
            print(f"Unknown data type: {data_type}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from topic `{topic}`: {e}")
    except Exception as e:
        print(f"Unexpected error processing message from `{topic}`: {e}")

# Flask endpoint to get IoT data for all sensors
@app.route("/data", methods=["GET"])
def get_data():
    return jsonify(iot_data)

# Start MQTT Client
def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    # Run MQTT client in a separate thread
    mqtt_thread = threading.Thread(target=start_mqtt)
    mqtt_thread.start()

    # Run Flask app
    app.run(debug=True, use_reloader=False)
