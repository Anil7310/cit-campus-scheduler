import logging
import certifi
import copy
from typing import Optional, Dict, Any, List
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, PyMongoError
from app.config import settings

logger = logging.getLogger("cit_scheduler.db")

class DatabaseManager:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.is_connected = False
        self._in_memory_store: Dict[str, List[Dict[str, Any]]] = {
            "users": [],
            "datasets": [],
            "timetables": [],
            "exam_schedules": [],
            "bookings": [],
            "proposals": [],
            "jobs": [],
            "priority_config": [],
            "audit_logs": [],
            "explanations_cache": [],
            "system_state": [{"_id": "state", "published_version": None}]
        }

    def connect(self):
        if not settings.MONGODB_URI:
            logger.warning("MONGODB_URI not provided; falling back to memory-backed store for local development/testing.")
            self.is_connected = True
            return

        try:
            kwargs = {
                "serverSelectionTimeoutMS": 8000,
            }
            # Add certifi tlsCAFile if connecting to mongodb+srv or ssl
            if "mongodb+srv://" in settings.MONGODB_URI or "ssl=true" in settings.MONGODB_URI.lower():
                kwargs["tlsCAFile"] = certifi.where()

            self.client = MongoClient(settings.MONGODB_URI, **kwargs)
            # Ping
            self.client.admin.command('ping')
            self.db = self.client[settings.MONGODB_DB]
            self.is_connected = True
            logger.info(f"Connected to MongoDB Atlas: {settings.MONGODB_DB}")
            self.init_indexes()
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}. Running with offline/fallback store.")
            self.is_connected = False

    def init_indexes(self):
        if not self.is_connected or self.db is None:
            return

        try:
            self.db.users.create_index([("email", ASCENDING)], unique=True)
            self.db.datasets.create_index([("is_active", ASCENDING)])
            self.db.timetables.create_index([("version", ASCENDING)], unique=True)
            self.db.exam_schedules.create_index([("version", ASCENDING)])
            self.db.bookings.create_index([("requester_id", ASCENDING)])
            self.db.bookings.create_index([("status", ASCENDING)])
            self.db.proposals.create_index([("status", ASCENDING)])
            self.db.jobs.create_index([("status", ASCENDING)])
            self.db.jobs.create_index([("created_at", ASCENDING)])
            self.db.audit_logs.create_index([("ts", ASCENDING)])
            self.db.explanations_cache.create_index([("key", ASCENDING)], unique=True)
            logger.info("MongoDB indexes verified.")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    def get_collection(self, name: str):
        if self.is_connected and self.db is not None:
            return self.db[name]
        return InMemoryCollection(self._in_memory_store, name)

# Lightweight MongoDB-compatible Collection wrapper for in-memory execution
class InMemoryCollection:
    def __init__(self, store: Dict[str, List[Dict[str, Any]]], name: str):
        self.store = store
        self.name = name
        if name not in self.store:
            self.store[name] = []

    def _matches(self, doc: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        if not filter_dict:
            return True
        for k, v in filter_dict.items():
            if k == "$or" and isinstance(v, list):
                if not any(self._matches(doc, cond) for cond in v):
                    return False
                continue
            if k.startswith("$"):
                continue
            doc_val = doc.get(k)
            if isinstance(v, dict):
                # Simple operators
                if "$in" in v and doc_val not in v["$in"]:
                    return False
                if "$ne" in v and doc_val == v["$ne"]:
                    return False
                if "$gt" in v and not (doc_val is not None and doc_val > v["$gt"]):
                    return False
                if "$gte" in v and not (doc_val is not None and doc_val >= v["$gte"]):
                    return False
            else:
                if doc_val != v:
                    return False
        return True

    def find_one(self, filter_dict: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        filter_dict = filter_dict or {}
        for doc in self.store[self.name]:
            if self._matches(doc, filter_dict):
                return copy.deepcopy(doc)
        return None

    def find(self, filter_dict: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None):
        filter_dict = filter_dict or {}
        results = [copy.deepcopy(doc) for doc in self.store[self.name] if self._matches(doc, filter_dict)]
        return InMemoryCursor(results)

    def insert_one(self, doc: Dict[str, Any]):
        doc_copy = copy.deepcopy(doc)
        if "_id" not in doc_copy:
            doc_copy["_id"] = str(len(self.store[self.name]) + 1)
        self.store[self.name].append(doc_copy)
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertResult(doc_copy["_id"])

    def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any], upsert: bool = False):
        for doc in self.store[self.name]:
            if self._matches(doc, filter_dict):
                if "$set" in update_dict:
                    for k, v in update_dict["$set"].items():
                        doc[k] = copy.deepcopy(v)
                if "$unset" in update_dict:
                    for k in update_dict["$unset"]:
                        doc.pop(k, None)
                class UpdateResult:
                    matched_count = 1
                    modified_count = 1
                return UpdateResult()
        if upsert:
            new_doc = copy.deepcopy(filter_dict)
            if "$set" in update_dict:
                new_doc.update(copy.deepcopy(update_dict["$set"]))
            self.insert_one(new_doc)
            class UpdateResultUpsert:
                matched_count = 0
                modified_count = 1
            return UpdateResultUpsert()
        class UpdateResultNone:
            matched_count = 0
            modified_count = 0
        return UpdateResultNone()

    def find_one_and_update(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any], return_document=False):
        for doc in self.store[self.name]:
            if self._matches(doc, filter_dict):
                old_doc = copy.deepcopy(doc)
                if "$set" in update_dict:
                    for k, v in update_dict["$set"].items():
                        doc[k] = copy.deepcopy(v)
                return copy.deepcopy(doc) if return_document else old_doc
        return None

    def delete_one(self, filter_dict: Dict[str, Any]):
        for i, doc in enumerate(self.store[self.name]):
            if self._matches(doc, filter_dict):
                del self.store[self.name][i]
                break

    def delete_many(self, filter_dict: Dict[str, Any]):
        self.store[self.name] = [d for d in self.store[self.name] if not self._matches(d, filter_dict)]

    def count_documents(self, filter_dict: Dict[str, Any]) -> int:
        return sum(1 for doc in self.store[self.name] if self._matches(doc, filter_dict))

    def create_index(self, *args, **kwargs):
        pass

class InMemoryCursor:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self._sort_key = None
        self._sort_desc = False
        self._limit = None
        self._skip = 0

    def sort(self, key_or_list, direction=1):
        if isinstance(key_or_list, list) and key_or_list:
            k, d = key_or_list[0]
            self.data.sort(key=lambda x: x.get(k) or "", reverse=(d < 0))
        elif isinstance(key_or_list, str):
            self.data.sort(key=lambda x: x.get(key_or_list) or "", reverse=(direction < 0))
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def skip(self, n: int):
        self._skip = n
        return self

    def __iter__(self):
        items = self.data[self._skip:]
        if self._limit is not None:
            items = items[:self._limit]
        return iter(items)

    def to_list(self, length: Optional[int] = None):
        items = list(self)
        if length is not None:
            return items[:length]
        return items

db_manager = DatabaseManager()

def get_db():
    return db_manager
