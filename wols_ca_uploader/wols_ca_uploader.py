import paho.mqtt.client as mqtt
import json
import base64
import os
import sys
from collections import defaultdict

# --- CONFIGURATION ---
MQTT_BROKER = "192.168.101.240" 
MQTT_PORT = 1883
MQTT_TOPIC = "wols-ca/admin/automation_upload"
AUTOMATIONS_DIR = "/config/automations" 

parts_buffer = defaultdict(dict)
current_versions = {}

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"✅ Connected successfully to Broker ({MQTT_BROKER})")
        # Abonneren zodra de verbinding staat
        client.subscribe(MQTT_TOPIC)
        print(f"📡 Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"❌ Connection failed with reason code: {reason_code}")

def on_message(client, userdata, msg):
    print(f"📩 New message received on {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode())
        filename = payload["filename"]
        device_id = payload.get("device_id", "unknown")
        version = payload["version"]
        part = payload["part"]
        total_parts = payload["total_parts"]
        data = base64.b64decode(payload["data"])

        key = (filename, version)
        parts_buffer[key][part] = data

        print(f"   Part {part}/{total_parts} received for {filename}")

        if len(parts_buffer[key]) == total_parts:
            print(f"   📦 All parts received for {filename}. Processing...")
            
            if filename in current_versions and version <= current_versions[filename]:
                print(f"   ⚠️ Skipping {filename}: v{version} is not newer than v{current_versions[filename]}")
                del parts_buffer[key]
                return

            full_content = b''.join(parts_buffer[key][i] for i in range(1, total_parts + 1))
            content_str = full_content.decode('utf-8')

            # Voeg device info toe als commentaar onderaan
            if "device_id:" not in content_str:
                content_str += f"\n\n# Automated Upload\n# Source: {device_id}\n# Version: {version}\n"

            if not os.path.exists(AUTOMATIONS_DIR):
                os.makedirs(AUTOMATIONS_DIR)

            script_path = os.path.join(AUTOMATIONS_DIR, filename)
            with open(script_path, "w") as f:
                f.write(content_str)
            
            print(f"🚀 Successfully installed {filename} (v{version}) at {script_path}")
            current_versions[filename] = version
            del parts_buffer[key]
            
    except Exception as e:
        print(f"🔥 Error processing message: {e}")

# --- MQTT CLIENT SETUP ---
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="wols_ca_automation_manager")

# Callbacks koppelen
client.on_connect = on_connect
client.on_message = on_message

print(f"🚀 Starting Uploader Service...")
print(f"Attempting to connect to {MQTT_BROKER} on port {MQTT_PORT}...")

try:
    # Verbinding maken
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    # Start de oneindige loop
    client.loop_forever()
except Exception as e:
    print(f"💥 Critical Error: {e}")
    sys.exit(1)
