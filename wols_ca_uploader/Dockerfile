# We gebruiken een pure Python image om de s6-overlay fouten te omzeilen
FROM python:3.12-alpine

# Installeer de benodigde MQTT bibliotheek
RUN pip install --no-cache-dir paho-mqtt

# Map aanmaken voor de applicatie
WORKDIR /app

# Kopieer je python script naar de container
COPY wols_ca_uploader.py .

# Schakel s6-overlay expliciet uit voor Home Assistant
ENV S6_SERVICES_GRACETIME=0
ENV S6_READ_ONLY_ROOT=1

# Start het script direct als hoofdproces (PID 1)
ENTRYPOINT ["python", "wols_ca_uploader.py"]
