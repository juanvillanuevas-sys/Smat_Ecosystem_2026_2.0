from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ── Helper: obtener token ─────────────────────────
def get_token():
    response = client.post("/token")
    return response.json()["access_token"]

def auth_headers():
    return {"Authorization": f"Bearer {get_token()}"}

# ── Tests ─────────────────────────────────────────

def test_crear_estacion():
    response = client.post(
        "/estaciones/",
        json={"id": 1, "nombre": "Estación Rímac", "ubicacion": "Chosica"},
        headers=auth_headers()
    )
    assert response.status_code == 201

def test_registrar_lectura():
    client.post("/estaciones/", json={"id": 2, "nombre": "Test", "ubicacion": "Lima"}, headers=auth_headers())
    response = client.post(
        "/lecturas/",
        json={"estacion_id": 2, "valor": 12.5},
        headers=auth_headers()
    )
    assert response.status_code == 201
    assert response.json()["status"] == "Lectura guardada en DB"

def test_lectura_sin_token():
    response = client.post("/lecturas/", json={"estacion_id": 1, "valor": 5.0})
    assert response.status_code == 401

def test_riesgo_peligro():
    client.post("/estaciones/", json={"id": 10, "nombre": "Misti", "ubicacion": "Arequipa"}, headers=auth_headers())
    client.post("/lecturas/", json={"estacion_id": 10, "valor": 25.5}, headers=auth_headers())
    response = client.get("/estaciones/10/riesgo")
    assert response.status_code == 200
    assert response.json()["nivel"] == "PELIGRO"

def test_estacion_no_encontrada():
    response = client.get("/estaciones/999/riesgo")
    assert response.status_code == 404
    assert response.json()["detail"] == "Estación no encontrada"

def test_historial_y_promedio():
    client.post("/estaciones/", json={"id": 20, "nombre": "Río Yauli", "ubicacion": "La Oroya"}, headers=auth_headers())
    client.post("/lecturas/", json={"estacion_id": 20, "valor": 10.0}, headers=auth_headers())
    client.post("/lecturas/", json={"estacion_id": 20, "valor": 20.0}, headers=auth_headers())
    client.post("/lecturas/", json={"estacion_id": 20, "valor": 30.0}, headers=auth_headers())
    response = client.get("/estaciones/20/historial")
    assert response.status_code == 200
    assert response.json()["conteo"] == 3
    assert response.json()["promedio"] == 20.0

def test_stats_globales():
    client.post("/estaciones/", json={"id": 30, "nombre": "Stats Test", "ubicacion": "Lima"}, headers=auth_headers())
    client.post("/lecturas/", json={"estacion_id": 30, "valor": 50.0}, headers=auth_headers())
    client.post("/lecturas/", json={"estacion_id": 30, "valor": 100.0}, headers=auth_headers())
    response = client.get("/estaciones/stats")
    assert response.status_code == 200
    assert response.json()["total_estaciones"] >= 1
    assert response.json()["total_lecturas"] >= 2
    assert response.json()["lectura_maxima"]["valor"] >= 100.0