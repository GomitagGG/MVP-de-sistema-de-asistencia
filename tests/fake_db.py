class FakeQuery:
    """Representa una consulta simulada de Firestore con filtros simples.

    @param parent: Colección o contenedor padre sobre el que se evalúan los documentos.
    @param filtros: Lista de filtros aplicados a la consulta.
    """

    def __init__(self, parent, filtros=None):
        """Inicializa la consulta con su contenedor y filtros.

        @param parent: Colección o contenedor padre sobre el que se evaluarán los documentos.
        @param filtros: Filtros iniciales de la consulta; si es None, se usa una lista vacía.
        """
        self.parent = parent
        self.filtros = filtros or []

    def where(self, filter=None):
        """Agrega un filtro a la consulta.

        @param filter: Instancia de FieldFilter a incorporar a la consulta.
        @return FakeQuery: La misma instancia con el filtro agregado.
        """
        from google.cloud.firestore_v1.base_query import FieldFilter

        if isinstance(filter, FieldFilter):
            self.filtros.append((filter.field_path, filter.op_string, filter.value))
        return self

    def limit(self, n):
        """Establece un límite de resultados en la consulta.

        @param n: Número máximo de resultados a devolver.
        @return FakeQuery: La misma instancia para encadenar llamadas.
        """
        return self

    def get(self):
        """Obtiene los documentos que cumplen los filtros de la consulta.

        @return list[FakeDoc]: Lista de documentos coincidentes.
        """
        docs = []
        for doc_id, datos in self.parent.data.items():
            coincide = True
            for campo, op, valor in self.filtros:
                actual = datos.get(campo)
                if op == "==" and actual != valor:
                    coincide = False
                    break
                if op == ">=" and not (actual >= valor):
                    coincide = False
                    break
                if op == "<=" and not (actual <= valor):
                    coincide = False
                    break
            if coincide:
                docs.append(FakeDoc(doc_id, datos))
        return docs


class FakeDoc:
    """Representa un documento simulado de Firestore.

    @param id: Identificador del documento.
    @param datos: Diccionario con los datos del documento.
    """

    def __init__(self, id, datos):
        """Inicializa el documento con su identificador y contenido.

        @param id: Identificador único del documento.
        @param datos: Datos que almacenará el documento.
        """
        self.id = id
        self.data = datos
        self.exists = True

    def to_dict(self):
        """Devuelve el contenido del documento como diccionario.

        @return dict: Datos del documento.
        """
        return self.data

    def update(self, cambios):
        """Actualiza los datos del documento con un conjunto de cambios.

        @param cambios: Diccionario con los campos a modificar.
        @return None: Modifica el contenido del documento en memoria.
        """
        self.data.update(cambios)


class FakeRef:
    """Representa una referencia simulada a un documento dentro de una colección.

    @param parent: Colección padre que contiene el documento.
    @param id: Identificador del documento referenciado.
    """

    def __init__(self, parent, id):
        """Inicializa la referencia con la colección y el identificador.

        @param parent: Colección que contiene al documento.
        @param id: Identificador del documento asociado.
        """
        self.parent = parent
        self.id = id

    def get(self):
        """Recupera el documento referenciado desde la colección simulada.

        @return FakeDoc: Documento asociado a la referencia.
        """
        return FakeDoc(self.id, self.parent.data.get(self.id, {}))

    def update(self, cambios):
        """Actualiza los datos del documento referenciado si existe.

        @param cambios: Diccionario con los cambios a aplicar.
        @return None: Actualiza los valores del documento en memoria.
        """
        if self.id in self.parent.data:
            self.parent.data[self.id].update(cambios)


class FakeCollection:
    """Simula una colección de Firestore con almacenamiento en memoria.

    @param name: Nombre de la colección.
    @param data: Diccionario inicial de documentos; si es None, se crea vacío.
    """

    def __init__(self, name, data=None):
        """Inicializa la colección con su nombre y datos internos.

        @param name: Nombre identificador de la colección.
        @param data: Datos iniciales de la colección; si es None, se usa un diccionario vacío.
        """
        self.name = name
        self.data = data if data is not None else {}

    def add(self, datos):
        """Agrega un nuevo documento a la colección con un identificador automático.

        @param datos: Diccionario con los datos del nuevo documento.
        @return tuple: Tupla formada por FakeRef y FakeDoc del documento recién creado.
        """
        doc_id = f"auto_{len(self.data) + 1}"
        self.data[doc_id] = datos
        return (FakeRef(self, doc_id), FakeDoc(doc_id, datos))

    def document(self, doc_id):
        """Obtiene una referencia a un documento por su identificador.

        @param doc_id: Identificador del documento solicitado.
        @return FakeRef: Referencia al documento indicado.
        """
        return FakeRef(self, doc_id)

    def where(self, filter=None):
        """Crea una consulta filtrada sobre la colección.

        @param filter: Filtro inicial para la consulta.
        @return FakeQuery: Consulta simulada con el filtro aplicado.
        """
        return FakeQuery(self).where(filter=filter)

    def get(self):
        """Recupera todos los documentos de la colección.

        @return list[FakeDoc]: Lista de documentos contenidos en la colección.
        """
        return [FakeDoc(i, d) for i, d in self.data.items()]


class FakeDB:
    """Simula una base de datos Firestore con colecciones almacenadas en memoria.
    """

    def __init__(self):
        """Inicializa la base de datos con un diccionario de colecciones.

        @return None: Crea el contenedor interno de colecciones.
        """
        self.collections = {}

    def collection(self, nombre):
        """Obtiene una colección por nombre, creando una si no existe.

        @param nombre: Nombre de la colección solicitada.
        @return FakeCollection: Colección asociada al nombre indicado.
        """
        if nombre not in self.collections:
            self.collections[nombre] = FakeCollection(nombre)
        return self.collections[nombre]