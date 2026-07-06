"""A minimal, JSON-file-backed stand-in for google.cloud.firestore.Client.

Implements only the subset of the Firestore Python SDK surface that
app/services/*.py actually uses: collection/document navigation, get/set/
update/delete, simple equality/">"/"in" where-filters, order_by, streaming,
collection-group queries, and a (non-concurrent) transaction/@transactional
shim. It exists so the same service functions can run against local dummy
data before pointing at real Firestore — see app/core/db.py for the toggle.
"""

import json
import threading
import uuid
from functools import lru_cache
from pathlib import Path

SUBCOLLECTIONS_KEY = "__subcollections__"
_MISSING = object()


class DocumentSnapshot:
    def __init__(self, doc_id: str, data: dict | None, exists: bool, reference: "DocumentReference"):
        self.id = doc_id
        self.exists = exists
        self.reference = reference
        self._data = data or {}

    def to_dict(self) -> dict | None:
        if not self.exists:
            return None
        return {k: v for k, v in self._data.items() if k != SUBCOLLECTIONS_KEY}


class DocumentReference:
    def __init__(self, store: "FakeClient", path: tuple[str, ...]):
        self._store = store
        self._path = path
        self.id = path[-1]

    @property
    def parent(self) -> "CollectionReference":
        return CollectionReference(self._store, self._path[:-1])

    def collection(self, name: str) -> "CollectionReference":
        return CollectionReference(self._store, self._path + (name,))

    def get(self, transaction=None) -> DocumentSnapshot:
        data = self._store._get_doc(self._path)
        return DocumentSnapshot(self.id, data, data is not None, self)

    def set(self, data: dict) -> None:
        self._store._set_doc(self._path, data)

    def update(self, data: dict) -> None:
        self._store._update_doc(self._path, data)

    def delete(self) -> None:
        self._store._delete_doc(self._path)


class CollectionReference:
    def __init__(self, store: "FakeClient", path: tuple[str, ...]):
        self._store = store
        self._path = path

    @property
    def parent(self) -> DocumentReference | None:
        if len(self._path) <= 1:
            return None
        return DocumentReference(self._store, self._path[:-1])

    def document(self, doc_id: str | None = None) -> DocumentReference:
        if doc_id is None:
            doc_id = uuid.uuid4().hex
        return DocumentReference(self._store, self._path + (doc_id,))

    def where(self, filter) -> "Query":
        return Query(self._store, self._path, collection_group=False).where(filter=filter)

    def order_by(self, field: str, direction: str = "ASCENDING") -> "Query":
        return Query(self._store, self._path, collection_group=False).order_by(field, direction=direction)

    def stream(self):
        return Query(self._store, self._path, collection_group=False).stream()


class Query:
    def __init__(self, store: "FakeClient", path, collection_group: bool):
        self._store = store
        self._path = path
        self._collection_group = collection_group
        self._filters: list = []
        self._order: tuple[str, str] | None = None

    def where(self, filter) -> "Query":
        q = Query(self._store, self._path, self._collection_group)
        q._filters = [*self._filters, filter]
        q._order = self._order
        return q

    def order_by(self, field: str, direction: str = "ASCENDING") -> "Query":
        q = Query(self._store, self._path, self._collection_group)
        q._filters = list(self._filters)
        q._order = (field, direction)
        return q

    def _matches(self, filter, data: dict) -> bool:
        actual = data.get(filter.field_path, _MISSING)
        if filter.op_string == "==":
            return actual == filter.value
        if filter.op_string == ">":
            return actual is not _MISSING and actual is not None and actual > filter.value
        if filter.op_string == "in":
            return actual in filter.value
        raise NotImplementedError(f"Unsupported filter op: {filter.op_string}")

    def stream(self):
        if self._collection_group:
            hits = self._store._collect_group(self._path)
        else:
            hits = self._store._collect_collection(self._path)

        results = [(path, data) for path, data in hits if all(self._matches(f, data) for f in self._filters)]

        if self._order:
            field, direction = self._order
            results.sort(key=lambda item: item[1].get(field), reverse=(direction == "DESCENDING"))

        for path, data in results:
            yield DocumentSnapshot(path[-1], data, True, DocumentReference(self._store, path))


