class Estacion {
  final int id;
  final String nombre;
  final String ubicacion;
  final String nivelRiesgo;

  Estacion({
    required this.id,
    required this.nombre,
    required this.ubicacion,
    this.nivelRiesgo = 'SIN DATOS',
  });

  factory Estacion.fromJson(Map<String, dynamic> json) {
    return Estacion(
      id: json['id'],
      nombre: json['nombre'],
      ubicacion: json['ubicacion'],
    );
  }

  Estacion copyWith({String? nivelRiesgo}) {
    return Estacion(
      id: id,
      nombre: nombre,
      ubicacion: ubicacion,
      nivelRiesgo: nivelRiesgo ?? this.nivelRiesgo,
    );
  }
}