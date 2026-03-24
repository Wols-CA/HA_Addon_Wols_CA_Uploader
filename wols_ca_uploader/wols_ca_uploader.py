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
failed_attempts = 0

def on_connect(client, userdata, flags, reason_code, properties=None):
    global failed_attempts
    if reason_code == 0:
        print(f"✅ Succesvol verbonden met {MQTT_BROKER} als gebruiker: '{MQTT_USER}'")
        failed_attempts = 0
        client.subscribe(MQTT_TOPIC)
        print(f"📡 Geabonneerd op topic: {MQTT_TOPIC}")
    else:
        failed_attempts += 1
        print(f"❌ Verbinding mislukt voor '{MQTT_USER}' (Code: {reason_code}). Poging: {failed_attempts}")
        if reason_code == 5:
            print("   👉 Tip: Code 5 betekent 'Not Authorized'. Controleer je gebruikersnaam/wachtwoord.")

def on_message(client, userdata, msg):
    print(f"📩 Bericht ontvangen op {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode())
        filename = payload["filename"]
        version = payload["version"]
        part = payload["part"]
        total_parts = payload["total_parts"]
        data = base64.b64decode(payload["data"])

        key = (filename, version)
        parts_buffer[key][part] = data

        if len(parts_buffer[key]) == total_parts:
            full_content = b''.join(parts_buffer[key][i] for i in range(1, total_parts + 1))
            
            if not os.path.exists(AUTOMATIONS_DIR):
                os.makedirs(AUTOMATIONS_DIR)

            with open(os.path.join(AUTOMATIONS_DIR, filename), "w") as f:
                f.write(full_content.decode('utf-8'))
            
            print(f"🚀 Bestand geïnstalleerd: {filename} (v{version})")
            current_versions[filename] = version
            del parts_buffer[key]
    except Exception as e:
        print(f"🔥 Fout bij verwerken: {e}")

# --- SETUP ---
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

if MQTT_USER and MQTT_PASS:
    print(f"🔑 Gebruikersnaam gevonden in configuratie: '{MQTT_USER}'")
    # We tonen het wachtwoord niet, maar wel dat het gezet is
    print(f"🔐 Wachtwoord is ingesteld (lengte: {len(MQTT_PASS)} tekens)")
    client.username_pw_set(MQTT_USER, MQTT_PASS)
else:
    print("⚠️ Geen gebruikersnaam/wachtwoord geconfigureerd. We proberen anoniem te verbinden.")

print(f"🚀 Start Uploader Service...")

# --- MAIN LOOP ---
while True:
    try:
        print(f"Verbinden met {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever() 
    except Exception as e:
        failed_attempts += 1
        print(f"💥 Netwerkfout: {e}")
    
    # Vertraging bij mislukking
    if failed_attempts >= 5:
        print("🕒 Te veel mislukte pogingen. Wachten van 5 minuten...")
        time.sleep(300)
    else:
        print(f"🔄 Korte pauze van 15 seconden voor herpoging {failed_attempts + 1}...")
        time.sleep(15)
