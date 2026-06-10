import paho.mqtt.client as mqtt
import requests
import json
import sys
import time

# CONFIGURACIÓN DEL ENTORNO SMAT
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "fisi/smat/estaciones/+/lecturas"  # El '+' es un wildcard para el ID de la estación

API_URL = "http://localhost:8000/lecturas/"

# Token JWT generado previamente desde Swagger o la App móvil para el usuario administrador
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl9zbWF0IiwiZXhwIjoxNzgxMTA4ODU0fQ.kMq-b8U3_H1p5LaZoeKLMnoULRCAnXzGfuJJvhNS9Qg"
cache_estaciones = {} #Ultimo valor persistido
#Configuracion el filtro
UMBRAL_CAMBIO = 0.05
TIEMPO_VIDA = 60

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("🟢 Conectado exitosamente al Broker MQTT")

        # Suscribirse al tópico global de lecturas de estaciones
        client.subscribe(MQTT_TOPIC)

        print(f"📡 Escuchando transmisiones en el tópico: {MQTT_TOPIC}")
    else:
        print(f"🔴 Error de conexión al Broker. Código de retorno: {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    try:
        # 1. Decodificar el payload binario de MQTT a JSON string
        payload_raw = msg.payload.decode("utf-8")
        data_json = json.loads(payload_raw)

        # 2. Extraer ID de estación
        topic_parts = msg.topic.split('/')
        estacion_id = int(topic_parts[3])

        valor_actual = float(data_json["valor"])

        print(
            f"📩 Telemetría recibida de Estación "
            f"[{estacion_id}]: {valor_actual}"
        )

        tiempo_actual = time.time()

        # Primera lectura de la estación
        if estacion_id not in cache_estaciones:
            print(
                f"🆕 Primera lectura de estación "
                f"{estacion_id}. Se almacenará."
            )
            debe_guardarse = True
        else:
            ultimo_valor = cache_estaciones[estacion_id]["valor"]
            ultimo_tiempo = cache_estaciones[estacion_id]["timestamp"]

            diferencia = abs(valor_actual - ultimo_valor)
            if ultimo_valor != 0:
                porcentaje_cambio = diferencia / abs(ultimo_valor)
            else:
                porcentaje_cambio = 1
            tiempo_transcurrido = tiempo_actual - ultimo_tiempo
            # Regla 1: Cambio mayor al 5%
            if porcentaje_cambio > UMBRAL_CAMBIO:
                print(
                    f"📈 Cambio significativo detectado "
                    f"({porcentaje_cambio*100:.2f}%)."
                )
                debe_guardarse = True
            # Regla 2: Reporte mínimo de vida cada 60 segundos
            elif tiempo_transcurrido > TIEMPO_VIDA:
                print(
                    f"⏱️ Reporte de vida "
                    f"({int(tiempo_transcurrido)} s)."
                )
                debe_guardarse = True

            else:
                print(
                    f"🚫 Lectura filtrada. "
                    f"Cambio={porcentaje_cambio*100:.2f}%"
                )
                debe_guardarse = False

        if not debe_guardarse:
            return

        # 3. Payload para FastAPI
        api_payload = {
            "valor": valor_actual,
            "estacion_id": estacion_id
        }

        # 4. Headers HTTP
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JWT_TOKEN}"
        }

        response = requests.post(
            API_URL,
            json=api_payload,
            headers=headers
        )

        if response.status_code in [200, 201]:

            print(
                f"💾 [DB Sincronizada] "
                f"Lectura de {valor_actual} guardada."
            )

            cache_estaciones[estacion_id] = {
                "valor": valor_actual,
                "timestamp": tiempo_actual
            }

        else:

            print(
                f"⚠️ [Fallo de Ingesta] "
                f"Código: {response.status_code} "
                f"- {response.text}"
            )

    except KeyError as e:
        print(f"❌ Error de esquema: Falta la llave {e}.")
    except ValueError:
        print("❌ Error de casteo.")
    except Exception as e:
        print(f"❌ Error crítico en el Bridge: {e}")

# Inicialización del cliente de red MQTT
bridge_client = mqtt.Client()
bridge_client.on_connect = on_connect
bridge_client.on_message = on_message

try:
    print("🚀 Inicializando el Bridge de Acoplamiento SMAT...")
    bridge_client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # Mantener el hilo escuchando activamente de forma síncrona
    bridge_client.loop_forever()

except KeyboardInterrupt:
    print("\n🛑 Bridge detenido por el administrador.") 