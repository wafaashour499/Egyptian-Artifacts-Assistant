from groq import Groq

def rag_query(user_question, collection, embedding_model, api_key, n_results=3):
    # 1. نحوّل السؤال لـ embedding
    query_embedding = embedding_model.encode([user_question])

    # 2. نجيب أقرب قطع من الـ vector database
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=n_results
    )

    # 3. نبني الـ context
    context_parts = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context_parts.append(f"- {meta['label']}: {doc}")
    context = "\n".join(context_parts)

    # 4. نبعت للـ Groq
    client_groq = Groq(api_key=api_key)

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
            }
            for meta in results["metadatas"][0]
        ]
    }