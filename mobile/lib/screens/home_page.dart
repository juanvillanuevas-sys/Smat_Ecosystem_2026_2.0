import 'package:flutter/material.dart';
import 'dart:async';                          // ← NUEVO
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../models/estacion.dart';
import 'login_screen.dart';
import 'add_estacion_screen.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final ApiService apiService = ApiService();
  List<Estacion> _estaciones = [];
  bool _isLoading = true;
  String? _error;
  Timer? _timer;                              // ← NUEVO

  @override
  void initState() {
    super.initState();
    _cargarEstaciones();
    // Auto-refresh cada 10 segundos para ver datos IoT en tiempo real
    _timer = Timer.periodic(const Duration(seconds: 10), (_) {
      _cargarEstaciones();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();                         // ← NUEVO
    super.dispose();
  }

  Future<void> _cargarEstaciones() async {
    setState(() {
      _isLoading = _estaciones.isEmpty;
      _error = null;
    });
    try {
      final lista = await apiService.fetchEstaciones();
      final conRiesgo = await Future.wait(
        lista.map((est) async {
          final nivel = await apiService.fetchNivelRiesgo(est.id);
          return est.copyWith(nivelRiesgo: nivel);
        }),
      );
      setState(() {
        _estaciones = conRiesgo;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Color _colorPorNivel(String nivel) {
    switch (nivel) {
      case 'PELIGRO': return Colors.red;
      case 'ALERTA':  return Colors.orange;
      case 'NORMAL':  return Colors.green;
      default:        return Colors.grey;
    }
  }

  void _mostrarDialogoEdicion(Estacion estacion) {
    final nombreCtrl = TextEditingController(text: estacion.nombre);
    final ubicacionCtrl = TextEditingController(text: estacion.ubicacion);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Editar Estación'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: nombreCtrl,
                decoration: const InputDecoration(labelText: 'Nombre')),
            TextField(controller: ubicacionCtrl,
                decoration: const InputDecoration(labelText: 'Ubicación')),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () async {
              bool ok = await apiService.editarEstacion(
                  estacion.id, nombreCtrl.text, ubicacionCtrl.text);
              if (ok) {
                Navigator.pop(context);
                _cargarEstaciones();
              }
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }

  void _handleLogout() async {
    _timer?.cancel();
    await AuthService().logout();
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (context) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Estaciones SMAT'),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        actions: [
          // Indicador de auto-refresh
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 16, horizontal: 8),
            child: Text('🔄 Live', style: TextStyle(fontSize: 12)),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: _handleLogout,
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final result = await Navigator.push(context,
              MaterialPageRoute(builder: (context) => AddEstacionScreen()));
          if (result == true) _cargarEstaciones();
        },
        backgroundColor: Colors.teal,
        tooltip: 'Nueva estación',
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.wifi_off, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            const Text('❌ Sin conexión con el servidor',
                style: TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('Verifica que el backend esté corriendo',
                style: TextStyle(color: Colors.grey[600])),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _cargarEstaciones,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      );
    }
    if (_estaciones.isEmpty) {
      return const Center(child: Text('No hay estaciones registradas.'));
    }
    return RefreshIndicator(
      onRefresh: _cargarEstaciones,
      child: ListView.builder(
        itemCount: _estaciones.length,
        itemBuilder: (context, index) {
          final est = _estaciones[index];
          final colorAlerta = _colorPorNivel(est.nivelRiesgo);
          return Dismissible(
            key: Key(est.id.toString()),
            direction: DismissDirection.endToStart,
            background: Container(
              color: Colors.red,
              alignment: Alignment.centerRight,
              padding: const EdgeInsets.only(right: 20),
              child: const Icon(Icons.delete, color: Colors.white),
            ),
            onDismissed: (direction) async {
              bool ok = await apiService.eliminarEstacion(est.id);
              if (ok) {
                ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('${est.nombre} eliminada')));
                _cargarEstaciones();
              }
            },
            child: Card(
              margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: colorAlerta,
                  child: const Icon(Icons.satellite_alt, color: Colors.white),
                ),
                title: Text(est.nombre,
                    style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text('📍 ${est.ubicacion}  •  ${est.nivelRiesgo}'),
                trailing: Text('ID: ${est.id}',
                    style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                onTap: () => _mostrarDialogoEdicion(est),
              ),
            ),
          );
        },
      ),
    );
  }
}