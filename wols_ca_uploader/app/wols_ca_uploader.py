import paho.mqtt.client as mqtt
import os
import yaml
import json

from mqtt_triggers import handle_mqtt_message

UPLOADER_VERSION = ""
MQTT_BROKER = "localhost"  # Change as needed
MQTT_PORT = 1883
MQTT_USER = ""
MQTT_PASSWORD = "" 
MQTT_TOPIC = ""

def get_version_from_yaml():
    version_file = "/config/version.yaml"
    with open(version_file, "r") as f:
        data = yaml.safe_load(f)
    UPLOADER_VERSION = data.get("version", "Unknown")

def get_mqtt_settings():
    config_file = "/data/options.json"
    with open(config_file, 'r') as f:
        data = json.load(f)

        MQTT_BROKER = data.get("mqtt_broker", "localhost")
        MQTT_PORT = data.get("mqtt_port", 1883)
        MQTT_USER = data.get("mqtt_user", None)
        MQTT_PASSWORD = data.get("mqtt_password", None)
        MQTT_TOPIC = data.get("mqtt_topic", None)
    printString = f"MQTT Settings - Broker: {MQTT_BROKER}, Port: {MQTT_PORT}, User: {MQTT_USER}, Topic: {MQTT_TOPIC}"
    print(printString)
    print


def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    # Subscribe to all relevant topics for triggers, handshake, secrets, etc.
    client.subscribe("wols-ca/trigger/#")
    client.subscribe("wols-ca/keys/public")
    client.subscribe("wols-ca/secrets/request/#")
    client.subscribe("wols-ca/uploader/required_version")
    # After connecting to MQTT:
    publish_version(client, UPLOADER_VERSION)
    # Add more as needed
    

def on_message(client, userdata, msg):
    if not handle_mqtt_message(client, msg, UPLOADER_VERSION):
        print(f"No handler for topic: {msg.topic}")

def publish_version(client, version):
    client.publish("wols-ca/uploader/version", version, retain=True)

def printStart():
    get_version_from_yaml()
    startString = f"************************************************************************************************"

    print( str(startString))
    print("WOLS CA Uploader - MQTT Client for Home Assistant Add-on")
    print( str(startString))
    print("")

    printString = f"Uploader Version: " + str(UPLOADER_VERSION)
    print(str(printString))
    print("")


def main():
    
    get_mqtt_settings()

    client = mqtt.Client()
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=60)  # delays in seconds
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    publish_version(client, UPLOADER_VERSION)
    client.loop_forever()

if __name__ == "__main__":
    main()
