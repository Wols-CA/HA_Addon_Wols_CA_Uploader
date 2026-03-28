import paho.mqtt.client as mqtt
import os
import yaml
import json
import logging

from mqtt_triggers import handle_mqtt_message

upLoaderVersion = ""
mqttBroker = "localhost"  # Change as needed
mqttPort = 1883
mqttUser = ""
mqttPassword = "" 
mqttTopic = ""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def get_version_from_yaml():
    version_file = "/config/version.yaml"
    with open(version_file, "r") as f:
        data = yaml.safe_load(f)
    return data.get("version", "Unknown")

def get_mqtt_settings():
    config_file = "/data/options.json"
    with open(config_file, 'r') as f:
        data = json.load(f)

        mqttBroker = data.get("mqttBroker", "localhost")
        mqttPort = data.get("mqttPort", 1883)
        mqttUser = data.get("mqttUser", None)
        mqttPassword = data.get("mqtt_password", None)
        mqttTopic = data.get("mqttTopic", None)
        f.close();

    printString = f"MQTT Settings - Broker: {mqttBroker}, Port: {mqttPort}, User: {mqttUser}, Topic: {mqttTopic}"
    logging.info(printString)
    logging.info("")
    return mqttBroker, mqttPort, mqttUser, mqttPassword, mqttTopic


def on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code", rc)
    # Subscribe to all relevant topics for triggers, handshake, secrets, etc.
    client.subscribe("wols-ca/trigger/#")
    client.subscribe("wols-ca/keys/public")
    client.subscribe("wols-ca/secrets/request/#")
    client.subscribe("wols-ca/uploader/required_version")
    # After connecting to MQTT:
    publish_version(client, upLoaderVersion)
    # Add more as needed
    

def on_message(client, userdata, msg):
    if not handle_mqtt_message(client, msg, upLoaderVersion):
        logging.info(f"No handler for topic: {msg.topic}")

def publish_version(client, version):
    client.publish("wols-ca/uploader/version", version, retain=True)

def LogStart( version, broker, port, user, password, topic):

    starString = f"************************************************************************************************"

    logging.info( str(starString))
    logging.info("WOLS CA Uploader - MQTT Client for Home Assistant Add-on")
    logging.info( str(starString))
    logging.info("")

    logging.info(f"Version  : {version}")
    logging.info("MQTT Settings:")
    logging.info(f"  Broker : {broker}")
    logging.info(f"  Port   : {port}")
    logging.info(f"  User   : {user}") 
    logging.info(f"  Topic  : {topic}")
    logging.info("")
    logging.info( str(starString))
    logging.info("")


def main():
    uploaderVersion = get_version_from_yaml()
    mqttBroker, mqttPort, mqttUser, mqttPassword, mqttTopic = get_mqtt_settings()

    LogStart( uploaderVersion, mqttBroker, mqttPort, mqttUser, mqttPassword, mqttTopic)
    
    client = mqtt.Client()
    if mqttUser and mqttPassword:
        client.username_pw_set(mqttUser, mqttPassword)
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=60)  # delays in seconds
    client.connect(mqttBroker, mqttPort, 60)
    publish_version(client, upLoaderVersion)
    client.loop_forever()

if __name__ == "__main__":
    main()
