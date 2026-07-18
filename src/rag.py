from groq import Groq

def rag_query(user_question, collection, embedding_model, api_key, n_results=3):
    client_groq = Groq(api_key=api_key)

    # 1. نترجم السؤال للإنجليزي عشان البحث يبقى أدق
    translation = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Translate the following question to English. Return only the translation, nothing else."},
            {"role": "user", "content": user_question}
        ]
    )
    search_query = translation.choices[0].message.content

    # 2. نحوّل السؤال المترجم لـ embedding
    query_embedding = embedding_model.encode([search_query])

    # 3. نجيب أقرب قطع من الـ vector database
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=n_results
    )

    # 4. نبني الـ context
    context_parts = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context_parts.append(f"- {meta['label']}: {doc}")
    context = "\n".join(context_parts)

    # 5. نبعت للـ Groq عشان يجاوب
    response = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """أنت مرشد متحفي متخصص في الآثار المصرية القديمة، عندك معرفة عميقة بالتاريخ المصري القديم والحضارة الفرعونية.

عند الإجابة:
1. استخدم المعلومات المقدمة من قاعدة البيانات كنقطة بداية
2. أكمّل بمعرفتك الأكاديمية عن الآثار والحضارة المصرية
3. اذكر العصر أو الأسرة الحاكمة لو معروفة
4. اشرح أهمية القطعة تاريخياً
5. أجب بالعربي أو الإنجليزي حسب لغة السؤال
6. لو المعلومات غير كافية، قل ذلك بصراحة واذكر ما تعرفه عن الموضوع بشكل عام"""
            },
            {
                "role": "user",
                "content": f"بناءً على المعلومات التالية:\n{context}\n\nسؤال: {user_question}"
            }
        ]
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": [
            {
                "label": meta["label"],
                "image": meta["image"],
                "material": meta["material"],
                "museum": meta.get("museum", ""),
            }
            for meta in results["metadatas"][0]
        ]
    }