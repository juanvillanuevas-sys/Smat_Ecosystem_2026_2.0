import paho.mqtt.client as mqtt
import json
import time
import random

BROKER = "broker.hivemq.com"  # Broker público para pruebas
PORT = 1883
TOPIC = "fisi/smat/estaciones/1"  # Tópico alineado con el bridge

client = mqtt.Client()
client.connect(BROKER, PORT)

while True:
    payload = {
        "valor": round(random.uniform(44.0, 46.0), 2),
        "timestamp": time.time()
    }

    # Publicar datos en el "Topic"
    client.publish(TOPIC, json.dumps(payload))
    print(f"Enviado por MQTT: {payload}")
    time.sleep(10)