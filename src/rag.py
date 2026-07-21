import json
from groq import Groq

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """أنت مرشد متحفي متخصص في الآثار المصرية القديمة، عندك معرفة عميقة بالتاريخ المصري القديم والحضارة الفرعونية.

عند الإجابة:
1. استخدم المعلومات المقدمة من قاعدة البيانات كنقطة بداية
2. أكمّل بمعرفتك الأكاديمية عن الآثار والحضارة المصرية
3. اذكر العصر أو الأسرة الحاكمة لو معروفة
4. اشرح أهمية القطعة تاريخياً
5. لو المعلومات غير كافية، قل ذلك بصراحة واذكر ما تعرفه عن الموضوع بشكل عام"""


class RagError(Exception):
    """خطأ واضح نقدر نعرضه للمستخدم برسالة لطيفة بدل ما التطبيق يكراش."""
    pass


def _has_arabic(text):
    return any("\u0600" <= ch <= "\u06FF" for ch in text)


def _analyze_question(client_groq, user_question):
    """
    نداء واحد بس للـ Groq: بيترجم السؤال للإنجليزي (لتحسين البحث في قاعدة البيانات)
    وبيحدد لغة السؤال الأصلية، مع بعض، بدل نداءين منفصلين زي الأول.
    """
    try:
        resp = client_groq.chat.completions.create(
            model=MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": (
                    "Return ONLY a compact JSON object (no markdown fences, no explanation) "
                    'with exactly two keys: "translation" (the given question translated to '
                    'English) and "lang" (either "arabic" or "english" — the language of the '
                    "ORIGINAL question)."
                )},
                {"role": "user", "content": user_question}
            ]
        )
        raw = resp.choices[0].message.content.strip().strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
        data = json.loads(raw)
        translation = (data.get("translation") or user_question).strip()
        lang = (data.get("lang") or "").strip().lower()
        if lang not in ("arabic", "english"):
            lang = "arabic" if _has_arabic(user_question) else "english"
        return translation, lang
    except Exception:
        # فشل النداء أو الرد مش JSON سليم: نكمل بدون ترجمة بدل ما نوقف التطبيق كله
        return user_question, "arabic" if _has_arabic(user_question) else "english"


def retrieve(user_question, collection, embedding_model, api_key, n_results=3):
    """
    كل الخطوات اللي قبل توليد الرد: تحليل السؤال، البحث في قاعدة البيانات،
    بناء الـ context، وتجهيز القطع المقترحة والمصادر.
    """
    client_groq = Groq(api_key=api_key)

    search_query, lang = _analyze_question(client_groq, user_question)

    lang_instruction = (
        "You MUST respond in English only. Do not use Arabic at all."
        if lang == "english"
        else "يجب أن تجيب باللغة العربية فقط. لا تستخدم الإنجليزية أبداً."
    )

    try:
        query_embedding = embedding_model.encode([search_query])
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=max(n_results, 1) * 2,  # بنجيب أكتر من المطلوب لأن الـ dedup بعد كده هيقلل العدد
        )
    except Exception as e:
        raise RagError("مشكلة في الوصول لقاعدة بيانات القطع الأثرية، حاول تاني.") from e

    # dedup على أساس اسم القطعة، مع وقف لحد ما نوصل للعدد المطلوب فعلياً
    seen_labels = set()
    unique_docs, unique_metas = [], []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        if meta["label"] in seen_labels:
            continue
        seen_labels.add(meta["label"])
        unique_docs.append(doc)
        unique_metas.append(meta)
        if len(unique_docs) >= n_results:
            break

    context = "\n".join(f"- {meta['label']}: {doc}" for doc, meta in zip(unique_docs, unique_metas))

    sources = [
        {
            "label": meta["label"],
            "image": meta["image"],
            "material": meta["material"],
            "museum": meta.get("museum", ""),
        }
        for meta in unique_metas
    ]

    references = [
        {
            "label": meta["label"],
            "museum": meta.get("museum", ""),
            "material": meta.get("material", ""),
            "wikidata_url": f"https://www.wikidata.org/wiki/{meta['item_id']}" if meta.get("item_id") else "",
        }
        for meta in unique_metas
    ]

    return {
        "client_groq": client_groq,
        "context": context,
        "lang_instruction": lang_instruction,
        "sources": sources,
        "references": references,
    }


def generate_answer_stream(client_groq, user_question, context, lang_instruction, chat_history=None):
    """
    بيرجع generator بيبعت أجزاء من الرد أول بأول (streaming) بدل ما ينتظر الرد كامل.
    استخدامه المتوقع: for chunk in generate_answer_stream(...): ...
    أو تمريره مباشرة لـ st.write_stream في Streamlit.
    """
    chat_history = chat_history or []
    try:
        stream = client_groq.chat.completions.create(
            model=MODEL,
            stream=True,
            messages=[
                {"role": "system", "content": f"{lang_instruction}\n\n{SYSTEM_PROMPT}"},
                *chat_history,
                {
                    "role": "user",
                    "content": f"بناءً على المعلومات التالية:\n{context}\n\nسؤال: {user_question}",
                },
            ],
        )
    except Exception as e:
        raise RagError("مشكلة في التواصل مع نموذج الذكاء الاصطناعي، حاول تاني.") from e

    def _iter():
        try:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            raise RagError("انقطع الاتصال أثناء توليد الرد، حاول تاني.") from e

    return _iter()
