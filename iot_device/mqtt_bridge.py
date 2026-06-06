import json
import paho.mqtt.client as mqtt
import requests
import threading
import time

# CONFIGURACIÓN
BROKER = "broker.hivemq.com"
TOPIC = "fisi/smat/estaciones/#"  # Reto: suscripción al tópico correcto
API_URL = "http://127.0.0.1:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl9zbWF0IiwiZXhwIjoxNzgwNzg3NzYxfQ.Mp7KNv8HCpvLMCbW9_XO3oPbBMXsV1tomRJTymT0mbk"  # ← Pega aquí tu token

# Diccionario para rastrear el último mensaje de cada estación
last_seen = {}


def on_message(client, userdata, msg):
    try:
        # 1. Decodificar el mensaje MQTT
        payload = json.loads(msg.payload.decode())
        print(f"📩 Mensaje recibido en {msg.topic}: {payload}")

        # 2. Extraer el ID de la estación desde el tópico
        # Ejemplo: fisi/smat/estaciones/1 -> ID = 1
        estacion_id = msg.topic.split("/")[-1]

        # Actualizar tiempo de último mensaje (para detectar offline)
        last_seen[estacion_id] = time.time()

        # 3. Preparar los datos para el Backend
        data_to_send = {
            "valor": payload["valor"],
            "estacion_id": int(estacion_id)
        }

        # 4. Enviar a la API mediante HTTP POST (Reto: persistencia)
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.post(
            f"{API_URL}/lecturas/",
            json=data_to_send,
            headers=headers
        )

        if response.status_code == 201:
            print(f"✅ Dato persistido en DB para estación {estacion_id}")
        else:
            print(f"⚠️ Error API ({response.status_code}): {response.text}")

    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")


def check_deadlines():
    """Reto: Detectar estaciones offline si no envían datos en 30 segundos."""
    while True:
        current_time = time.time()
        for eid, t in list(last_seen.items()):
            if current_time - t > 30:  # 30 segundos de gracia
                print(f"🚨 ALERTA: Estación {eid} está OFFLINE")
                # Notificar al backend el estado offline
                try:
                    headers = {"Authorization": f"Bearer {TOKEN}"}
                    requests.post(
                        f"{API_URL}/lecturas/",
                        json={"valor": -1.0, "estacion_id": int(eid)},
                        headers=headers
                    )
                except Exception as e:
                    print(f"❌ Error notificando offline: {e}")
        time.sleep(10)


# Lanzar el hilo de monitoreo antes del loop MQTT
threading.Thread(target=check_deadlines, daemon=True).start()

# Configuración del Cliente MQTT
client = mqtt.Client()
client.on_message = on_message

print("🚀 Bridge SMAT iniciado. Esperando datos...")
client.connect(BROKER, 1883)
client.subscribe(TOPIC)
client.loop_forever()