import paho.mqtt.client as mqtt
import json
import time
import random

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "fisi/smat/estaciones/1"  # Tópico unificado

client = mqtt.Client()
client.connect(BROKER, PORT)

print("📡 Emisor MQTT iniciado. Enviando datos cada 10s...")

while True:
    payload = {
        "valor": round(random.uniform(20.0, 85.0), 2),
        "timestamp": time.time()
    }
    client.publish(TOPIC, json.dumps(payload))
    print(f"Enviado por MQTT: {payload}")
    time.sleep(10)