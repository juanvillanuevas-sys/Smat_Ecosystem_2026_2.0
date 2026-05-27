from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from smat_backend.app import crud
from smat_backend.app.database import engine, get_db
from smat_backend.app.auth import crear_token_acceso, obtener_identidad_actual
from smat_backend.app import models, schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SMAT - Sistema de Monitoreo de Alerta Temprana",
    description="""
API robusta para la gestión y monitoreo de desastres naturales.
Permite la telemetría de sensores en tiempo real y el cálculo de niveles de riesgo.

**Entidades principales:**
* **Estaciones:** Puntos de monitoreo físico.
* **Lecturas:** Datos capturados por sensores.
* **Riesgos:** Análisis de criticidad basado en umbrales.
""",
    version="1.0.0",
    terms_of_service="http://unmsm.edu.pe/terms/",
    contact={
        "name": "Soporte Técnico SMAT - FISI",
        "url": "http://fisi.unmsm.edu.pe",
        "email": "desarrollo.smat@unmsm.edu.pe",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

# ── CORS ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: especificar dominios reales
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Seguridad ────────────────────────────────────

@app.post(
    "/token",
    tags=["Seguridad"],
    summary="Obtener token de acceso",
    description="Genera un JWT válido por 30 minutos para autenticar peticiones protegidas."
)
async def login_para_obtener_token():
    return {
        "access_token": crear_token_acceso({"sub": "admin_smat"}),
        "token_type": "bearer"
    }

# ── Gestión de Infraestructura ───────────────────

@app.post(
    "/estaciones/",
    status_code=201,
    tags=["Gestión de Infraestructura"],
    summary="Registrar una nueva estación de monitoreo",
    description="Inserta una estación física (ej. río, volcán, zona sísmica) en la base de datos relacional.",
    responses={401: {"description": "Token inválido o ausente"}}
)
def crear_estacion(
    estacion: schemas.EstacionCreate,
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_identidad_actual)  # PROTECCIÓN JWT
):
    return crud.crear_estacion(db=db, estacion=estacion)


@app.get(
    "/estaciones/",
    status_code=200,
    tags=["Gestión de Infraestructura"],
    summary="Listar todas las estaciones de monitoreo",
    description="Recupera todas las estaciones registradas en la base de datos.",
    responses={401: {"description": "Token inválido o ausente"}}
)
def obtener_estaciones(
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_identidad_actual)  # PROTECCIÓN JWT igual que el POST
):
    # Consultamos todas las estaciones de la base de datos
    estaciones = db.query(models.EstacionDB).all()
    return estaciones
# ── Telemetría de Sensores ───────────────────────

@app.post(
    "/lecturas/",
    status_code=201,
    tags=["Telemetría de Sensores"],
    summary="Recibir datos de telemetría",
    description="Recibe el valor capturado por un sensor y lo vincula a una estación existente mediante su ID.",
    responses={
        401: {"description": "Token inválido o ausente"},
        404: {"description": "Estación no encontrada"}
    }
)
def registrar_lectura(
    lectura: schemas.LecturaCreate,
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_identidad_actual)  # PROTECCIÓN JWT
):
    # Validación cruzada: verificar existencia de la estación
    estacion_db = db.query(models.EstacionDB).filter(
        models.EstacionDB.id == lectura.estacion_id
    ).first()
    if not estacion_db:
        raise HTTPException(
            status_code=404,
            detail="Error de Integridad: La estación no existe en la base de datos."
        )
    return crud.guardar_lectura(db=db, lectura=lectura)

# ── Reportes Históricos ──────────────────────────

@app.get(
    "/estaciones/{id}/historial",
    tags=["Reportes Históricos"],
    summary="Consultar historial estadístico de una estación",
    description=(
        "Recupera todas las lecturas de una estación e implementa dos cálculos estadísticos:\n\n"
        "- **Conteo**: número total de lecturas (len).\n"
        "- **Promedio**: media aritmética de los valores (sum / len). "
        "Retorna 0.0 si no hay lecturas para evitar división entre cero."
    ),
    responses={404: {"description": "Estación no encontrada"}}
)
def obtener_historial(id: int, db: Session = Depends(get_db)):
    estacion = db.query(models.EstacionDB).filter(
        models.EstacionDB.id == id
    ).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")

    lecturas_filtradas = [
        l.valor for l in db.query(models.LecturaDB).filter(
            models.LecturaDB.estacion_id == id
        ).all()
    ]

    promedio = sum(lecturas_filtradas) / len(lecturas_filtradas) if lecturas_filtradas else 0.0

    return {
        "estacion_id": id,
        "lecturas": lecturas_filtradas,
        "conteo": len(lecturas_filtradas),
        "promedio": round(promedio, 2)
    }

