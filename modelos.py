import os
import sys
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter


def ruta_relativa(ruta):
    """Resuelve la ruta absoluta de un archivo dentro del proyecto.

    @param ruta: Ruta relativa del archivo a localizar.
    @return str: Ruta completa del recurso según el entorno de ejecución.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, ruta)


def get_db():
    """Obtiene la instancia de la base de datos Firestore configurada.

    @return firestore.Client: Cliente de Firestore inicializado con las credenciales del proyecto.
    """
    if not firebase_admin._apps:
        key_file = "config/firebase-key.json"
        if not os.path.exists(ruta_relativa(key_file)):
            key_file = "config/registro-asistencia-bfe64-firebase-adminsdk-fbsvc-1d738c49d5.json"
        cred = credentials.Certificate(ruta_relativa(key_file))
        firebase_admin.initialize_app(cred)
    return firestore.client()


FERIADOS = frozenset(("2026-09-17", "2026-09-18"))


class Usuario:
    """Representa un usuario del sistema de asistencia.

    @param documento: Diccionario con los datos del usuario a inicializar.
    """

    def __init__(self, documento=None):
        """Inicializa los atributos del usuario con los datos recibidos.

        @param documento: Diccionario con información del usuario.
        """
        documento = documento or {}
        self.usuario = documento.get("usuario", "")
        self.correo = documento.get("correo", "")
        self.clave = documento.get("clave", "")
        self.rol = documento.get("rol", "")
        self.nombre = documento.get("nombre", "")

    def to_dict(self):
        """Convierte el usuario en un diccionario serializable.

        @return dict: Datos del usuario listos para guardar en Firestore.
        """
        return {
            "usuario": self.usuario,
            "correo": self.correo,
            "clave": self.clave,
            "rol": self.rol,
            "nombre": self.nombre,
        }

    @classmethod
    def buscar_por_identificador(cls, db, identificador):
        """Busca un usuario por nombre de usuario o correo electrónico.

        @param db: Cliente de Firestore.
        @param identificador: Valor a buscar como usuario o correo.
        @return dict | None: Documento del usuario encontrado o None si no existe.
        """
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
        """Valida que una clave coincida con la clave del usuario.

        @param doc: Documento del usuario a validar.
        @param clave: Contraseña a comprobar.
        @return bool: True si la clave coincide, False en caso contrario.
        """
        return doc is not None and doc.get("clave") == clave


class Marcacion:
    """Representa una marcación de entrada o salida de un usuario."""

    HORA_ENTRADA_LIMITE = "09:30"
    HORA_SALIDA_LIMITE = "17:30"
    ENTRADA = "entrada"
    SALIDA = "salida"

    def __init__(self, usuario="", correo="", accion="", fecha="", hora="", timestamp=None):
        """Inicializa una marcación con sus datos básicos.

        @param usuario: Nombre de usuario que realiza la marcación.
        @param correo: Correo del usuario.
        @param accion: Tipo de acción, entrada o salida.
        @param fecha: Fecha de la marcación.
        @param hora: Hora de la marcación.
        @param timestamp: Fecha y hora exacta del evento.
        """
        self.usuario = usuario
        self.correo = correo
        self.accion = accion
        self.fecha = fecha
        self.hora = hora
        self.timestamp = timestamp or datetime.now()

    @staticmethod
    def hoy():
        """Devuelve la fecha actual en formato ISO.

        @return str: Fecha del día actual en formato YYYY-MM-DD.
        """
        return datetime.now().strftime("%Y-%m-%d")

    @classmethod
    def ahora(cls, usuario, correo="", accion=ENTRADA):
        """Crea una marcación con la fecha y hora actuales.

        @param cls: Clase Marcacion.
        @param usuario: Nombre del usuario.
        @param correo: Correo del usuario.
        @param accion: Tipo de acción a registrar.
        @return Marcacion: Instancia de marca con el timestamp actual.
        """
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
        """Determina si la marcación de entrada está fuera del horario permitido.

        @return bool: True si la entrada es tardía, False en caso contrario.
        """
        return self.accion == self.ENTRADA and self.hora[:5] > self.HORA_ENTRADA_LIMITE

    def es_salida_anticipada(self):
        """Determina si la salida se registró antes del horario permitido.

        @return bool: True si la salida fue anticipada, False en caso contrario.
        """
        return self.accion == self.SALIDA and self.hora[:5] < self.HORA_SALIDA_LIMITE

    def guardar(self, db, atrasado=False, salida_anticipada=False):
        """Guarda la marcación en la colección de marcaciones de Firestore.

        @param db: Cliente de Firestore.
        @param atrasado: Indicador si la entrada está atrasada.
        @param salida_anticipada: Indicador si la salida fue anticipada.
        @return str: Identificador del documento creado.
        """
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
        """Busca una marcación por usuario, fecha y tipo de acción.

        @param db: Cliente de Firestore.
        @param identificador: Usuario a filtrar.
        @param fecha: Fecha específica a consultar.
        @param accion: Tipo de acción a consultar.
        @return dict | None: Marcación encontrada o None si no existe.
        """
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
    """Representa una alerta generada por un evento de asistencia."""

    TIPO_ATRASO = "atraso"
    TIPO_SALIDA_ANTICIPADA = "salida_anticipada"
    TIPO_INASISTENCIA = "inasistencia"
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_LEIDA = "leida"

    def __init__(self, tipo="", usuario="", fecha="", hora="", estado=ESTADO_PENDIENTE,
                 timestamp=None, _id=None):
        """Inicializa una alerta con el tipo, usuario y estado dados.

        @param tipo: Tipo de alerta que se está creando.
        @param usuario: Usuario al cual pertenece la alerta.
        @param fecha: Fecha de la alerta.
        @param hora: Hora de la alerta.
        @param estado: Estado inicial de la alerta.
        @param timestamp: Timestamp de la ocurrencia.
        @param _id: Identificador del documento en Firestore.
        """
        self.tipo = tipo
        self.usuario = usuario
        self.fecha = fecha
        self.hora = hora
        self.estado = estado
        self.timestamp = timestamp
        self._id = _id

    def to_dict(self):
        """Convierte la alerta a un diccionario serializable.

        @return dict: Datos de la alerta listos para guardarse.
        """
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
        """Comprueba si ya existe una alerta igual para el mismo usuario y fecha.

        @param db: Cliente de Firestore.
        @param tipo: Tipo de alerta a revisar.
        @param usuario: Usuario asociado a la alerta.
        @param fecha: Fecha de la alerta.
        @return bool: True si ya existe una alerta duplicada.
        """
        docs = db.collection("alertas") \
            .where(filter=FieldFilter("fecha", "==", fecha)).get()
        for doc in docs:
            datos = doc.to_dict()
            if datos.get("tipo") == tipo and datos.get("usuario") == usuario:
                return True
        return False

    @classmethod
    def crear(cls, db, tipo, usuario, fecha, hora=""):
        """Crea una alerta si todavía no existe para ese usuario y fecha.

        @param cls: Clase Alerta.
        @param db: Cliente de Firestore.
        @param tipo: Tipo de alerta a crear.
        @param usuario: Usuario afectado.
        @param fecha: Fecha de la alerta.
        @param hora: Hora de la alerta.
        @return Alerta | None: Instancia creada o None si ya existe.
        """
        if cls.ya_existe(db, tipo, usuario, fecha):
            return None
        alerta = cls(tipo=tipo, usuario=usuario, fecha=fecha, hora=hora)
        _, ref = db.collection("alertas").add(alerta.to_dict())
        alerta._id = ref.id
        return alerta

    @staticmethod
    def marcar_leida(db, alerta_id):
        """Marca una alerta como leída en la base de datos.

        @param db: Cliente de Firestore.
        @param alerta_id: Identificador de la alerta a actualizar.
        """
        db.collection("alertas").document(alerta_id).update({"estado": "leida"})

    @staticmethod
    def listar(db, estado=None, fecha_inicio=None, fecha_fin=None):
        """Lista alertas según filtros opcionales de estado y rango de fechas.

        @param db: Cliente de Firestore.
        @param estado: Estado a filtrar, por ejemplo pendiente o leida.
        @param fecha_inicio: Fecha inicial del rango.
        @param fecha_fin: Fecha final del rango.
        @return list: Lista de alertas ordenadas por fecha y hora.
        """
        col = db.collection("alertas")
        consulta = col
        if fecha_inicio:
            consulta = consulta.where(
                filter=FieldFilter("fecha", ">=", fecha_inicio))
        if fecha_fin:
            consulta = consulta.where(
                filter=FieldFilter("fecha", "<=", fecha_fin))
        docs = consulta.get()
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