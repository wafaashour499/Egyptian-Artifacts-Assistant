import html
import json
import re
import streamlit as st
from dotenv import load_dotenv
import os
from groq import Groq
from src.embeddings import load_data, build_collection
from src.rag import retrieve, generate_answer_stream, language_ok, RagError

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

@st.cache_resource
def get_groq_client():
    return Groq(api_key=api_key)

client_groq = get_groq_client()

MAX_HISTORY_EXCHANGES = 7  # آخر 7 تبادلات (سؤال+رد) بس هي اللي بتتبعت للموديل كسياق
MAX_QUESTIONS_PER_SESSION = 15  # حماية بسيطة من استهلاك الـ Groq API بشكل مبالغ فيه

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
    div[data-testid="InputInstructions"] {
    display: none !important;
    }
    .references-box {
        border: 1px solid rgba(201,168,76,0.3);
        border-radius: 10px;
        background: rgba(255,255,255,0.04);
        padding: 4px 16px;
        margin: 6px 0 14px 0;
        direction: rtl;
    }
    .references-item {
        text-align: right;
        color: #e8e8e8;
        font-size: 0.9rem;
        line-height: 1.9;
        border-top: 1px solid rgba(201,168,76,0.15);
        padding: 8px 0;
    }
    .references-item:first-child { border-top: none; }
    .references-item b { color: #f0d080; }
    .references-item a { color: #9fc4e8; text-decoration: none; }
    .references-item a:hover { text-decoration: underline; }
    div[data-testid="stExpander"] {
        border: 1px solid rgba(201,168,76,0.3) !important;
        border-radius: 10px !important;
        background: rgba(255,255,255,0.04) !important;
        direction: rtl;
    }
    div[data-testid="stExpander"] summary {
        color: #c9a84c !important;
        font-weight: 700 !important;
    }
    .feedback-note {
        font-size: 0.85rem; text-align: right; margin: 4px 0 10px 0;
    }
    .feedback-note.up { color: #6fcf8e; }
    .feedback-note.down { color: #e88a8a; }
    div[class*="st-key-fb-up-"] button {
        background: linear-gradient(135deg, #2e7d4f, #5cb87f) !important;
        color: #ffffff !important;
    }
    div[class*="st-key-fb-down-"] button {
        background: linear-gradient(135deg, #9a3b3b, #d16b6b) !important;
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


@st.cache_data
def load_virtual_tours():
    """بتحمّل كل الجولات الافتراضية من data/virtual_tours.json عشان تتعرض
    بشكل ثابت في الـ sidebar، من غير ما نمر على منطق الـ retrieval/matching."""
    path = os.path.join(os.path.dirname(__file__), "data", "virtual_tours.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


ALL_VIRTUAL_TOURS = load_virtual_tours()

with st.sidebar:
    st.markdown(f"### 🏺 القطع المتاحة: {collection.count()}")
    
    st.markdown("---")
    st.markdown("### 📚 المتاحف المتاحة")
    st.markdown("🏛️ المتحف المصري بالقاهرة")
    st.markdown("🏺 المتحف المصري الكبير GEM")
    st.markdown("🌊 متحف النوبة")
    st.markdown("🌅 متحف الأقصر")
    st.markdown("---")
    if ALL_VIRTUAL_TOURS:
        st.markdown(f"### 🎥 الجولات الافتراضية ({len(ALL_VIRTUAL_TOURS)})")
        for tour in ALL_VIRTUAL_TOURS:
            st.markdown(
                f"🔗 [{html.escape(tour['name'])}]({tour['url']})  \n"
                f"<span style='font-size:0.8rem;color:#aaa;'>{html.escape(tour['location'])}</span>",
                unsafe_allow_html=True,
            )
        st.markdown("---")
    st.markdown("### 💡 أمثلة")
    st.markdown("- من هو رمسيس الثاني؟")
    st.markdown("- ماهي الممياوات؟")
    st.markdown("- تماثيل من عصر الدولة الحديثة")
    st.markdown("---")
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = []
        st.session_state.feedback = {}
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback" not in st.session_state:
    st.session_state.feedback = {}  # {msg_idx: "up" | "down"}
if "question_count" not in st.session_state:
    st.session_state.question_count = 0


def clean_text(text):
    """
    الـ streaming أحياناً بيبعت علامة الترقيم كـ chunk منفصل مسبوق بمسافة
    (مثلاً 'كلمة' ثم ' .')، وده بيسبب التفاف غلط للسطر في الاتجاه RTL.
    بنشيل أي مسافة قبل علامات الترقيم مباشرة.
    """
    return re.sub(r"\s+([.,،؛؛:؟!])", r"\1", text or "")


def escape_for_html(text):
    """نمنع أي HTML/JS جاي من المستخدم أو من رد الموديل إنه يتنفذ جوه الصفحة."""
    return html.escape(clean_text(text) or "").replace("\n", "<br>")


def build_chat_history(messages, exclude_last=False):
    msgs = messages[:-1] if exclude_last else messages
    # بنحد السياق بآخر 7 تبادلات (سؤال + رد) بس، عشان السياق ميكبرش من غير حد
    msgs = msgs[-(MAX_HISTORY_EXCHANGES * 2):]
    history = []
    for msg in msgs:
        if msg["role"] == "user":
            history.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "bot":
            history.append({"role": "assistant", "content": msg["content"]})
    return history


def render_references(references):
    if not references:
        return
    with st.expander(f"📚 المصادر ({len(references)})", expanded=False):
        for ref in references:
            line = f"🏺 <b>{escape_for_html(ref['label'])}</b>"
            if ref.get("museum"):
                line += f" — 🏛️ {escape_for_html(ref['museum'])}"
            if ref.get("material"):
                line += f" — 🪨 {escape_for_html(ref['material'])}"
            if ref.get("wikidata_url"):
                line += f' — <a href="{ref["wikidata_url"]}" target="_blank">🔗 المصدر على Wikidata</a>'
            st.markdown(f'<div class="references-item">{line}</div>', unsafe_allow_html=True)


def render_tours(tours):
    if not tours:
        return
    for tour in tours:
        st.markdown(f"""
        <div style="
            border: 1px solid rgba(159,196,232,0.4);
            border-radius: 10px;
            background: rgba(159,196,232,0.08);
            padding: 10px 16px;
            margin: 6px 0;
            text-align: right;
            direction: rtl;
        ">
            🎥 حابب تجرب جولة افتراضية داخل <b>{escape_for_html(tour['name'])}</b>
            ({escape_for_html(tour['location'])})؟
            <a href="{tour['url']}" target="_blank" style="color:#9fc4e8; font-weight:700;">ابدأ الجولة 🔗</a>
        </div>
        """, unsafe_allow_html=True)


def to_thumb_url(url, width=550):
    """
    بتحول رابط صورة Wikimedia الأصلي (اللي ممكن يكون كذا ميجابايت) لرابط
    نسخة مصغّرة (thumbnail) بعرض width بكسل، بنفس الجودة المعروضة على الشاشة
    تقريباً بس بحجم ملف أصغر بكتير وتحميل أسرع.

    500-600px كافية جداً لعرض الويب/الموبايل، فمفيش أي فقدان جودة ملحوظ.
    """
    if not url:
        return url
    if "/commons/thumb/" in url:
        return url  # already a thumbnail
    if "upload.wikimedia.org/wikipedia/commons/" in url:
        try:
            path = url.split("/wikipedia/commons/", 1)[1]
            filename = path.split("/")[-1]
            return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{path}/{width}px-{filename}"
        except IndexError:
            return url
    return url


def render_image(url, height="180px", thumb_width=700):
    """
    بتعرض صورة، ولو الرابط فشل أو فاضي بتستبدلها تلقائياً
    بمربع رمادي مكتوب عليه 'الصورة غير متاحة' بدل ما تفضل مساحة فاضية.

    بتستخدم نسخة مصغّرة (thumbnail) من Wikimedia بعرض thumb_width بكسل
    بدل الصورة الأصلية، عشان التحميل يبقى أسرع بكتير من غير فرق ملحوظ
    في الجودة المعروضة.
    """
    placeholder = f"""
    <div style="width:100%;height:{height};display:flex;align-items:center;justify-content:center;
                background:#3a3a4a;color:#ccc;font-size:0.85rem;text-align:center;border-radius:10px;
                flex-direction:column;gap:6px;">
        <span style="font-size:1.6rem;">🖼️</span>
        <span>الصورة غير متاحة</span>
    </div>
    """
    if not url:
        st.markdown(placeholder, unsafe_allow_html=True)
        return

    display_url = to_thumb_url(url, width=thumb_width)
    safe_url = html.escape(display_url, quote=True)

    st.markdown(f"""
    <div style="position:relative; width:100%;">
        <img src="{safe_url}" loading="lazy"
             style="width:100%;height:{height};object-fit:cover;border-radius:10px;display:block;"
             onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
        <div style="display:none;width:100%;height:{height};align-items:center;justify-content:center;
                    background:#3a3a4a;color:#ccc;font-size:0.85rem;text-align:center;border-radius:10px;
                    flex-direction:column;gap:6px;">
            <span style="font-size:1.6rem;">🖼️</span>
            <span>الصورة غير متاحة</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def log_feedback(question, answer, rating):
    """بنسجل التقييم في ملف محلي؛ لو فشل التسجيل مش المفروض يوقف التطبيق."""
    try:
        with open("feedback_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(
                {"question": question, "answer": answer, "rating": rating},
                ensure_ascii=False
            ) + "\n")
    except Exception:
        pass


def render_feedback_buttons(idx, question, answer):
    existing = st.session_state.feedback.get(idx)
    if existing:
        label = "👍 مفيد" if existing == "up" else "👎 غير مفيد"
        css_class = "up" if existing == "up" else "down"
        st.markdown(
            f'<div class="feedback-note {css_class}">شكراً على تقييمك: {label} ✅</div>',
            unsafe_allow_html=True
        )
        return

    col_up, col_down, _ = st.columns([1, 1, 6])
    with col_up:
        with st.container(key=f"fb-up-{idx}"):
            if st.button("👍", key=f"fb_up_{idx}"):
                st.session_state.feedback[idx] = "up"
                log_feedback(question, answer, "up")
                st.rerun()
    with col_down:
        with st.container(key=f"fb-down-{idx}"):
            if st.button("👎", key=f"fb_down_{idx}"):
                st.session_state.feedback[idx] = "down"
                log_feedback(question, answer, "down")
                st.rerun()


def ask_and_append(question, extra_bot_fields=None, force_lang=None):
    """
    بتعمل: append سؤال المستخدم -> retrieval -> streaming للرد -> append الرد.
    بترجع True لو نجحت، وبتعمل st.error لو حصل خطأ.

    force_lang: تمريرها لـ retrieve() عشان تفرض لغة الرد (مفيدة لزرار "اعرف أكثر").
    """
    if st.session_state.question_count >= MAX_QUESTIONS_PER_SESSION:
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.messages.append({
            "role": "bot",
            "content": (
                "وصلت للحد الأقصى من الأسئلة المسموح بيها في الجلسة الواحدة (15 سؤال). "
                "من فضلك حدّث الصفحة أو ارجع بعد فترة قصيرة للمتابعة."
            ),
            "sources": [],
            "references": [],
        })
        return False

    st.session_state.question_count += 1
    st.session_state.messages.append({"role": "user", "content": question})
    chat_history = build_chat_history(st.session_state.messages, exclude_last=True)

    try:
        with st.spinner("🔍 جاري البحث..."):
            prep = retrieve(question, collection, embedding_model, client_groq, force_lang=force_lang)
    except RagError as e:
        st.session_state.messages.append({"role": "bot", "content": str(e), "sources": [], "references": []})
        return False

    placeholder = st.empty()
    full_text = ""
    try:
        for chunk in generate_answer_stream(
            prep["client_groq"], question, prep["context"], prep["lang_instruction"], chat_history
        ):
            full_text += chunk
            placeholder.markdown(
                f'<div class="chat-message-bot">{escape_for_html(full_text)}</div>',
                unsafe_allow_html=True
            )
    except RagError as e:
        if not full_text:
            st.session_state.messages.append({"role": "bot", "content": str(e), "sources": [], "references": []})
            return False
        # لو انقطع الاتصال بعد ما بدأ يرد، نحتفظ باللي وصلنا منه
        full_text += f"\n\n⚠️ {e}"

    # حارس اللغة: لو الرد طلع بلغة غلط (نادر بس بيحصل)، نعيد المحاولة مرة واحدة بتعليمة أقوى
    if not language_ok(full_text, prep["lang"]):
        retry_text = ""
        try:
            for chunk in generate_answer_stream(
                prep["client_groq"], question, prep["context"], prep["lang_instruction"], chat_history,
                strict=True,
            ):
                retry_text += chunk
                placeholder.markdown(
                    f'<div class="chat-message-bot">{escape_for_html(retry_text)}</div>',
                    unsafe_allow_html=True
                )
            if retry_text and language_ok(retry_text, prep["lang"]):
                full_text = retry_text
        except RagError:
            pass  # فشلت المحاولة التانية: نسيب الرد الأول زي ما هو بدل ما نضيع الرد كله

    msg = {
        "role": "bot",
        "content": full_text,
        "sources": prep["sources"],
        "references": prep["references"],
        "tours": prep.get("tours", []),
    }
    if extra_bot_fields:
        msg.update(extra_bot_fields)
    st.session_state.messages.append(msg)
    return True


for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-message-user">{escape_for_html(msg["content"])}</div>', unsafe_allow_html=True)
    else:
        # لو فيه صورة مختارة نعرضها جنب النص
        if msg.get("featured_image"):
            col_img, col_text = st.columns([1, 2])
            with col_img:
                render_image(msg["featured_image"], height="340px")
                st.caption(f"📌 {msg.get('featured_label', '')}")
            with col_text:
                st.markdown(f'<div class="chat-message-bot">{escape_for_html(msg["content"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message-bot">{escape_for_html(msg["content"])}</div>', unsafe_allow_html=True)

        render_references(msg.get("references"))
        render_tours(msg.get("tours"))

        question_for_feedback = st.session_state.messages[idx - 1]["content"] if idx > 0 else ""
        render_feedback_buttons(idx, question_for_feedback, msg["content"])

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

                    render_image(source["image"], height="230px")
                    st.caption(f"📌 {source['label']}")
                    if source["material"]:
                        st.caption(f"🪨 {source['material']}")
                    if source.get("museum"):
                        st.caption(f"🏛️ {source['museum']}")

                    st.markdown('</div>', unsafe_allow_html=True)

                    if st.button("🔍 اعرف أكثر", key=f"btn_{idx}_{i}_{source['label']}"):
                        auto_question = f"أخبرني بتفاصيل أكثر عن {source['label']}"
                        ask_and_append(
                            auto_question,
                            extra_bot_fields={"featured_image": source["image"], "featured_label": source["label"]},
                            force_lang="arabic",
                        )
                        st.rerun()

st.markdown("---")
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input("", placeholder="اكتب سؤالك هنا...", label_visibility="collapsed")
    with col2:
        send = st.form_submit_button("إرسال ➤")

if send and question:
    ask_and_append(question)
    st.rerun()
