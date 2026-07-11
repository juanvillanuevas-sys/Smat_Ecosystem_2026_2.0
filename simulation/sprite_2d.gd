extends Node2D

# Variables exportables para configurar desde el editor
@export var estacion_id: int = 1
@export var nombre_estacion: String = "Estación 1"

@onready var label_valor = $Label
@onready var label_nombre = $LabelNombre
@onready var sprite = $Sprite2D

func _ready():
	label_nombre.text = nombre_estacion
	label_valor.text = "-- cm"
	sprite.modulate = Color.GRAY

func actualizar_estado(valor: float):
	label_valor.text = str(valor) + " cm"

	# Lógica de colores de alerta temprana
	if valor > 70:
		sprite.modulate = Color.RED
		print("🔴 PELIGRO en ", nombre_estacion, ": ", valor, " cm")
	elif valor > 50:
		sprite.modulate = Color.ORANGE
		print("🟠 ALERTA en ", nombre_estacion, ": ", valor, " cm")
	else:
		sprite.modulate = Color.GREEN
		print("🟢 NORMAL en ", nombre_estacion, ": ", valor, " cm")
