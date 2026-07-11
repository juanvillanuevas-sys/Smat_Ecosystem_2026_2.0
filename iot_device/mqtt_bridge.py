import json
import paho.mqtt.client as mqtt
import requests
import time
import os
import sys

# CONFIGURACIÓN
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "fisi/smat/estaciones/+"  # Escucha todas las estaciones

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000/lecturas/")
JWT_TOKEN = os.environ.get("JWT_TOKEN", "")  # ← Pon tu token aquí o en variable de entorno

cache_estaciones = {}
UMBRAL_CAMBIO = 0.05
TIEMPO_VIDA = 60


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("🟢 Conectado exitosamente al Broker MQTT")
        client.subscribe(MQTT_TOPIC)
        print(f"📡 Escuchando en: {MQTT_TOPIC}")
    else:
        print(f"🔴 Error de conexión. Código: {rc}")
        sys.exit(1)


def on_message(client, userdata, msg):
    try:
        payload_raw = msg.payload.decode("utf-8")
        data_json = json.loads(payload_raw)

        topic_parts = msg.topic.split('/')
        estacion_id = int(topic_parts[3])
        valor_actual = float(data_json["valor"])

        print(f"📩 Telemetría recibida de Estación [{estacion_id}]: {valor_actual}")

        tiempo_actual = time.time()
        debe_guardarse = False

        if estacion_id not in cache_estaciones:
            print(f"🆕 Primera lectura de estación {estacion_id}. Se almacenará.")
            debe_guardarse = True
        else:
            ultimo_valor = cache_estaciones[estacion_id]["valor"]
            ultimo_tiempo = cache_estaciones[estacion_id]["timestamp"]
            diferencia = abs(valor_actual - ultimo_valor)
            porcentaje_cambio = diferencia / abs(ultimo_valor) if ultimo_valor != 0 else 1
            tiempo_transcurrido = tiempo_actual - ultimo_tiempo

            if porcentaje_cambio > UMBRAL_CAMBIO:
                print(f"📈 Cambio significativo ({porcentaje_cambio*100:.2f}%).")
                debe_guardarse = True
            elif tiempo_transcurrido > TIEMPO_VIDA:
                print(f"⏱️ Reporte de vida ({int(tiempo_transcurrido)}s).")
                debe_guardarse = True
            else:
                print(f"🚫 Lectura filtrada. Cambio={porcentaje_cambio*100:.2f}%")

        if not debe_guardarse:
            return

        api_payload = {"valor": valor_actual, "estacion_id": estacion_id}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JWT_TOKEN}"
        }

        response = requests.post(
            API_URL,
            json=api_payload,
            headers=headers,
            allow_redirects=False
        )

        if response.status_code in [200, 201]:
            print(f"💾 Lectura {valor_actual} guardada en DB.")
            cache_estaciones[estacion_id] = {
                "valor": valor_actual,
                "timestamp": tiempo_actual
            }
        else:
            print(f"⚠️ Error API ({response.status_code}): {response.text}")

    except KeyError as e:
        print(f"❌ Error de esquema: Falta la llave {e}.")
    except ValueError:
        print("❌ Error de casteo.")
    except Exception as e:
        print(f"❌ Error crítico: {e}")


bridge_client = mqtt.Client()
bridge_client.on_connect = on_connect
bridge_client.on_message = on_message

try:
    print("🚀 Inicializando Bridge SMAT...")
    bridge_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    bridge_client.loop_forever()
except KeyboardInterrupt:
    print("\n🛑 Bridge detenido.")