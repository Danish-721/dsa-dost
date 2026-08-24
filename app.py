import streamlit as st
from groq import Groq
import os
import io
import uuid
from typing import List, Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
import datetime
import html
import re

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="DSA Dost — AI DSA Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAX_HISTORY = 12
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_API_KEY_HARDCODED = None

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONT_PATH = os.path.join(FONT_DIR, "NotoSansDevanagari-Regular.ttf")

SYSTEM_PROMPT = """
You are "DSA Dost" — an expert, friendly tutor for Data Structures & Algorithms.
Your replies MUST be grammatically correct, clear, and well-formed sentences.
Avoid broken Hindi, fractured English, slang, or filler.
Use a balanced Hinglish style: technical definitions in clear English, short
explanatory sentences in simple Hindi. Never reply completely in only Hindi
or only English.

Tone & Style:
- Friendly, encouraging, and concise.
- Use 1–3 short sentences per idea.
- Use phrases like "Mast question!" occasionally, but do NOT overuse them.
- Avoid repeating the same sentence or phrase across replies.
- If the user repeats the same question, give a fresh analogy or example.

Answer Structure:
1. Definition (1–2 sentences in English, exam-friendly).
2. Short Explanation (2–4 sentences in simple Hinglish; use an analogy).
3. Offer next step question: Ask either "Example chahiye?" or
   "Code dekhna hai?" — only one short question.
If the user explicitly asks for code or example, provide it immediately.

Code & Examples:
- Default language: C++.
- If the user requests Python, Java, or JavaScript, switch.
- Provide clean, tested, commented code.
- Include Time & Space complexity for algorithmic/code questions.

Memory:
- Maintain short-term conversation context.
- If the user asks what they asked earlier, summarize previous messages concisely.

Out-of-scope:
If asked about non-DSA topics, politely say:
"Yaar, ye DSA se bahar hai. Main DSA mein madad kar sakta hoon — koi DSA sawaal pucho."

If you don't know an answer, say:
"Example me abhi beta version hu. I am under development."
and offer to search if allowed.

Language:
- Use ONLY English and Hindi.
"""

