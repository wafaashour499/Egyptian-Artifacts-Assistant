import hashlib
import json
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "egyptian_artifacts"

embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def load_data(path="data/egyptian_museum_cairo.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _data_fingerprint(unique_data):
    """
    بصمة (hash) لمحتوى البيانات فعلياً، مش بس عددها. كده لو حد عدّل قطعة موجودة
    (مثلاً صحح الخامة أو المتحف) من غير ما يزود أو يقلل عدد القطع، هنكتشف
    التغيير ونعيد بناء الـ embeddings بدل ما نستخدم نسخة قديمة (stale) من الكاش.
    """
    h = hashlib.sha256()
    for item in unique_data:
        h.update(str(item.get("item_id", "")).encode("utf-8"))
        h.update((item.get("document_text") or "").encode("utf-8"))
    return h.hexdigest()

def _dedup_by_item_id(data):
    """
    إزالة القطع المكررة بناءً على item_id، مع الحفاظ على أول ظهور لكل قطعة
    وترتيب باقي القطع زي ما هو.
    """
    seen_ids = set()
    unique_data = []
    for item in data:
        if item["item_id"] not in seen_ids:
            seen_ids.add(item["item_id"])
            unique_data.append(item)
    return unique_data


def build_collection(data):
    unique_data = _dedup_by_item_id(data)

    # قاعدة بيانات دائمة على القرص بدل client في الميموري بيتبني من الصفر كل مرة.
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    fingerprint = _data_fingerprint(unique_data)

    # لو الكولكشن موجودة أصلاً وبصمة محتواها زي بصمة البيانات الحالية، بنستخدمها كما هي
    # وبنوفر إعادة حساب الـ embeddings (اللي بتاخد وقت طويل خصوصاً على أول تشغيل للسيرفر).
    # الاعتماد على بصمة المحتوى (مش بس العدد) بيضمن إننا نكتشف أي تعديل في بيانات
    # قطعة موجودة أصلاً (زي تصحيح خامة أو متحف) حتى لو العدد الكلي فضل زي ما هو.
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        if (collection.metadata or {}).get("fingerprint") == fingerprint:
            return collection, embedding_model
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    documents = [item["document_text"] for item in unique_data]
    embeddings = embedding_model.encode(documents, show_progress_bar=True)

    collection = client.create_collection(name=COLLECTION_NAME, metadata={"fingerprint": fingerprint})

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
