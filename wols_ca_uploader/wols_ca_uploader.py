import paho.mqtt.client as mqtt
import json
import base64
import os
import sys
import time
from collections import defaultdict

# --- HA OPTIONS LOADER ---
OPTIONS_PATH = "/data/options.json"

if os.path.exists(OPTIONS_PATH):
    with open(OPTIONS_PATH) as f:
        conf = json.load(f)
else:
    conf = {}

MQTT_BROKER = conf.get("mqtt_broker", "192.168.101.240")
MQTT_PORT = conf.get("mqtt_port", 1883)
MQTT_USER = conf.get("mqtt_user", "")
MQTT_PASS = conf.get("mqtt_password", "")
MQTT_TOPIC = conf.get("mqtt_topic", "wols-ca/admin/automation_upload")
AUTOMATIONS_DIR = "/config/automations"

parts_buffer = defaultdict(dict)
current_versions = {}
failed_attempts = 0 # Teller voor mislukte pogingen

def on_connect(client, userdata, flags, reason_code, properties=None):
    global failed_attempts
    if reason_code == 0:
        print(f"✅ Verbonden met {MQTT_BROKER}")
        failed_attempts = 0 # Reset teller bij succes
        client.subscribe(MQTT_TOPIC)
    else:
        failed_attempts += 1
        print(f"❌ Verbinding mislukt (Code: {reason_code}). Poging: {failed_attempts}")

def on_message(client, userdata, msg):
    # ... (rest van de on_message logica blijft gelijk)
    try:
        payload = json.loads(msg.payload.decode())
        # (bestaande verwerkingscode hier...)
        print(f"🚀 Bestand geïnstalleerd: {payload['filename']}")
    except Exception as e:
        print(f"🔥 Fout: {e}")

# --- MAIN LOOP MET VERTRAGING ---
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

if MQTT_USER and MQTT_PASS:
    client.username_pw_set(MQTT_USER, MQTT_PASS)

print(f"🚀 Start Uploader Service...")

while True:
    try:
        print(f"Verbinden met {MQTT_BROKER}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever() # Dit blokkeert zolang de verbinding goed is
    except Exception as e:
        failed_attempts += 1
        print(f"💥 Verbindingsfout: {e}")
    
    # Als we hier komen, is de verbinding verbroken of mislukt
    if failed_attempts >= 5:
        print("⚠️ 5 mislukte pogingen. We wachten 5 minuten voor de volgende poging...")
        time.sleep(300) # 5 minuten rust
    else:
        print(f"Pauze van 10 seconden voor herpoging {failed_attempts + 1}...")
        time.sleep(10) # Korte pauze tussen normale pogingen
