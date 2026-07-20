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
    padding: 16px 20px; border-radius: 18px 18px 18px 4px;
    border: 1px solid rgba(201,168,76,0.3); text-align: right;
    height: 100%; line-height: 1.8;
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
    .sources-title {
        color: #c9a84c; font-size: 1rem; font-weight: 700;
        margin: 15px 0 10px 0; text-align: right;
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

def build_chat_history(messages, exclude_last=False):
    history = []
    msgs = messages[:-1] if exclude_last else messages
    for msg in msgs:
        if msg["role"] == "user":
            history.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "bot":
            history.append({"role": "assistant", "content": msg["content"]})
    return history

for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-message-user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        # لو فيه صورة مختارة نعرضها جنب النص
        if msg.get("featured_image"):
            col_img, col_text = st.columns([1, 2])
            with col_img:
                st.image(msg["featured_image"], use_container_width=True)
                st.caption(f"📌 {msg.get('featured_label', '')}")
            with col_text:
                st.markdown(f'<div class="chat-message-bot">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message-bot">{msg["content"]}</div>', unsafe_allow_html=True)

        if msg.get("sources") and not msg.get("featured_image"):
            st.markdown('<div class="sources-title">🏺 قطع مقترحة</div>', unsafe_allow_html=True)
            cols = st.columns(len(msg["sources"]))
            for i, (col, source) in enumerate(zip(cols, msg["sources"])):
                with col:
                    st.markdown(f"""
                    <div style="
                        border: 1px solid rgba(201,168,76,0.3);
                        border-radius: 12px;
                        padding: 10px;
                        text-align: center;
                        transition: all 0.3s ease;
                        background: rgba(255,255,255,0.05);
                    " onmouseover="this.style.border='1px solid #c9a84c';this.style.background='rgba(201,168,76,0.15)';this.style.transform='translateY(-3px)'"
                      onmouseout="this.style.border='1px solid rgba(201,168,76,0.3)';this.style.background='rgba(255,255,255,0.05)';this.style.transform='translateY(0)'">
                    """, unsafe_allow_html=True)

                    if source["image"]:
                        st.image(source["image"], use_container_width=True)
                    st.caption(f"📌 {source['label']}")
                    if source["material"]:
                        st.caption(f"🪨 {source['material']}")
                    if source.get("museum"):
                        st.caption(f"🏛️ {source['museum']}")

                    st.markdown('</div>', unsafe_allow_html=True)

                    if st.button("🔍 اعرف أكثر", key=f"btn_{idx}_{i}_{source['label']}"):
                        auto_question = f"أخبرني بتفاصيل أكثر عن {source['label']}"
                        st.session_state.messages.append({"role": "user", "content": auto_question})
                        chat_history = build_chat_history(st.session_state.messages, exclude_last=True)
                        with st.spinner("🔍 جاري البحث..."):
                            result = rag_query(auto_question, collection, embedding_model, api_key, chat_history)
                        st.session_state.messages.append({
                            "role": "bot",
                            "content": result["answer"],
                            "sources": result["sources"],
                            "featured_image": source["image"],
                            "featured_label": source["label"]
                        })
                        st.rerun()

st.markdown("---")
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input("", placeholder="اكتب سؤالك هنا...", label_visibility="collapsed")
    with col2:
        send = st.form_submit_button("إرسال ➤")

if send and question:
    st.session_state.messages.append({"role": "user", "content": question})
    chat_history = build_chat_history(st.session_state.messages, exclude_last=True)
    with st.spinner("🔍 جاري البحث..."):
        result = rag_query(question, collection, embedding_model, api_key, chat_history)
    st.session_state.messages.append({
        "role": "bot",
        "content": result["answer"],
        "sources": result["sources"]
    })
    st.rerun()