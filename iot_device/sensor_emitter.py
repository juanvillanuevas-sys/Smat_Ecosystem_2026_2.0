import requests
import time
import random

# CONFIGURACIÓN
API_URL = "http://127.0.0.1:8000/lecturas/"
ESTACION_ID = 1 # ID de la estación registrada en la DB
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl9zbWF0IiwiZXhwIjoxNzc5OTAzMjMxfQ.Jc_Gu9RXTCktZkA2EdwlLWcb1gbcJhoUkQZk_axp4hI" # Reemplaza por el access_token largo de Swagger

def leer_sensor_emulado():
    # Simulamos una lectura de nivel de río (0 a 100 cm)
    return round(random.uniform(10.5, 85.0), 2)

def enviar_telemetria():
    print(f"--- Iniciando Emisor IoT para Estación {ESTACION_ID} ---")
    while True:
        valor = leer_sensor_emulado()
        
        # 1. LÓGICA DE ALARMA: Imprimir advertencia si supera los 70.0 cmpython sensor_emitter.py
        if valor > 70.0:
            print(f"[ALERTA] Umbral de inundación superado: {valor} cm")
        
        payload = {
            "valor": valor,
            "estacion_id": ESTACION_ID
        }
        headers = {
            "Authorization": f"Bearer {TOKEN}"
        }
        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                print(f"[OK] Lectura enviada: {valor} cm")
            else:
                print(f"[ERROR] Código: {response.status_code}")
        except Exception as e:
            print(f"[CRÍTICO] No hay conexión con el servidor: {e}")
            
        # 2. FRECUENCIA DINÁMICA: 2 segundos si es alerta (>70), 10 segundos si es normal
        if valor > 70.0:
            time.sleep(2)
        else:
            time.sleep(10)

if __name__ == "__main__":
    enviar_telemetria()