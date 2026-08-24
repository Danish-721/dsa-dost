import datetime
import html
import io
import os
import uuid
from typing import Dict, List, Optional

import requests
import streamlit as st

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="DSA Dost — AI DSA Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv(
    "DJANGO_API_BASE_URL",
    "http://127.0.0.1:8000/api",
).rstrip("/")

TOKEN_URL = os.getenv(
    "DJANGO_TOKEN_URL",
    f"{API_BASE_URL}/auth/token/",
)

REGISTER_URL = os.getenv(
    "DJANGO_REGISTER_URL",
    f"{API_BASE_URL}/auth/register/",
)

REQUEST_TIMEOUT = 60
MAX_HISTORY = 12

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONT_PATH = os.path.join(FONT_DIR, "NotoSansDevanagari-Regular.ttf")


# ============================================================
# UI CSS
# ============================================================

st.markdown(
    """
<style>
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

.conversation-button-wrap {
    margin-bottom: 7px;
}

.active-chat-note {
    color: #8b5cf6;
    font-size: 9px;
    margin: -3px 0 7px 10px;
}

.sidebar-footer {
    color:#596274;
    font-size:10px;
    line-height:1.6;
    padding: 20px 0 4px;
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

.hero h1 .wave {
    -webkit-text-fill-color: initial;
    color: #facc15;
    background: none;
    -webkit-background-clip: initial;
    background-clip: initial;
    display: inline-block;
}

.hero p {
    color:#8f98aa;
    margin:0 auto;
    font-size:14px;
}

.chat-title {
    text-align:center;
    color:#e9edf5;
    font-size:14px;
    font-weight:700;
    margin: 0 auto 12px;
}

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

[data-testid="stChatMessage"] pre {
    border:1px solid rgba(255,255,255,.08);
    border-radius:13px;
    background:#0a0d14 !important;
}

[data-testid="stChatMessage"] pre code {
    font-size:12px !important;
    line-height:1.65 !important;
}

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

.soft-divider {
    height:1px;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,.08),transparent);
    margin:20px 0;
}

.app-footer {
    text-align:center;
    color:#50596a;
    font-size:10px;
    padding:18px 0 4px;
}

.login-card {
    max-width: 440px;
    margin: 8vh auto 0;
    padding: 30px;
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,.085);
    background:
        radial-gradient(circle at 20% 10%, rgba(124,58,237,.12), transparent 35%),
        linear-gradient(135deg, rgba(255,255,255,.045), rgba(255,255,255,.018));
    box-shadow: 0 25px 80px rgba(0,0,0,.25);
}

.login-title {
    text-align:center;
    font-size:30px;
    font-weight:800;
    margin-bottom:6px;
}

.login-subtitle {
    text-align:center;
    color:#8f98aa;
    font-size:13px;
    margin-bottom:24px;
}

#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header[data-testid="stHeader"] { height:0; }

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
# SESSION STATE
# ============================================================

def initialize_state():
    defaults = {
        "access_token": None,
        "refresh_token": None,
        "username": None,
        "auth_mode": "login",
        "login_username": "",
        "conversation_id": None,
        "conversation_title": "New Chat",
        "conversations": [],
        "messages": [],
        "quick_prompt": None,
        "session_id": str(uuid.uuid4()),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()


# ============================================================
# API HELPERS
# ============================================================

def api_headers() -> Dict[str, str]:
    token = st.session_state.get("access_token")
    headers = {
        "Content-Type": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def handle_auth_failure(response):
    if response.status_code in (401, 403):
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.username = None
        st.session_state.conversation_id = None
        st.session_state.conversation_title = "New Chat"
        st.session_state.messages = []
        st.session_state.conversations = []
        return True

    return False


def api_request(
    method: str,
    endpoint: str,
    *,
    json: Optional[dict] = None,
    timeout: int = REQUEST_TIMEOUT,
):
    url = f"{API_BASE_URL}/{endpoint.strip('/')}/"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=api_headers(),
            json=json,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        st.error(
            "Django backend se connection nahi ho pa raha. "
            f"Backend running hai ya nahi check karo.\n\n{exc}"
        )
        return None

    if handle_auth_failure(response):
        st.rerun()

    return response


def login_user(username: str, password: str) -> bool:
    try:
        response = requests.post(
            TOKEN_URL,
            json={
                "username": username,
                "password": password,
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        st.error(f"Django backend se connection nahi ho pa raha: {exc}")
        return False

    if response.status_code != 200:
        try:
            detail = response.json()
        except Exception:
            detail = response.text

        st.error(f"Login failed: {detail}")
        return False

    data = response.json()

    st.session_state.access_token = data.get("access")
    st.session_state.refresh_token = data.get("refresh")
    st.session_state.username = username

    return bool(st.session_state.access_token)


def register_user(
    username: str,
    email: str,
    password: str,
    password2: str,
) -> bool:
    try:
        response = requests.post(
            REGISTER_URL,
            json={
                "username": username,
                "email": email,
                "password": password,
                "password2": password2,
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        st.error(f"Django backend se connection nahi ho pa raha: {exc}")
        return False

    if response.status_code not in (200, 201):
        try:
            detail = response.json()
        except Exception:
            detail = response.text

        # DRF validation errors are usually dictionaries such as:
        # {"username": [...], "password": [...], ...}
        if isinstance(detail, dict):
            messages = []
            for field, errors in detail.items():
                if isinstance(errors, list):
                    error_text = " ".join(str(item) for item in errors)
                else:
                    error_text = str(errors)
                messages.append(f"{field}: {error_text}")
            st.error("Registration failed — " + " | ".join(messages))
        else:
            st.error(f"Registration failed: {detail}")

        return False

    return True


def logout_user():
    for key in [
        "access_token",
        "refresh_token",
        "username",
        "auth_mode",
        "login_username",
        "conversation_id",
        "conversation_title",
        "conversations",
        "messages",
        "quick_prompt",
    ]:
        if key in st.session_state:
            st.session_state[key] = None if key in [
                "access_token",
                "refresh_token",
                "username",
                "conversation_id",
                "quick_prompt",
            ] else (
                [] if key in ["conversations", "messages"]
                else ("login" if key == "auth_mode" else "")
                if key == "login_username"
                else "New Chat"
            )

    st.session_state.session_id = str(uuid.uuid4())


def fetch_conversations() -> List[dict]:
    response = api_request("GET", "conversations")

    if response is None:
        return []

    if response.status_code != 200:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        st.error(f"Conversations load nahi hui: {detail}")
        return []

    data = response.json()

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and "results" in data:
        return data["results"]

    return []


def create_conversation(title: str = "New Chat") -> Optional[dict]:
    response = api_request(
        "POST",
        "conversations",
        json={"title": title},
    )

    if response is None:
        return None

    if response.status_code not in (200, 201):
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        st.error(f"Conversation create nahi hui: {detail}")
        return None

    return response.json()


def fetch_conversation(conversation_id: int) -> Optional[dict]:
    response = api_request(
        "GET",
        f"conversations/{conversation_id}",
    )

    if response is None:
        return None

    if response.status_code != 200:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        st.error(f"Conversation load nahi hui: {detail}")
        return None

    return response.json()


def delete_conversation(conversation_id: int) -> bool:
    response = api_request(
        "DELETE",
        f"conversations/{conversation_id}",
    )

    if response is None:
        return False

    if response.status_code not in (200, 202, 204):
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        st.error(f"Conversation delete nahi hui: {detail}")
        return False

    return True


def send_message_to_backend(
    conversation_id: int,
    content: str,
) -> Optional[dict]:
    response = api_request(
        "POST",
        f"conversations/{conversation_id}/messages",
        json={"content": content},
    )

    if response is None:
        return None

    if response.status_code not in (200, 201):
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        st.error(f"Message send nahi hua: {detail}")
        return None

    return response.json()


# ============================================================
# CONVERSATION STATE HELPERS
# ============================================================

def normalize_messages(messages) -> List[dict]:
    normalized = []

    for message in messages or []:
        normalized.append(
            {
                "id": message.get("id"),
                "role": message.get("role", "user"),
                "content": message.get("content", ""),
                "model_used": message.get("model_used"),
                "provider": message.get("provider"),
                "fallback_used": message.get("fallback_used", False),
                "created_at": message.get("created_at", ""),
            }
        )

    return normalized


def load_conversation(conversation_id: int):
    conversation = fetch_conversation(conversation_id)

    if not conversation:
        return

    st.session_state.conversation_id = conversation.get("id")
    st.session_state.conversation_title = (
        conversation.get("title") or "New Chat"
    )
    st.session_state.messages = normalize_messages(
        conversation.get("messages", [])
    )
    st.session_state.quick_prompt = None


def start_new_chat():
    conversation = create_conversation("New Chat")

    if not conversation:
        return

    st.session_state.conversation_id = conversation.get("id")
    st.session_state.conversation_title = (
        conversation.get("title") or "New Chat"
    )
    st.session_state.messages = []
    st.session_state.quick_prompt = None

    st.session_state.conversations = fetch_conversations()


def refresh_conversations():
    st.session_state.conversations = fetch_conversations()


def make_sidebar_title(title: str) -> str:
    title = str(title or "New Chat").strip()

    if len(title) > 34:
        return title[:34].rstrip() + "..."

    return title


def add_local_message(
    role: str,
    content: str,
    message_data: Optional[dict] = None,
):
    if message_data:
        st.session_state.messages.append(
            {
                "id": message_data.get("id"),
                "role": message_data.get("role", role),
                "content": message_data.get("content", content),
                "model_used": message_data.get("model_used"),
                "provider": message_data.get("provider"),
                "fallback_used": message_data.get(
                    "fallback_used",
                    False,
                ),
                "created_at": message_data.get(
                    "created_at",
                    datetime.datetime.now().isoformat(),
                ),
            }
        )
    else:
        st.session_state.messages.append(
            {
                "id": None,
                "role": role,
                "content": content,
                "model_used": None,
                "provider": None,
                "fallback_used": False,
                "created_at": datetime.datetime.now().isoformat(),
            }
        )


# ============================================================
# PDF HELPERS
# ============================================================

def register_font():
    try:
        if os.path.isfile(FONT_PATH):
            pdfmetrics.registerFont(
                TTFont("NotoDeva", FONT_PATH)
            )
            return "NotoDeva"
    except Exception:
        pass

    return None


def safe_pdf_text(text: str) -> str:
    text = str(text or "")
    text = html.escape(text)
    text = text.replace("\n", "<br/>")
    return text


def create_chat_pdf_bytes(
    messages: List[Dict],
    title: str = "DSA Chat History",
) -> bytes:
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
                "Exported on: "
                + datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ),
            base_style,
        ),
        Spacer(1, 10),
    ]

    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        created_at = message.get("created_at", "")

        label = (
            "<b>You:</b> "
            if role == "user"
            else "<b>DSA Dost:</b> "
        )

        timestamp = (
            f' <font size="8" color="grey">'
            f"({html.escape(str(created_at))})"
            f"</font>"
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


def get_pdf_bytes_for_download():
    return create_chat_pdf_bytes(
        st.session_state.get("messages", []),
        title=st.session_state.get(
            "conversation_title",
            "DSA Dost — Chat Export",
        ),
    )


# ============================================================
# LOGIN / REGISTER SCREEN
# ============================================================

if not st.session_state.get("access_token"):
    st.markdown(
        """
        <div class="login-card">
            <div class="welcome-icon">🤖</div>
            <div class="login-title">DSA Dost</div>
            <div class="login-subtitle">
                Learn DSA, practice problems and keep your conversations saved.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(["🔐 Login", "✨ Create Account"])

    with login_tab:
        st.markdown("### Welcome back")
        st.caption("Sign in to access your saved conversations.")

        with st.form("login_form"):
            username = st.text_input(
                "Username",
                value=st.session_state.get("login_username", ""),
                placeholder="Enter your Django username",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True,
            )

        if submitted:
            username = username.strip()

            if not username or not password:
                st.warning("Username aur password dono enter karo.")
            elif login_user(username, password):
                st.session_state.login_username = username
                refresh_conversations()
                st.rerun()

    with register_tab:
        st.markdown("### Create your account")
        st.caption("Create a free account to save and revisit your DSA chats.")

        with st.form("register_form"):
            new_username = st.text_input(
                "Username",
                placeholder="Choose a username",
            )

            new_email = st.text_input(
                "Email",
                placeholder="you@example.com",
            )

            new_password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a strong password",
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
            )

            register_submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True,
            )

        if register_submitted:
            new_username = new_username.strip()
            new_email = new_email.strip()

            if not new_username or not new_email or not new_password or not confirm_password:
                st.warning("Username, email aur dono password fields fill karo.")
            elif new_password != confirm_password:
                st.warning("Passwords do not match.")
            elif register_user(
                new_username,
                new_email,
                new_password,
                confirm_password,
            ):
                st.session_state.login_username = new_username
                st.success(
                    "Account successfully create ho gaya! "
                    "Ab Login tab se sign in karo."
                )

    st.stop()


