extends Node2D

# Broker público HiveMQ vía WebSocket (compatible con Godot 4)
const BROKER = "ws://broker.hivemq.com:8000/mqtt"
const TOPIC_BASE = "fisi/smat/estaciones/"

@onready var mqtt = $MQTTClient
@onready var label_estado = $LabelEstado

func _ready():
	label_estado.text = "🔄 Conectando al Broker..."
	print("🚀 Dashboard SMAT iniciando...")

	# Conectar señales del plugin
	mqtt.connected_to_broker.connect(_on_connected)
	mqtt.received_message.connect(_on_msg)
	mqtt.broker_disconnected.connect(_on_disconnected)

	# Conectar al broker
	mqtt.connect_to_broker(BROKER)

func _on_connected():
	label_estado.text = "🟢 Conectado al Broker MQTT"
	print("✅ Conectado al Broker MQTT")

	# Suscribirse al tópico de todas las estaciones
	mqtt.subscribe(TOPIC_BASE + "+")
	print("📡 Suscrito a: ", TOPIC_BASE + "+")

func _on_disconnected():
	label_estado.text = "🔴 Desconectado del Broker"
	print("⚠️ Desconectado del Broker MQTT")

func _on_msg(topic: String, message: String):
	print("📩 Mensaje recibido: ", topic, " -> ", message)

	var data = JSON.parse_string(message)
	if data == null:
		print("❌ Error parseando JSON: ", message)
		return

	if not data.has("valor"):
		print("❌ El mensaje no tiene campo 'valor'")
		return

	# Extraer ID de estación desde el tópico
	# Ejemplo: fisi/smat/estaciones/1 → id = "1"
	var parts = topic.split("/")
	if parts.size() < 4:
		return

	var estacion_id = parts[3]
	var valor = float(data["valor"])

	actualizar_sensor(estacion_id, valor)

func actualizar_sensor(id: String, valor: float):
	# Buscar el nodo con nombre "Estacion_1", "Estacion_2", etc.
	var nodo = get_node_or_null("Estacion_" + id)
	if nodo:
		nodo.actualizar_estado(valor)
	else:
		print("⚠️ No se encontró nodo para estación: ", id)
