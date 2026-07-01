from sqlalchemy.orm import Session
from . import schemas
from . import models

def crear_estacion(db: Session, estacion: schemas.EstacionCreate):
    nueva = models.EstacionDB(
        id=estacion.id,
        nombre=estacion.nombre,
        ubicacion=estacion.ubicacion
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def guardar_lectura(db: Session, lectura: schemas.LecturaCreate):
    nueva = models.LecturaDB(
        valor=lectura.valor,
        estacion_id=lectura.estacion_id
    )
    db.add(nueva)
    db.commit()
    return nueva