# ============================================================
# PREMIUM UI CSS
# ============================================================
st.markdown(
    """
<style>
/* ---------- Global ---------- */
.stApp {
    background:
        radial-gradient(circle at 12% 8%, rgba(124, 58, 237, 0.13), transparent 27%),
        radial-gradient(circle at 88% 15%, rgba(37, 99, 235, 0.10), transparent 26%),
        radial-gradient(circle at 52% 100%, rgba(6, 182, 212, 0.06), transparent 30%),
        #070910;
    color: #f8fafc;
}

[data-testid="stAppViewContainer"] {
    background: transparent;
}

[data-testid="stHeader"] {
    background: rgba(7, 9, 16, 0.72);
}

.block-container {
    max-width: 1180px;
    padding-top: 2.2rem;
    padding-bottom: 7rem;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(17, 20, 31, 0.98), rgba(9, 11, 18, 0.99));
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.4rem;
}

section[data-testid="stSidebar"] .stButton > button,
section[data-testid="stSidebar"] .stDownloadButton > button {
    width: 100%;
    border-radius: 11px;
    border: 1px solid rgba(255,255,255,0.09);
    background: rgba(255,255,255,0.045);
    color: #e5e7eb;
    transition: all .2s ease;
}

section[data-testid="stSidebar"] .stButton > button:hover,
section[data-testid="stSidebar"] .stDownloadButton > button:hover {
    border-color: rgba(124,58,237,.45);
    background: rgba(124,58,237,.12);
    transform: translateY(-1px);
}

.sidebar-brand {
    display:flex;
    align-items:center;
    gap:12px;
    padding: 5px 2px 20px 2px;
}

.brand-logo {
    width:44px;
    height:44px;
    border-radius:14px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:22px;
    background: linear-gradient(135deg,#7c3aed,#2563eb);
    box-shadow: 0 10px 30px rgba(124,58,237,.28);
}

.brand-title {
    font-size:18px;
    font-weight:800;
    letter-spacing:-.3px;
}

.brand-subtitle {
    color:#8f98aa;
    font-size:11px;
    margin-top:2px;
}

.sidebar-section {
    color:#71798a;
    font-size:10px;
    font-weight:800;
    letter-spacing:1.5px;
    margin:22px 0 10px;
    text-transform:uppercase;
}

.sidebar-info {
    padding:12px 13px;
    border:1px solid rgba(255,255,255,.07);
    border-radius:12px;
    background:rgba(255,255,255,.025);
    color:#aab2c0;
    font-size:12px;
    line-height:1.5;
}

.sidebar-info strong {
    color:#e7eaf0;
}

.sidebar-footer {
    position: fixed;
    bottom: 18px;
    left: 20px;
    color:#596274;
    font-size:10px;
    line-height:1.6;
}

/* ---------- Header ---------- */
.hero {
    text-align:center;
    padding: 8px 0 18px;
}

.hero-badge {
    display:inline-flex;
    align-items:center;
    gap:7px;
    padding:7px 12px;
    border-radius:999px;
    border:1px solid rgba(124,58,237,.25);
    background:rgba(124,58,237,.08);
    color:#c4b5fd;
    font-size:11px;
    font-weight:700;
    letter-spacing:.5px;
}

.online-dot {
    width:7px;
    height:7px;
    border-radius:50%;
    background:#22c55e;
    box-shadow:0 0 12px rgba(34,197,94,.8);
}

.hero h1 {
    margin:17px 0 6px;
    font-size: clamp(34px, 5vw, 58px);
    line-height:1.05;
    letter-spacing:-2.5px;
    font-weight:850;
    background:linear-gradient(90deg,#ffffff 5%,#c4b5fd 48%,#67e8f9 95%);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.hero p {
    color:#8f98aa;
    margin:0 auto;
    font-size:14px;
}

/* ---------- Welcome ---------- */
.welcome-card {
    position:relative;
    overflow:hidden;
    margin: 10px auto 22px;
    max-width: 850px;
    padding: 32px;
    border-radius:24px;
    border:1px solid rgba(255,255,255,.085);
    background:
        radial-gradient(circle at 20% 10%, rgba(124,58,237,.12), transparent 35%),
        linear-gradient(135deg, rgba(255,255,255,.045), rgba(255,255,255,.018));
    box-shadow: 0 25px 80px rgba(0,0,0,.25);
    text-align:center;
}

.welcome-icon {
    width:62px;
    height:62px;
    margin:0 auto 16px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:20px;
    font-size:30px;
    background:linear-gradient(135deg,rgba(124,58,237,.22),rgba(37,99,235,.18));
    border:1px solid rgba(167,139,250,.2);
}

.welcome-card h2 {
    margin:0 0 8px;
    font-size:27px;
    letter-spacing:-.7px;
}

.welcome-card p {
    color:#929bad;
    margin:0 auto;
    max-width:600px;
    font-size:13px;
    line-height:1.7;
}

/* ---------- Prompt cards ---------- */
.prompt-label {
    color:#737c8d;
    font-size:10px;
    font-weight:800;
    letter-spacing:1.5px;
    text-transform:uppercase;
    margin: 5px 0 10px;
}

.prompt-card {
    min-height:78px;
    padding:14px 15px;
    border-radius:16px;
    border:1px solid rgba(255,255,255,.075);
    background:rgba(255,255,255,.028);
    transition:all .2s ease;
}

.prompt-card:hover {
    border-color:rgba(124,58,237,.35);
    background:rgba(124,58,237,.07);
    transform:translateY(-2px);
}

.prompt-icon {
    font-size:18px;
    margin-bottom:6px;
}

.prompt-title {
    color:#e8ebf1;
    font-size:12px;
    font-weight:700;
}

.prompt-sub {
    color:#747d8f;
    font-size:10px;
    margin-top:3px;
}

/* ---------- Streamlit buttons ---------- */
.stButton > button {
    border-radius:13px;
    min-height:44px;
    background:rgba(255,255,255,.035);
    border:1px solid rgba(255,255,255,.08);
    color:#dce1ea;
    font-weight:600;
    transition:all .2s ease;
}

.stButton > button:hover {
    border-color:rgba(124,58,237,.42);
    background:rgba(124,58,237,.09);
    color:#fff;
}

/* ---------- Chat ---------- */
[data-testid="stChatMessage"] {
    border:1px solid rgba(255,255,255,.065);
    background:rgba(255,255,255,.025);
    border-radius:20px;
    padding: 15px 18px;
    margin: 10px 0;
    box-shadow:0 10px 35px rgba(0,0,0,.12);
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background:linear-gradient(135deg,rgba(124,58,237,.10),rgba(37,99,235,.055));
    border-color:rgba(124,58,237,.16);
}

[data-testid="stChatMessage"] p {
    color:#dce1e9;
    font-size:14px;
    line-height:1.72;
}

[data-testid="stChatMessage"] code {
    border-radius:6px;
}

/* ---------- Code blocks ---------- */
[data-testid="stChatMessage"] pre {
    border:1px solid rgba(255,255,255,.08);
    border-radius:13px;
    background:#0a0d14 !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}

[data-testid="stChatMessage"] pre code {
    font-size:12px !important;
    line-height:1.65 !important;
}

/* ---------- Chat input ---------- */
[data-testid="stChatInput"] {
    border-top:0 !important;
    background:transparent !important;
}

[data-testid="stChatInput"] > div {
    background:rgba(16,19,29,.88) !important;
    border:1px solid rgba(255,255,255,.10) !important;
    border-radius:18px !important;
    box-shadow:
        0 15px 45px rgba(0,0,0,.38),
        0 0 0 1px rgba(124,58,237,.025) !important;
    backdrop-filter:blur(18px);
}

[data-testid="stChatInput"] textarea {
    color:#f8fafc !important;
    font-size:14px !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color:#697285 !important;
}

/* ---------- Divider ---------- */
.soft-divider {
    height:1px;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,.08),transparent);
    margin:20px 0;
}

/* ---------- Footer ---------- */
.app-footer {
    text-align:center;
    color:#50596a;
    font-size:10px;
    padding:18px 0 4px;
}

/* ---------- Hide Streamlit chrome ---------- */
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header[data-testid="stHeader"] {
    height:0;
}

/* ---------- Mobile ---------- */
@media (max-width: 768px) {
    .block-container {
        padding: 1.1rem .8rem 6rem;
    }

    .hero h1 {
        font-size:38px;
        letter-spacing:-1.7px;
    }

    .welcome-card {
        padding:24px 17px;
        border-radius:20px;
    }

    [data-testid="stChatMessage"] {
        padding:13px;
        border-radius:17px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# HELPERS
# ============================================================
def get_secret(key_path: List[str], default=None):
    """Try Streamlit secrets, then environment variable."""
    try:
        node = st.secrets
        for key in key_path:
            node = node[key]
        return node
    except Exception:
        env_key = "_".join(key_path).upper()
        return os.getenv(env_key, default)


GROQ_API_KEY = (
    get_secret(["groq", "api_key"], None)
    or os.getenv("GROQ_API_KEY")
    or GROQ_API_KEY_HARDCODED
)


def register_font():
    """Register Devanagari TTF if available."""
    try:
        if os.path.isfile(FONT_PATH):
            pdfmetrics.registerFont(TTFont("NotoDeva", FONT_PATH))
            return "NotoDeva"
    except Exception:
        pass
    return None


def safe_pdf_text(text: str) -> str:
    """Make chat text safer for ReportLab Paragraph."""
    text = str(text or "")
    text = html.escape(text)
    text = text.replace("\n", "<br/>")
    return text


def create_chat_pdf_bytes(messages: List[Dict], title: str = "DSA Chat History") -> bytes:
    font_name = register_font()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    if font_name:
        base_style = ParagraphStyle(
            "BasePremium",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#22252b"),
        )
        title_style = ParagraphStyle(
            "TitlePremium",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=17,
            leading=21,
            alignment=TA_LEFT,
        )
    else:
        base_style = styles["Normal"]
        title_style = styles["Title"]

    story = [
        Paragraph(safe_pdf_text(title), title_style),
        Spacer(1, 6),
        Paragraph(
            safe_pdf_text(
                f"Exported on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ),
            base_style,
        ),
        Spacer(1, 10),
    ]

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        created_at = msg.get("created_at", "")

        label = "<b>You:</b> " if role == "user" else "<b>DSA Dost:</b> "
        timestamp = (
            f' <font size="8" color="grey">({html.escape(created_at)})</font>'
            if created_at
            else ""
        )

        story.append(
            Paragraph(
                f"{label}{safe_pdf_text(content)}{timestamp}",
                base_style,
            )
        )
        story.append(Spacer(1, 7))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def initialize_state():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "quick_prompt" not in st.session_state:
        st.session_state.quick_prompt = None


def reset_chat():
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.quick_prompt = None


def add_message(role: str, content: str):
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def prepare_pdf_messages():
    return [
        {
            "role": m.get("role"),
            "content": m.get("content"),
            "created_at": m.get("created_at", ""),
        }
        for m in st.session_state.get("messages", [])
    ]


def get_pdf_bytes_for_download():
    return create_chat_pdf_bytes(
        prepare_pdf_messages(),
        title="DSA Dost — Chat Export",
    )


def set_quick_prompt(prompt: str):
    st.session_state.quick_prompt = prompt


# ============================================================
# INITIALIZE
# ============================================================
initialize_state()

if not GROQ_API_KEY:
    st.error(
        "GROQ_API_KEY is not set. Add it to Streamlit secrets "
        "or set the GROQ_API_KEY environment variable."
    )
    st.stop()

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Failed to initialize Groq client: {e}")
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-logo">🤖</div>
            <div>
                <div class="brand-title">DSA Dost</div>
                <div class="brand-subtitle">AI Learning Assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("＋  New Chat", use_container_width=True):
        reset_chat()
        st.rerun()

    st.markdown('<div class="sidebar-section">Tools</div>', unsafe_allow_html=True)

    st.download_button(
        label="📄  Export Chat as PDF",
        data=get_pdf_bytes_for_download(),
        file_name="dsa_dost_chat.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    if st.button("🗑  Clear Conversation", use_container_width=True):
        reset_chat()
        st.rerun()

    st.markdown('<div class="sidebar-section">Current Session</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="sidebar-info">
            <strong>Session active</strong><br>
            Your chat is stored temporarily in this browser session.<br><br>
            <span style="color:#667085;">ID:</span>
            <span style="font-family:monospace;color:#8d96a8;">
                {html.escape(st.session_state.session_id[:12])}...
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sidebar-footer">
            DSA Dost v1.0<br>
            Python · Streamlit · Groq
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HERO
# ============================================================
st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">
            <span class="online-dot"></span>
            AI ASSISTANT ONLINE
        </div>
        <h1>DSA Dost</h1>
        <p>Your intelligent companion for Data Structures & Algorithms.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# WELCOME / QUICK PROMPTS
# ============================================================
if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome-card">
            <div class="welcome-icon">🤖</div>
            <h2>Let's master DSA together.</h2>
            <p>
                Ask a concept, understand an algorithm, solve an interview problem,
                or get clean C++ code with complexity analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="prompt-label">Start with a popular topic</div>', unsafe_allow_html=True)

    prompt_data = [
        ("🔍", "Binary Search", "Explain Binary Search simply.", "Learn searching"),
        ("↕️", "Sorting", "Explain Merge Sort with example and complexity.", "Master algorithms"),
        ("🌳", "Trees", "Explain Binary Tree and its traversals.", "Understand trees"),
        ("⚡", "Interview Practice", "Give me 5 medium DSA interview questions.", "Practice problems"),
    ]

    cols = st.columns(4, gap="small")

    for col, (icon, title, prompt, subtitle) in zip(cols, prompt_data):
        with col:
            st.markdown(
                f"""
                <div class="prompt-card">
                    <div class="prompt-icon">{icon}</div>
                    <div class="prompt-title">{title}</div>
                    <div class="prompt-sub">{subtitle}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Ask this →",
                key=f"prompt_{title}",
                use_container_width=True,
            ):
                set_quick_prompt(prompt)
                st.rerun()

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)


