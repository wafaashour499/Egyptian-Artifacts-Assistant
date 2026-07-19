import streamlit as st
from dotenv import load_dotenv
import os
from src.embeddings import load_data, build_collection
from src.rag import rag_query

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(
    page_title="المرشد الذكي للآثار المصرية",
    page_icon="🏛️",
    layout="wide"
)

if not api_key:
    st.error("⚠️ مش لاقي GROQ_API_KEY في ملف .env")
    st.stop()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    * { font-family: 'Tajawal', sans-serif; }
    .stApp { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); }
    .chat-message-user {
        background: linear-gradient(135deg, #c9a84c, #f0d080);
        color: #1a1a2e; padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0; max-width: 75%; margin-left: auto;
        text-align: right; font-weight: 600;
    }
    .chat-message-bot {
        background: rgba(255,255,255,0.08); color: #f0f0f0;
        padding: 12px 18px; border-radius: 18px 18px 18px 4px;
        margin: 8px 0; max-width: 80%;
        border: 1px solid rgba(201,168,76,0.3); text-align: right;
    }
    .header-title {
        text-align: center; color: #c9a84c; font-size: 2.5rem;
        font-weight: 700; padding: 20px 0 5px 0;
        text-shadow: 0 0 20px rgba(201,168,76,0.5);
    }
    .header-subtitle { text-align: center; color: #aaa; font-size: 1rem; margin-bottom: 30px; }
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.08) !important; color: white !important;
        border: 1px solid rgba(201,168,76,0.5) !important;
        border-radius: 25px !important; padding: 12px 20px !important; text-align: right;
    }
    .stButton > button {
        background: linear-gradient(135deg, #c9a84c, #f0d080) !important;
        color: #1a1a2e !important; border: none !important;
        border-radius: 25px !important; padding: 10px 30px !important;
        font-weight: 700 !important; width: 100%; height: 50px;
    }
    section[data-testid="stSidebar"] {
    background: rgba(15,52,96,0.9) !important;
    border-right: 1px solid rgba(201,168,76,0.3);
    color: #ffffff !important;
    }
    section[data-testid="stSidebar"] * {
    color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-title">🏛️ المرشد الذكي للآثار المصرية</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">اسأل عن أي قطعة أثرية في المتاحف المصرية</div>', unsafe_allow_html=True)

@st.cache_resource
def init():
    data = load_data()
    collection, embedding_model = build_collection(data)
    return collection, embedding_model

collection, embedding_model = init()

with st.sidebar:
    st.markdown(f"### 🏺 القطع المتاحة: {collection.count()}")
    st.markdown("---")
    st.markdown("### 📚 المتاحف المتاحة")
    st.markdown("🏛️ المتحف المصري بالقاهرة")
    st.markdown("🏺 المتحف المصري الكبير GEM")
    st.markdown("🌊 متحف النوبة")
    st.markdown("🌅 متحف الأقصر")
    st.markdown("---")
    st.markdown("### 💡 أمثلة")
    st.markdown("- ما هي قطع الذهب الموجودة؟")
    st.markdown("- tell me about mummies")
    st.markdown("- تماثيل من عصر الدولة الحديثة")
    st.markdown("---")
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-message-user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message-bot">{msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("sources"):
            cols = st.columns(len(msg["sources"]))
            for col, source in zip(cols, msg["sources"]):
                with col:
                    if source["image"]:
                        st.image(source["image"], use_container_width=True)
                    st.caption(f"📌 {source['label']}")
                    if source["material"]:
                        st.caption(f"🪨 {source['material']}")
                    if source.get("museum"):
                        st.caption(f"🏛️ {source['museum']}")

st.markdown("---")
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input("", placeholder="اكتب سؤالك هنا...", label_visibility="collapsed")
    with col2:
        send = st.form_submit_button("إرسال ➤")

if send and question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.spinner("🔍 جاري البحث..."):
        result = rag_query(question, collection, embedding_model, api_key)
    st.session_state.messages.append({
        "role": "bot",
        "content": result["answer"],
        "sources": result["sources"]
    })
    st.rerun()