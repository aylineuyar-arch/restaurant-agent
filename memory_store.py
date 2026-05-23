import json
import chromadb
from datetime import datetime

_client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=chromadb.Settings(anonymized_telemetry=False)
)
_collection = _client.get_or_create_collection("restaurant_searches")


def search_memory(city: str, cuisine: str) -> list[dict]:
    try:
        results = _collection.query(
            query_texts=[f"{cuisine} restaurants in {city}"],
            n_results=3
        )
        docs  = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        return [{"text": d, "meta": m} for d, m in zip(docs, metas)]
    except Exception:
        return []


def save_to_memory(city: str, cuisine: str, date: str, recommendations: list) -> None:
    doc = f"{cuisine} restaurants in {city} on {date}: {json.dumps(recommendations)}"
    uid = f"{city}_{cuisine}_{date}_{datetime.now().timestamp()}"
    _collection.add(
        documents=[doc],
        ids=[uid],
        metadatas=[{"city": city, "cuisine": cuisine, "date": date}]
    )
