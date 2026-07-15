import streamlit as st
from src.embeddings import load_data, build_collection
from src.rag import rag_query

# إعدادات الصفحة
st.set_page_config(
    page_title="المرشد الذكي للمتحف المصري",
    page_icon="🏛️",
    layout="centered"
)

st.title("🏛️ المرشد الذكي للمتحف المصري")
st.markdown("اسأل عن أي قطعة أثرية موجودة في المتحف المصري بالقاهرة")

# تحميل البيانات مرة واحدة بس
@st.cache_resource
def init():
    data = load_data()
    collection, embedding_model = build_collection(data)
    return collection, embedding_model

collection, embedding_model = init()

# الـ API Key
api_key = st.sidebar.text_input("Groq API Key", type="password")

# صندوق السؤال
question = st.text_input("اكتب سؤالك هنا", placeholder="مثال: ما هي أشهر التماثيل في المتحف؟")

if question and api_key:
    if st.button("ابحث"):
        with st.spinner("جاري البحث..."):
            result = rag_query(question, collection, embedding_model, api_key)

        # عرض الإجابة
        st.markdown("### الإجابة")
        st.write(result["answer"])

        # عرض المصادر والصور
        st.markdown("### القطع ذات الصلة")
        cols = st.columns(len(result["sources"]))
        for col, source in zip(cols, result["sources"]):
            with col:
                if source["image"]:
                    st.image(source["image"], use_column_width=True)
                st.caption(source["label"])
                if source["material"]:
                    st.caption(f"المادة: {source['material']}")
else:
    if st.button("ابحث"):
        st.warning("من فضلك أدخل الـ Groq API Key في الشريط الجانبي")