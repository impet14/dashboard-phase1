import paho.mqtt.client as mqtt
from flask import Flask, jsonify
import threading
import json

app = Flask(__name__)

# Data storage
# Instead of having nested structures keyed by "sensor_id", 
# we will keep it simpler and store data by "device_name"
iot_data = {}

# MQTT settings
BROKER = "110.164.181.55"
PORT = 1883

# Subscribe to a single topic: sensor/data
TOPIC = "sensor/data"

# MQTT Callback when connecting to the broker
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(TOPIC)
    print(f"Subscribed to topic: {TOPIC}")

# MQTT Callback when receiving a message
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"Received `{payload}` from `{topic}` topic")

    try:
        data = json.loads(payload)

        # We expect a JSON payload with at least the "device_name"
        device_name = data.get("device_name")
        if not device_name:
            print("Error: 'device_name' not found in payload.")
            return

        # Store the entire JSON object by device_name
        iot_data[device_name] = data

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from topic `{topic}`: {e}")
    except Exception as e:
        print(f"Unexpected error processing message from `{topic}`: {e}")

# Flask endpoint to get IoT data
@app.route("/data", methods=["GET"])
def get_data():
    # Return whatever we have stored in iot_data
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