# ── Análisis de Riesgo ───────────────────────────

@app.get(
    "/estaciones/{id}/riesgo",
    tags=["Análisis de Riesgo"],
    summary="Evaluar nivel de peligro actual",
    description="Analiza la última lectura recibida de una estación y determina si el estado es NORMAL, ALERTA o PELIGRO.",
    responses={404: {"description": "Estación no encontrada o sin lecturas"}}
)
def obtener_riesgo(id: int, db: Session = Depends(get_db)):
    estacion = db.query(models.EstacionDB).filter(
        models.EstacionDB.id == id
    ).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")

    ultima = db.query(models.LecturaDB).filter(
        models.LecturaDB.estacion_id == id
    ).order_by(models.LecturaDB.id.desc()).first()

    if not ultima:
        return {"id": id, "nivel": "SIN DATOS", "valor": 0}

    valor = ultima.valor
    if valor > 20.0:
        nivel = "PELIGRO"
    elif valor > 10.0:
        nivel = "ALERTA"
    else:
        nivel = "NORMAL"

    return {"id": id, "valor": valor, "nivel": nivel}

# ── Auditoría ────────────────────────────────────

@app.get(
    "/reportes/criticos",
    tags=["Auditoría"],
    summary="Listar lecturas que superan un umbral de alerta",
    description=(
        "Escanea todas las lecturas y filtra aquellas cuyo valor supere el parámetro **umbral**.\n\n"
        "- Si **umbral** no se envía, se aplica el valor por defecto de **75.0**.\n"
        "- Si se envía (ej. `?umbral=90`), solo se retornan lecturas con valor > umbral.\n\n"
        "Útil para auditorías operativas sin necesidad de consultar cada estación individualmente."
    )
)
def reportes_criticos(
    umbral: Optional[float] = Query(
        default=75.0,
        description="Valor mínimo para considerar una lectura como crítica"
    ),
    db: Session = Depends(get_db)
):
    lecturas = db.query(models.LecturaDB).filter(
        models.LecturaDB.valor > umbral
    ).all()

    return {
        "umbral_aplicado": umbral,
        "total_criticas": len(lecturas),
        "lecturas": [{"id": l.id, "estacion_id": l.estacion_id, "valor": l.valor} for l in lecturas]
    }

@app.get(
    "/estaciones/stats",
    tags=["Auditoría"],
    summary="Resumen ejecutivo del sistema SMAT",
    description=(
        "Genera un resumen ejecutivo del estado global del sistema. Consolida:\n\n"
        "- **total_estaciones**: número de estaciones registradas en la red.\n"
        "- **total_lecturas**: volumen acumulado de telemetría recibida.\n"
        "- **promedio_global**: media aritmética de todas las lecturas del sistema.\n"
        "- **lectura_maxima**: valor más alto registrado e identificación de la estación crítica."
    )
)
def stats_globales(db: Session = Depends(get_db)):
    total_estaciones = db.query(models.EstacionDB).count()
    todas_las_lecturas = db.query(models.LecturaDB).all()

    total_lecturas = len(todas_las_lecturas)
    valores = [l.valor for l in todas_las_lecturas]
    promedio_global = round(sum(valores) / total_lecturas, 2) if total_lecturas > 0 else 0.0

    # Estación con lectura máxima (punto crítico)
    lectura_max = max(todas_las_lecturas, key=lambda l: l.valor) if todas_las_lecturas else None

    return {
        "total_estaciones": total_estaciones,
        "total_lecturas": total_lecturas,
        "promedio_global": promedio_global,
        "lectura_maxima": {
            "valor": lectura_max.valor,
            "estacion_id": lectura_max.estacion_id
        } if lectura_max else None
    }