# ============================================================
# CHAT HISTORY
# ============================================================
for message in st.session_state.messages:
    avatar = "🤖" if message["role"] == "assistant" else "🧑‍💻"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


# ============================================================
# INPUT
# ============================================================
typed_prompt = st.chat_input("Ask your DSA question...")

prompt = st.session_state.quick_prompt or typed_prompt

if prompt:
    st.session_state.quick_prompt = None

    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_message("user", prompt)

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    conversation_history = []

    for msg in st.session_state.messages[-MAX_HISTORY:]:
        if msg["role"] in ["user", "assistant"]:
            conversation_history.append(
                {
                    "role": msg["role"],
                    "content": msg["content"],
                }
            )

    groq_messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + conversation_history

    try:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("DSA Dost is thinking..."):
                chat_completion = groq_client.chat.completions.create(
                    messages=groq_messages,
                    model=GROQ_MODEL,
                )

                ai_response = chat_completion.choices[0].message.content
                st.markdown(ai_response)

        add_message("assistant", ai_response)

    except Exception as e:
        error_text = (
            "Sorry, response fetch nahi ho paya. Please try again."
        )

        with st.chat_message("assistant", avatar="🤖"):
            st.error(f"Groq error: {e}")
            st.markdown(error_text)

        add_message("assistant", error_text)


# ============================================================
# FOOTER
# ============================================================
st.markdown(
    """
    <div class="app-footer">
        DSA Dost &nbsp;•&nbsp; Built with Python + Streamlit + Groq
    </div>
    """,
    unsafe_allow_html=True,
)