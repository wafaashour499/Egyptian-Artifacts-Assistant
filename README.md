# 🏛️ المرشد الذكي للآثار المصرية | Egyptian Artifacts Assistant

نظام **RAG (Retrieval-Augmented Generation)** بيرد على أسئلتك عن القطع الأثرية المصرية القديمة، باللغة العربية أو الإنجليزية، باستخدام بيانات حقيقية من Wikidata ونموذج Llama 3.3 عبر Groq.

A **RAG (Retrieval-Augmented Generation)** system that answers questions about ancient Egyptian artifacts, in Arabic or English, using real data from Wikidata and Llama 3.3 via Groq.

🔗 **جرّب التطبيق مباشرة | Live Demo:** https://egyptian-artifacts-assistant.streamlit.app/

---

## 📸 لقطات من الواجهة | Screenshots

<p align="center">
  <img src="assets/screenshot-home.png" alt="الصفحة الرئيسية" width="80%">
</p>
<p align="center">
  <img src="assets/screenshot-chat.png" alt="مثال على محادثة" width="80%">
</p>

---

## 🇪🇬 نظرة عامة

بتسأل بالعربي أو الإنجليزي عن أي قطعة أثرية، ملك، أو متحف، والنظام:
1. بيبحث في قاعدة بيانات القطع الأثرية (متحف القاهرة، الأقصر، النوبة، المتحف المصري الكبير)
2. بيجيب أقرب القطع المرتبطة بسؤالك (Semantic Search)
3. بيولّد رد متكامل بالعربية دايماً، مبني على البيانات المسترجعة + معرفة الموديل التاريخية

### ✨ المميزات
- 🔍 **بحث دلالي متعدد اللغات** — اسأل بالعربي أو الإنجليزي، النتيجة واحدة
- 🌊 **رد Streaming** — الإجابة بتظهر أول بأول بدل الانتظار للرد كامل
- 📚 **مصادر موثّقة** — كل رد معاه قسم "المصادر" برابط مباشر لصفحة القطعة على Wikidata
- 🎥 **جولات افتراضية** — روابط تلقائية لجولات Matterport لو القطعة مرتبطة بموقع أثري متاح جولته
- 🖼️ **صور مع Fallback** — لو رابط الصورة اتعطل، بيظهر بديل بدل مساحة فاضية
- 👍 **تقييم المستخدم** — زرار إعجاب/عدم إعجاب تحت كل رد
- 🏺 **قطع مقترحة** — كروت تفاعلية لاستكشاف قطع مشابهة بضغطة زرار

---

## 🇬🇧 Overview

Ask in Arabic or English about any artifact, king, or museum, and the system:
1. Searches the artifacts database (Cairo, Luxor, Nubian, and Grand Egyptian museums)
2. Retrieves the most relevant items via semantic search
3. Generates a complete answer — always in Arabic — grounded in the retrieved data plus the model's historical knowledge

### ✨ Features
- 🔍 **Multilingual semantic search** — ask in Arabic or English, same accurate results
- 🌊 **Streaming responses** — answers appear progressively instead of a blocking wait
- 📚 **Cited sources** — every answer includes a collapsible "Sources" section linking directly to the Wikidata entry
- 🎥 **Virtual tours** — automatic links to Matterport 3D tours when a retrieved artifact matches a site with an available tour
- 🖼️ **Image fallback** — broken image links gracefully fall back to a placeholder instead of empty space
- 👍 **User feedback** — thumbs up/down on every response
- 🏺 **Suggested artifacts** — interactive cards to explore related pieces with one click

---

## 🛠️ التقنيات المستخدمة | Tech Stack

| الطبقة | التقنية |
|---|---|
| الواجهة | [Streamlit](https://streamlit.io) |
| نموذج اللغة | Llama 3.3 70B عبر [Groq API](https://groq.com) |
| الـ Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (Sentence Transformers) |
| قاعدة بيانات المتجهات | [ChromaDB](https://www.trychroma.com) (Persistent Client) |
| مصدر البيانات | [Wikidata](https://www.wikidata.org) (رخصة CC0) |

---

## 📂 هيكل المشروع | Project Structure

```
Egyptian-Artifacts-Assistant/
├── app.py                      # واجهة Streamlit الرئيسية
├── requirements.txt
├── .env                        # GROQ_API_KEY (غير مرفوع على GitHub)
├── data/
│   ├── egyptian_museum_cairo.json
│   ├── gem_artifacts.json
│   ├── luxor_artifacts.json
│   ├── nubian_artifacts.json
│   └── virtual_tours.json      # روابط الجولات الافتراضية
└── src/
    ├── data_loader.py          # جمع بيانات القطع من Wikidata
    ├── embeddings.py           # بناء الـ embeddings وقاعدة ChromaDB
    └── rag.py                  # منطق الاسترجاع + التوليد + الـ streaming
```

---

## 🚀 التشغيل محلياً | Run Locally

```bash
# 1) Clone
git clone https://github.com/wafaashour499/Egyptian-Artifacts-Assistant.git
cd Egyptian-Artifacts-Assistant

# 2) بيئة افتراضية | virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3) المكتبات | dependencies
pip install -r requirements.txt

# 4) ملف الإعدادات | environment file
echo "GROQ_API_KEY=your_key_here" > .env

# 5) تشغيل | run
streamlit run app.py
```

> على Streamlit Community Cloud، حطي `GROQ_API_KEY` في **Secrets** بدل `.env`.
> On Streamlit Community Cloud, add `GROQ_API_KEY` under **Secrets** instead of `.env`.

---

## 📊 مصدر البيانات | Data Source

البيانات مسحوبة من **Wikidata** (رخصة [CC0](https://creativecommons.org/publicdomain/zero/1.0/) — مفتوحة بالكامل)، وصور القطع من **Wikimedia Commons**.

All data is sourced from **Wikidata** (fully open [CC0](https://creativecommons.org/publicdomain/zero/1.0/) license), with artifact images from **Wikimedia Commons**.

---

## 🤝 المساهمة | Contributing

الـ Pull Requests والاقتراحات مرحّب بيها. لو لقيت مشكلة أو عندك فكرة تحسين، افتح [Issue](../../issues) جديد.

Pull requests and suggestions are welcome. Found a bug or have an idea? Open an [Issue](../../issues).

---

## 📄 الترخيص | License

 This project is licensed under the MIT License.
