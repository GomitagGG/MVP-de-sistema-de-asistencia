import os
import sys
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter


def ruta_relativa(ruta):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, ruta)


def get_db():
    if not firebase_admin._apps:
        key_file = "config/firebase-key.json"
        if not os.path.exists(ruta_relativa(key_file)):
            key_file = "config/registro-asistencia-bfe64-firebase-adminsdk-fbsvc-236f010224.json"
        cred = credentials.Certificate(ruta_relativa(key_file))
        firebase_admin.initialize_app(cred)
    return firestore.client()


class Usuario:

    def __init__(self, documento=None):
        documento = documento or {}
        self.usuario = documento.get("usuario", "")
        self.correo = documento.get("correo", "")
        self.clave = documento.get("clave", "")
        self.rol = documento.get("rol", "")
        self.nombre = documento.get("nombre", "")

    def to_dict(self):
        return {
            "usuario": self.usuario,
            "correo": self.correo,
            "clave": self.clave,
            "rol": self.rol,
            "nombre": self.nombre,
        }

    @classmethod
    def buscar_por_identificador(cls, db, identificador):
        identificador = (identificador or "").strip()
        if not identificador:
            return None
        docs = db.collection("usuarios").where(filter=FieldFilter("usuario", "==", identificador)).limit(1).get()
        if len(docs) == 0:
            docs = db.collection("usuarios").where(filter=FieldFilter("correo", "==", identificador)).limit(1).get()
        if len(docs) == 0:
            return None
        doc = docs[0].to_dict()
        doc["_id"] = docs[0].id
        return doc

    @staticmethod
    def clave_valida(doc, clave):
        return doc is not None and doc.get("clave") == clave


class Marcacion:
    HORA_ENTRADA_LIMITE = "09:30"
    HORA_SALIDA_LIMITE = "17:30"
    ENTRADA = "entrada"
    SALIDA = "salida"

    def __init__(self, usuario="", correo="", accion="", fecha="", hora="", timestamp=None):
        self.usuario = usuario
        self.correo = correo
        self.accion = accion
        self.fecha = fecha
        self.hora = hora
        self.timestamp = timestamp or datetime.now()

    @staticmethod
    def hoy():
        return datetime.now().strftime("%Y-%m-%d")

    @classmethod
    def ahora(cls, usuario, correo="", accion=ENTRADA):
        momento = datetime.now()
        return cls(
            usuario=usuario,
            correo=correo,
            accion=accion,
            fecha=momento.strftime("%Y-%m-%d"),
            hora=momento.strftime("%H:%M:%S"),
            timestamp=momento,
        )

    def es_entrada_atrasada(self):
        return self.accion == self.ENTRADA and self.hora[:5] > self.HORA_ENTRADA_LIMITE

    def es_salida_anticipada(self):
        return self.accion == self.SALIDA and self.hora[:5] < self.HORA_SALIDA_LIMITE

    def guardar(self, db, atrasado=False, salida_anticipada=False):
        _, ref = db.collection("marcaciones").add({
            "usuario": self.usuario,
            "correo": self.correo,
            "tipo": self.accion,
            "fecha": self.fecha,
            "hora": self.hora,
            "timestamp": self.timestamp,
            "atrasado": atrasado,
            "salida_anticipada": salida_anticipada,
        })
        return ref.id

    @staticmethod
    def buscar(db, identificador, fecha=None, accion=None):
        fecha = fecha or Marcacion.hoy()
        identificador = (identificador or "").strip()
        docs = db.collection("marcaciones").where(filter=FieldFilter("fecha", "==", fecha)).get()
        for doc in docs:
            datos = doc.to_dict()
            if identificador and datos.get("usuario") != identificador:
                continue
            if accion and datos.get("tipo") != accion:
                continue
            return datos
        return None


class Alerta:
    TIPO_ATRASO = "atraso"
    TIPO_SALIDA_ANTICIPADA = "salida_anticipada"
    TIPO_INASISTENCIA = "inasistencia"
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_LEIDA = "leida"

    def __init__(self, tipo="", usuario="", fecha="", hora="", estado=ESTADO_PENDIENTE,
                 timestamp=None, _id=None):
        self.tipo = tipo
        self.usuario = usuario
        self.fecha = fecha
        self.hora = hora
        self.estado = estado
        self.timestamp = timestamp
        self._id = _id

    def to_dict(self):
        return {
            "tipo": self.tipo,
            "usuario": self.usuario,
            "fecha": self.fecha,
            "hora": self.hora,
            "estado": self.estado,
            "timestamp": self.timestamp or datetime.now(),
        }

    @staticmethod
    def ya_existe(db, tipo, usuario, fecha):
        docs = db.collection("alertas") \
            .where(filter=FieldFilter("fecha", "==", fecha)).get()
        for doc in docs:
            datos = doc.to_dict()
            if datos.get("tipo") == tipo and datos.get("usuario") == usuario:
                return True
        return False

    @classmethod
    def crear(cls, db, tipo, usuario, fecha, hora=""):
        if cls.ya_existe(db, tipo, usuario, fecha):
            return None
        alerta = cls(tipo=tipo, usuario=usuario, fecha=fecha, hora=hora)
        _, ref = db.collection("alertas").add(alerta.to_dict())
        alerta._id = ref.id
        return alerta

    @staticmethod
    def marcar_leida(db, alerta_id):
        db.collection("alertas").document(alerta_id).update({"estado": "leida"})

    @staticmethod
    def listar(db, estado=None, fecha_inicio=None, fecha_fin=None):
        col = db.collection("alertas")
        docs = col.get()
        resultados = []
        for doc in docs:
            datos = doc.to_dict()
            if estado and datos.get("estado") != estado:
                continue
            if fecha_inicio and datos.get("fecha") < fecha_inicio:
                continue
            if fecha_fin and datos.get("fecha") > fecha_fin:
                continue
            datos["_id"] = doc.id
            resultados.append(datos)
        resultados.sort(key=lambda a: (a.get("fecha", ""), a.get("hora", "")))
        return resultados