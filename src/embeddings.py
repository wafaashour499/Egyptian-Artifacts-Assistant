import json
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "egyptian_artifacts"

embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def load_data(path="data/egyptian_museum_cairo.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_collection(data):
    seen_ids = set()
    unique_data = []
    for item in data:
        if item["item_id"] not in seen_ids:
            seen_ids.add(item["item_id"])
            unique_data.append(item)

    # قاعدة بيانات دائمة على القرص بدل client في الميموري بيتبني من الصفر كل مرة.
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # لو الكولكشن موجودة أصلاً وعدد القطع فيها زي عدد القطع الحالي، بنستخدمها كما هي
    # وبنوفر إعادة حساب الـ embeddings (اللي بتاخد وقت طويل خصوصاً على أول تشغيل للسيرفر).
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        if collection.count() == len(unique_data):
            return collection, embedding_model
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    documents = [item["document_text"] for item in unique_data]
    embeddings = embedding_model.encode(documents, show_progress_bar=True)

    collection = client.create_collection(name=COLLECTION_NAME)

    collection.add(
        ids=[str(item["item_id"]) for item in unique_data],
        embeddings=embeddings.tolist(),
        documents=documents,
        metadatas=[
            {
                "label": item["label"],
                "image": item.get("image") or "",
                "material": ", ".join(item.get("materials", [])),
                "museum": item.get("museum") or "Egyptian Museum, Cairo",
                "item_id": item.get("item_id") or "",
            }
            for item in unique_data
        ]
    )

    print(f"تم تخزين {collection.count()} قطعة")
    return collection, embedding_model