# INITIAL CONVERSATION LOAD
# ============================================================

if not st.session_state.conversations:
    st.session_state.conversations = fetch_conversations()

if (
    st.session_state.conversation_id is None
    and st.session_state.conversations
):
    first_conversation = st.session_state.conversations[0]
    load_conversation(first_conversation["id"])


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

    if st.button(
        "＋  New Chat",
        use_container_width=True,
        key="new_chat_button",
    ):
        start_new_chat()
        st.rerun()

    st.markdown(
        '<div class="sidebar-section">Conversations</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.conversations:
        st.caption("No conversations yet.")

    for conversation in st.session_state.conversations:
        conversation_id = conversation.get("id")
        title = make_sidebar_title(
            conversation.get("title") or "New Chat"
        )

        is_active = (
            conversation_id
            == st.session_state.conversation_id
        )

        button_label = (
            f"🟣 {title}"
            if is_active
            else f"💬 {title}"
        )

        if st.button(
            button_label,
            key=f"conversation_{conversation_id}",
            use_container_width=True,
        ):
            load_conversation(conversation_id)
            st.rerun()

    st.markdown(
        '<div class="sidebar-section">Tools</div>',
        unsafe_allow_html=True,
    )

    st.download_button(
        label="📄  Export Chat as PDF",
        data=get_pdf_bytes_for_download(),
        file_name="dsa_dost_chat.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="export_pdf",
    )

    if st.button(
        "🗑  Delete Current Chat",
        use_container_width=True,
        key="delete_chat",
    ):
        current_id = st.session_state.get("conversation_id")

        if current_id is None:
            st.warning("No active conversation.")
        else:
            if delete_conversation(current_id):
                st.session_state.conversation_id = None
                st.session_state.conversation_title = "New Chat"
                st.session_state.messages = []
                st.session_state.conversations = fetch_conversations()

                if st.session_state.conversations:
                    load_conversation(
                        st.session_state.conversations[0]["id"]
                    )

                st.rerun()

    st.markdown(
        '<div class="sidebar-section">Account</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="sidebar-info">
            <strong>{html.escape(str(st.session_state.username or ""))}</strong><br>
            Django authentication active.<br><br>
            <span style="color:#667085;">Conversation ID:</span>
            <span style="font-family:monospace;color:#8d96a8;">
                {html.escape(str(st.session_state.conversation_id or "—"))}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "↪ Logout",
        use_container_width=True,
        key="logout_button",
    ):
        logout_user()
        st.rerun()

    st.markdown(
        """
        <div class="sidebar-footer">
            DSA Dost v2.0<br>
            Streamlit · Django REST Framework · Groq
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN HERO
# ============================================================

username = html.escape(
    str(st.session_state.get("username") or "there")
)

st.markdown(
f"""<div class="hero">
<div class="hero-badge">
<span class="online-dot"></span>
AI ASSISTANT ONLINE
</div>
<h1>Welcome back, {username} <span class="wave">👋</span></h1>
<p>Your intelligent companion for Data Structures & Algorithms.</p>
</div>""",
unsafe_allow_html=True,
)

if st.session_state.conversation_id:
    st.markdown(
        f"""
        <div class="chat-title">
            💬 {html.escape(
                st.session_state.conversation_title or "New Chat"
            )}
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

    st.markdown(
        '<div class="prompt-label">Start with a popular topic</div>',
        unsafe_allow_html=True,
    )

    prompt_data = [
        (
            "🔍",
            "Binary Search",
            "Explain Binary Search simply.",
            "Learn searching",
        ),
        (
            "↕️",
            "Sorting",
            "Explain Merge Sort with example and complexity.",
            "Master algorithms",
        ),
        (
            "🌳",
            "Trees",
            "Explain Binary Tree and its traversals.",
            "Understand trees",
        ),
        (
            "⚡",
            "Interview Practice",
            "Give me 5 medium DSA interview questions.",
            "Practice problems",
        ),
    ]

    cols = st.columns(4, gap="small")

    for col, (icon, title, prompt, subtitle) in zip(
        cols,
        prompt_data,
    ):
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
                st.session_state.quick_prompt = prompt
                st.rerun()

    st.markdown(
        '<div class="soft-divider"></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:
    role = message.get("role", "assistant")

    avatar = (
        "🤖"
        if role == "assistant"
        else "🧑‍💻"
    )

    with st.chat_message(role, avatar=avatar):
        st.markdown(message.get("content", ""))


# ============================================================
# INPUT
# ============================================================

typed_prompt = st.chat_input(
    "Ask your DSA question..."
)

prompt = (
    st.session_state.quick_prompt
    or typed_prompt
)

if prompt:
    st.session_state.quick_prompt = None

    # Safety: a chat must have a backend conversation.
    if st.session_state.conversation_id is None:
        new_conversation = create_conversation("New Chat")

        if not new_conversation:
            st.error(
                "Conversation create nahi hui. "
                "Please try again."
            )
            st.stop()

        st.session_state.conversation_id = (
            new_conversation.get("id")
        )

        st.session_state.conversation_title = (
            new_conversation.get("title")
            or "New Chat"
        )

    # Show user message immediately.
    with st.chat_message(
        "user",
        avatar="🧑‍💻",
    ):
        st.markdown(prompt)

    try:
        with st.chat_message(
            "assistant",
            avatar="🤖",
        ):
            with st.spinner(
                "DSA Dost is thinking..."
            ):
                result = send_message_to_backend(
                    st.session_state.conversation_id,
                    prompt,
                )

                if not result:
                    st.error(
                        "Response fetch nahi ho paya. "
                        "Please try again."
                    )
                else:
                    user_message = result.get(
                        "user_message"
                    )
                    assistant_message = result.get(
                        "assistant_message"
                    )

                    if assistant_message:
                        st.markdown(
                            assistant_message.get(
                                "content",
                                "",
                            )
                        )

                    # Replace local history with the canonical
                    # response returned by Django.
                    if user_message:
                        add_local_message(
                            "user",
                            prompt,
                            user_message,
                        )

                    if assistant_message:
                        add_local_message(
                            "assistant",
                            assistant_message.get(
                                "content",
                                "",
                            ),
                            assistant_message,
                        )

        # Reload the conversation so the title and message
        # history are exactly what Django has stored.
        conversation = fetch_conversation(
            st.session_state.conversation_id
        )

        if conversation:
            st.session_state.conversation_title = (
                conversation.get("title")
                or st.session_state.conversation_title
                or "New Chat"
            )

            st.session_state.messages = (
                normalize_messages(
                    conversation.get("messages", [])
                )
            )

        st.session_state.conversations = (
            fetch_conversations()
        )

        st.rerun()

    except Exception as exc:
        st.error(
            f"Unexpected error: {exc}"
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="app-footer">
        DSA Dost &nbsp;•&nbsp;
        Streamlit + Django REST Framework + Groq
    </div>
    """,
    unsafe_allow_html=True,
)
