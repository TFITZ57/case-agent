from firebase_admin import firestore, credentials, initialize_app, get_app
from dataclasses import dataclass, field, fields
from typing_extensions import Annotated
from assistant import prompts
from langgraph.store.base import BaseStore
from typing import Any, Optional, Dict, List, TypedDict
import logging
import uuid
import os
import time

logger = logging.getLogger(__name__)

class ConfigDict(TypedDict, total=False):
    """Type definition for configuration dictionary"""
    configurable: Dict[str, Any]

@dataclass
class Memory:
    """A class to represent a memory in the database."""
    database: str  # name of the database
    collection: str  # 'users', 'cases', 'messages', or 'caseDetails'
    document_id: str  # UUID or Firebase UID
    data: Dict[str, Any]
    timestamp: float = field(default_factory=lambda: time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "collection": self.collection,
            "document_id": self.document_id,
            "data": self.data,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        return cls(**data)

@dataclass(kw_only=True)
class Configuration:
    case_id: str = field(default_factory=lambda: str(uuid.uuid4()), metadata={"description": "The ID of the case to remember in the conversation."})
    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="gpt-4o",
        metadata={
            "description": "The name of the language model to use for the agent. "
            "Should be in the form: provider/model-name."
        },
    )
    
    @classmethod
    def from_runnable_config(cls, config: Optional[Dict[str, Any]] = None) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        config_dict = {} if config is None else config
        configurable = config_dict.get("configurable", {})
        
        values: Dict[str, Any] = {}
        for f in fields(cls):
            if f.init:
                env_value = os.environ.get(f.name.upper())
                config_value = configurable.get(f.name)
                values[f.name] = env_value if env_value is not None else config_value
        
        return cls(**{k: v for k, v in values.items() if v is not None})


class FireStore(BaseStore):
    def __init__(self, db: Any):
        self.db = db
        self._batch = None

    async def get(self, namespace: tuple[str, str]) -> Optional[Memory]:
        """Get data from Firestore."""
        collection, doc_id = namespace
        doc_ref = self.db.collection(collection).document(doc_id)
        doc = doc_ref.get()
        return Memory.from_dict(doc.to_dict()) if doc.exists else None

    async def set(self, namespace: tuple[str, str], memory: Memory) -> None:
        """Set data in Firestore."""
        collection, doc_id = namespace
        doc_ref = self.db.collection(collection).document(doc_id)
        doc_ref.set(memory.to_dict())
        return None

    async def query(self, collection: str, filters: List[tuple]) -> List[Memory]:
        """Query Firestore with filters."""
        query = self.db.collection(collection)
        for field, op, value in filters:
            query = query.where(field, op, value)
        docs = query.stream()
        return [Memory.from_dict(doc.to_dict()) for doc in docs]

    async def delete(self, namespace: tuple[str, str]) -> None:
        """Delete data from Firestore."""
        doc_ref = self.db.collection(namespace[0]).document(namespace[1])
        doc_ref.delete()  
        return None

    async def batch(self) -> None:
        """Start a new batch operation."""
        self._batch = self.db.batch()

    async def abatch(self) -> None:
        """Start a new batch operation."""
        await self.batch()

    def put(self, namespace: tuple[str, str], key: str, value: Dict[str, Any]) -> None:
        """Put a value into the batch."""
        if self._batch is None:
            raise RuntimeError("No batch operation in progress")
        doc_ref = self.db.collection(namespace[0]).document(key)
        self._batch.set(doc_ref, value)

    async def commit(self) -> None:
        """Commit the current batch operation."""
        if self._batch is not None:
            self._batch.commit()  
            self._batch = None

def get_or_create_firebase_app():
    """Get existing Firebase app or create a new one."""
    try:
        return get_app()
    except ValueError:
        # Get credentials from environment variable
        cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS"))
        return initialize_app(cred, {
            'databaseURL': os.getenv("FIREBASE_DATABASE_URL"),
            'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")
        })

# Initialize Firebase and get Firestore client
firebase_app = get_or_create_firebase_app()
firestore_db = firestore.client()
store = FireStore(firestore_db)

# Export the initialized app and database client
__all__ = ["store", "firebase_app", "firestore_db"]
