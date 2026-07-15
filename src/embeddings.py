import json
import chromadb
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def load_data(path="data/egyptian_museum_cairo.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_collection(data):
    # نعمل deduplication الأول
    seen_ids = set()
    unique_data = []
    for item in data:
        if item["item_id"] not in seen_ids:
            seen_ids.add(item["item_id"])
            unique_data.append(item)

    documents = [item["document_text"] for item in unique_data]
    embeddings = embedding_model.encode(documents, show_progress_bar=True)

    client = chromadb.Client()

    try:
        client.delete_collection(name="egyptian_artifacts")
    except:
        pass

    collection = client.create_collection(name="egyptian_artifacts")

    collection.add(
        ids=[str(item["item_id"]) for item in unique_data],
        embeddings=embeddings.tolist(),
        documents=documents,
        metadatas=[
            {
                "label": item["label"],
                "image": item.get("image") or "",
                "material": ", ".join(item.get("materials", [])),
            }
            for item in unique_data
        ]
    )

    print(f"تم تخزين {collection.count()} قطعة")
    return collection, embedding_model