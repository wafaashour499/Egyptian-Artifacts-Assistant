import streamlit as st
from src.embeddings import load_data, build_collection
from src.rag import rag_query

st.set_page_config(
    page_title="المرشد الذكي للآثار المصرية",
    page_icon="🏛️",
    layout="wide"
)

# CSS مخصص محسّن ومصلح
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    
    * { font-family: 'Tajawal', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-bottom: 30px;
    }
    
    .chat-message-user {
        background: linear-gradient(135deg, #c9a84c, #f0d080);
        color: #1a1a2e;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 75%;
        margin-left: auto;
        text-align: right;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    .chat-message-bot {
        background: rgba(255,255,255,0.08);
        color: #f0f0f0;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
        border: 1px solid rgba(201, 168, 76, 0.3);
        text-align: right;
    }
    
    .header-title {
        text-align: center;
        color: #c9a84c;
        font-size: 2.5rem;
        font-weight: 700;
        padding: 20px 0 5px 0;
        text-shadow: 0 0 20px rgba(201,168,76,0.5);
    }
    
    .header-subtitle {
        text-align: center;
        color: #aaa;
        font-size: 1rem;
        margin-bottom: 30px;
    }

    /* تحسين تصميم الكارت ليحتوي عناصر الـ Streamlit */
    div[data-testid="stVerticalBlock"] > div:has(div.artifact-card-wrapper) {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(201,168,76,0.3) !important;
        border-radius: 12px !important;
        padding: 15px !important;
        text-align: center !important;
    }

    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.08) !important;
        color: white !important;
        border: 1px solid rgba(201,168,76,0.5) !important;
        border-radius: 25px !important;
        padding: 12px 20px !important;
        text-align: right;
    }

    .stButton > button {
        background: linear-gradient(135deg, #c9a84c, #f0d080) !important;
        color: #1a1a2e !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 10px 30px !important;
        font-weight: 700 !important;
        width: 100%;
        height: 50px;
    }

    section[data-testid="stSidebar"] {
        background: rgba(15, 52, 96, 0.9) !important;
        border-right: 1px solid rgba(201,168,76,0.3);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header-title">🏛️ المرشد الذكي للآثار المصرية</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">اسأل عن أي قطعة أثرية في المتاحف المصرية</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🔑 الإعدادات")
    api_key = st.text_input("Groq API Key", type="password")
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

# تحميل البيانات
@st.cache_resource
def init():
    data = load_data()
    collection, embedding_model = build_collection(data)
    return collection, embedding_model

collection, embedding_model = init()

# تاريخ المحادثة
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض المحادثة داخل حاوية مخصصة
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-message-user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message-bot">{msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("sources"):
            cols = st.columns(len(msg["sources"]))
            for col, source in zip(cols, msg["sources"]):
                with col:
                    # علامة نستخدمها في الـ CSS لتطبيق التنسيق على العمود
                    st.markdown('<div class="artifact-card-wrapper"></div>', unsafe_allow_html=True)
                    if source["image"]:
                        st.image(source["image"], use_container_width=True)
                    st.caption(f"📌 {source['label']}")
                    if source["material"]:
                        st.caption(f"🪨 {source['material']}")
                    if source.get("museum"):
                        st.caption(f"🏛️ {source['museum']}")
st.markdown('</div>', unsafe_allow_html=True)

# استخدام st.form لحل مشكلة اختفاء النصوص عند الضغط على الأزرار
st.markdown("---")
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input("", placeholder="اكتب سؤالك هنا...", label_visibility="collapsed")
    with col2:
        send = st.form_submit_button("إرسال ➤")

if send and question:
    if api_key:
        # إضافة سؤال المستخدم فوراً وتحديث الشاشة
        st.session_state.messages.append({"role": "user", "content": question})
        
        with st.spinner("🔍 جاري البحث والاستقصاء..."):
            result = rag_query(question, collection, embedding_model, api_key)
        
        # إضافة إجابة البوت
        st.session_state.messages.append({
            "role": "bot",
            "content": result["answer"],
            "sources": result["sources"]
        })
        st.rerun()
    else:
        st.warning("⚠️ من فضلك أدخل الـ Groq API Key في الشريط الجانبي")