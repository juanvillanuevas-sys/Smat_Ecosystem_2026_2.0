import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/estacion.dart';
import 'auth_service.dart';

class ApiService {
  final String baseUrl = "http://127.0.0.1:8000";
// ── GET estaciones ────────────────────────────
  Future<List<Estacion>> fetchEstaciones() async {
    try {
      final token = await AuthService().getToken();

      // Dejamos la barra al final tal como lo pide tu backend
      final response = await http.get(
        Uri.parse('$baseUrl/estaciones/'), 
        headers: {
          'Content-Type': 'application/json',
          if (token != null) 'Authorization': 'Bearer $token',
        },
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        List jsonResponse = json.decode(response.body);
        return jsonResponse.map((data) => Estacion.fromJson(data)).toList();
      } else {
        throw Exception('Error del servidor: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('No se pudo conectar con SMAT.');
    }
  }

  // ── GET nivel de riesgo ───────────────────────
  Future<String> fetchNivelRiesgo(int id) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/estaciones/$id/riesgo'))
          .timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        return json.decode(response.body)['nivel'] ?? 'SIN DATOS';
      }
      return 'SIN DATOS';
    } catch (e) {
      return 'SIN DATOS';
    }
  }

  // ── POST crear estación ───────────────────────
  Future<bool> crearEstacion(int id, String nombre, String ubicacion) async {
    final token = await AuthService().getToken();
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/estaciones/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({'id': id, 'nombre': nombre, 'ubicacion': ubicacion}),
      );
      if (response.statusCode == 401) throw Exception('TOKEN_EXPIRADO');
      return response.statusCode == 201;
    } catch (e) {
      rethrow;
    }
  }

  // ── PUT editar estación ───────────────────────
  Future<bool> editarEstacion(int id, String nombre, String ubicacion) async {
    final token = await AuthService().getToken();
    final response = await http.put(
      Uri.parse('$baseUrl/estaciones/$id'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({'id': id, 'nombre': nombre, 'ubicacion': ubicacion}),
    );
    return response.statusCode == 200;
  }

  // ── DELETE eliminar estación ──────────────────
  Future<bool> eliminarEstacion(int id) async {
    final token = await AuthService().getToken();
    final response = await http.delete(
      Uri.parse('$baseUrl/estaciones/$id'),
      headers: {'Authorization': 'Bearer $token'},
    );
    return response.statusCode == 200;
  }
}