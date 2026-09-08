class FakeQuery:
    def __init__(self, parent, filtros=None):
        self.parent = parent
        self.filtros = filtros or []

    def where(self, filter=None):
        from google.cloud.firestore_v1.base_query import FieldFilter

        if isinstance(filter, FieldFilter):
            self.filtros.append((filter.field_path, filter.op_string, filter.value))
        return self

    def limit(self, n):
        return self

    def get(self):
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
    def __init__(self, id, datos):
        self.id = id
        self.data = datos
        self.exists = True

    def to_dict(self):
        return self.data

    def update(self, cambios):
        self.data.update(cambios)


class FakeRef:
    def __init__(self, parent, id):
        self.parent = parent
        self.id = id

    def get(self):
        return FakeDoc(self.id, self.parent.data.get(self.id, {}))

    def update(self, cambios):
        if self.id in self.parent.data:
            self.parent.data[self.id].update(cambios)


class FakeCollection:
    def __init__(self, name, data=None):
        self.name = name
        self.data = data if data is not None else {}

    def add(self, datos):
        doc_id = f"auto_{len(self.data) + 1}"
        self.data[doc_id] = datos
        return (FakeRef(self, doc_id), FakeDoc(doc_id, datos))

    def document(self, doc_id):
        return FakeRef(self, doc_id)

    def where(self, filter=None):
        return FakeQuery(self).where(filter=filter)

    def get(self):
        return [FakeDoc(i, d) for i, d in self.data.items()]


class FakeDB:
    def __init__(self):
        self.collections = {}

    def collection(self, nombre):
        if nombre not in self.collections:
            self.collections[nombre] = FakeCollection(nombre)
        return self.collections[nombre]