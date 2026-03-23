import paho.mqtt.client as mqtt
import json
import base64
import os
from collections import defaultdict

# --- CONFIGURATION ---
# Jouw externe Docker MQTT broker
MQTT_BROKER = "192.168.101.240" 
MQTT_PORT = 1883
MQTT_TOPIC = "wols-ca/admin/automation_upload"

# Pad naar de automatiseringen map in Home Assistant
AUTOMATIONS_DIR = "/config/automations" 

# Buffer voor grote bestanden die in delen (parts) binnenkomen
parts_buffer = defaultdict(dict)
# Bijhouden van geïnstalleerde versies om overbodige uploads te voorkomen
current_versions = {}

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        filename = payload["filename"]
        device_id = payload["device_id"]
        version = payload["version"]
        part = payload["part"]
        total_parts = payload["total_parts"]
        data = base64.b64decode(payload["data"])

        key = (filename, version)
        parts_buffer[key][part] = data

        if len(parts_buffer[key]) == total_parts:
            # Versiecontrole: alleen installeren als de versie nieuwer is
            if filename in current_versions and version <= current_versions[filename]:
                print(f"Skipping {filename}: v{version} is not newer than v{current_versions[filename]}")
                del parts_buffer[key]
                return

            # Bestandsdelen samenvoegen
            full_content = b''.join(parts_buffer[key][i] for i in range(1, total_parts + 1))
            content_str = full_content.decode('utf-8')

            # device_id toevoegen als commentaar onderaan het YAML bestand indien afwezig
            if "device_id:" not in content_str:
                content_str += f"\n# Automated Upload\ndevice_id: {device_id}\n"

            # Map aanmaken als deze nog niet bestaat
            if not os.path.exists(AUTOMATIONS_DIR):
                os.makedirs(AUTOMATIONS_DIR)

            # Bestand wegschrijven naar de HA config map
            script_path = os.path.join(AUTOMATIONS_DIR, filename)
            with open(script_path, "w") as f:
                f.write(content_str)
            
            print(f"Successfully installed {filename} (v{version})")
            current_versions[filename] = version
            del parts_buffer[key]
            
    except Exception as e:
        print(f"Error processing message: {e}")

# Initialiseer MQTT Client
client = mqtt.Client(client_id="wols_ca_automation_manager")

# Optioneel: Gebruikersnaam/Wachtwoord instellen indien nodig
# client.username_pw_set("GEBRUIKERSNAAM", "WACHTWOORD")

print(f"Connecting to {MQTT_BROKER} on port {MQTT_PORT}...")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)
    client.on_message = on_message
    print("Uploader Service Started. Waiting for messages...")
    client.loop_forever()
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")