class Transaction:
    def __init__(self, store: "FakeClient"):
        self._store = store

    def update(self, ref: DocumentReference, data: dict) -> None:
        ref.update(data)

    def set(self, ref: DocumentReference, data: dict) -> None:
        ref.set(data)


def transactional(func):
    def wrapper(transaction: Transaction, *args, **kwargs):
        return func(transaction, *args, **kwargs)

    return wrapper


class FieldFilter:
    def __init__(self, field_path: str, op_string: str, value):
        self.field_path = field_path
        self.op_string = op_string
        self.value = value


class FakeClient:
    def __init__(self, json_path: str):
        self._path = Path(json_path)
        self._lock = threading.Lock()
        self._root: dict = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            self._root = json.loads(self._path.read_text(encoding="utf-8") or "{}")
        else:
            self._root = {}

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._root, indent=2), encoding="utf-8")

    def reset(self) -> None:
        with self._lock:
            self._root = {}
            self._persist()

    def collection(self, name: str) -> CollectionReference:
        return CollectionReference(self, (name,))

    def collection_group(self, name: str) -> Query:
        return Query(self, name, collection_group=True)

    def transaction(self) -> Transaction:
        return Transaction(self)

    def _resolve_container(self, path: tuple[str, ...]) -> dict:
        """Given a path ending in a collection name, return the {docId: docData} dict for it."""
        container = self._root
        i = 0
        while i < len(path) - 1:
            coll_name, doc_id = path[i], path[i + 1]
            container = container.setdefault(coll_name, {})
            doc = container.setdefault(doc_id, {})
            container = doc.setdefault(SUBCOLLECTIONS_KEY, {})
            i += 2
        return container.setdefault(path[-1], {})

    def _get_doc(self, path: tuple[str, ...]) -> dict | None:
        with self._lock:
            container = self._resolve_container(path[:-1])
            doc = container.get(path[-1])
            return dict(doc) if doc is not None else None

    def _set_doc(self, path: tuple[str, ...], data: dict) -> None:
        with self._lock:
            container = self._resolve_container(path[:-1])
            existing = container.get(path[-1], {})
            new_doc = dict(data)
            if SUBCOLLECTIONS_KEY in existing:
                new_doc[SUBCOLLECTIONS_KEY] = existing[SUBCOLLECTIONS_KEY]
            container[path[-1]] = new_doc
            self._persist()

    def _update_doc(self, path: tuple[str, ...], data: dict) -> None:
        with self._lock:
            container = self._resolve_container(path[:-1])
            doc = container.setdefault(path[-1], {})
            for key, value in data.items():
                if "." in key:
                    parts = key.split(".")
                    target = doc
                    for part in parts[:-1]:
                        target = target.setdefault(part, {})
                    target[parts[-1]] = value
                else:
                    doc[key] = value
            self._persist()

    def _delete_doc(self, path: tuple[str, ...]) -> None:
        with self._lock:
            container = self._resolve_container(path[:-1])
            container.pop(path[-1], None)
            self._persist()

    def _collect_collection(self, path: tuple[str, ...]):
        with self._lock:
            container = self._resolve_container(path)
            return [(path + (doc_id,), dict(doc)) for doc_id, doc in container.items()]

    def _collect_group(self, name: str):
        with self._lock:
            results = []
            self._walk(self._root, name, (), results)
            return results

    def _walk(self, node: dict, name: str, prefix: tuple[str, ...], results: list) -> None:
        for coll_name, docs in node.items():
            if coll_name == SUBCOLLECTIONS_KEY:
                continue
            coll_path = prefix + (coll_name,)
            for doc_id, doc_data in docs.items():
                doc_path = coll_path + (doc_id,)
                if coll_name == name:
                    results.append((doc_path, dict(doc_data)))
                subcols = doc_data.get(SUBCOLLECTIONS_KEY)
                if subcols:
                    self._walk(subcols, name, doc_path, results)


@lru_cache
def _client_for_path(json_path: str) -> FakeClient:
    return FakeClient(json_path)


def get_db() -> FakeClient:
    from app.core.config import get_settings

    return _client_for_path(get_settings().local_data_path)
