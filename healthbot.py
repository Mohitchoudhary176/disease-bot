import streamlit as st
import openai
import os
import sqlite3
from datetime import datetime

# ---------- CONFIG ----------
# Use Streamlit secrets or environment variable for key
OPENAI_KEY = None
if "OPENAI_API_KEY" in st.secrets:
    OPENAI_KEY = st.secrets["sk-proj-yoMf3e-pD-ZsBoFYVfO3Q_-MshfMRONeqLga9RBtzjJEHwz580VU8vimQm-pE9aa2vcnihhvmIT3BlbkFJCIF8SaOgvISoBeOlgWjJLOS9FXNNZfIPxOjhtt1zX5X5X-OJ0ktiGbCKYjbdmG2lyz3Ic_ER0Astreamlit run healthbot.pyY"]
else:
    OPENAI_KEY = os.environ.get("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")

if not OPENAI_KEY:
    st.error("OpenAI API key not found. Add OPENAI_API_KEY in Streamlit Secrets or environment.")
    st.stop()

openai.api_key = OPENAI_KEY

DB_PATH = "chat_history.db"   # SQLite file

# ---------- DB HELPERS ----------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def save_message(conn, role, content):
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)",
                (role, content, datetime.utcnow().isoformat()))
    conn.commit()

def load_history(conn, limit=None):
    cur = conn.cursor()
    if limit:
        cur.execute("SELECT role, content FROM messages ORDER BY id ASC LIMIT ?", (limit,))
    else:
        cur.execute("SELECT role, content FROM messages ORDER BY id ASC")
    rows = cur.fetchall()
    return [{"role": r[0], "content": r[1]} for r in rows]

# ---------- INITIALIZE ----------
conn = init_db()

st.set_page_config(page_title="Smart Health Chat Bot", page_icon="🤖", layout="centered")
st.title("🤖 Smart Health Chat Bot (English + Hinglish)")

# sidebar buttons
with st.sidebar:
    st.markdown("**Options**")
    if st.button("Clear local history"):
        cur = conn.cursor()
        cur.execute("DELETE FROM messages")
        conn.commit()
        st.info("Local history cleared. Reload the page.")
        st.experimental_rerun()
    st.markdown("---")
    st.markdown("**Note:** This app saves chat history to `chat_history.db` in app folder.")
    st.markdown("On Streamlit Cloud the file persists until you redeploy. For permanent persistence use an external DB.")

# load history from DB into session_state for fast display
if "loaded" not in st.session_state:
    st.session_state.history = load_history(conn)
    # If DB empty, add system prompt at start (stored too)
    if not st.session_state.history:
        system_msg = {
            "role": "system",
            "content": (
                "You are a friendly health assistant. Reply in simple English + Hinglish. "
                "Be concise, ask follow-up questions when needed. Always include a short reminder that you're not a doctor."
            )
        }
        save_message(conn, "system", system_msg["content"])
        st.session_state.history = [system_msg]
    st.session_state.loaded = True

# Show chat history
chat_placeholder = st.container()
with chat_placeholder:
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        elif msg["role"] == "assistant":
            st.chat_message("assistant").markdown(msg["content"])
        else:  # system or others
            st.markdown(f"**System:** {msg['content']}")

# --- File uploader
uploaded = st.file_uploader("Upload report (jpg/png/pdf) — optional", type=["jpg", "png", "jpeg", "pdf"])
if uploaded:
    st.image(uploaded, caption="Uploaded file", use_column_width=True)
    # read bytes (we'll send base64 for vision-capable models if needed)
    file_bytes = uploaded.read()
    # add a short user message indicating they uploaded file
    file_note = f"[Uploaded file: {uploaded.name}]"
    save_message(conn, "user", file_note)
    st.session_state.history.append({"role": "user", "content": file_note})
    # For vision analysis: send a text prompt + the textual note (actual image embedding/vision model usage varies by SDK)
    # We'll ask OpenAI to explain the image using a simple prompt (you can enhance if you have vision-enabled model)
    prompt = f"User uploaded a medical report image named {uploaded.name}. Explain likely findings in simple English + Hinglish, and remind user it's not a diagnosis."
    save_message(conn, "user", prompt)
    st.session_state.history.append({"role": "user", "content": prompt})

    # Call OpenAI ChatCompletion
    try:
        # Using ChatCompletion (legacy openai API)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.history[-12:],  # send last messages to limit tokens
            max_tokens=400,
            temperature=0.7
        )
        bot_reply = response.choices[0].message["content"].strip()
        save_message(conn, "assistant", bot_reply)
        st.session_state.history.append({"role": "assistant", "content": bot_reply})
        st.experimental_rerun()
    except Exception as e:
        st.error("Error calling OpenAI for image analysis: " + str(e))

# --- text input
user_text = st.chat_input("Type your message here... (English or Hinglish)")

if user_text:
    # Save and show user message
    save_message(conn, "user", user_text)
    st.session_state.history.append({"role": "user", "content": user_text})
    st.chat_message("user").markdown(user_text)

    # Build messages to send: we include the stored conversation but limit length (to control tokens)
    full_messages = load_history(conn)
    # Convert to OpenAI format (role/content)
    messages_for_api = [{"role": m["role"], "content": m["content"]} for m in full_messages]
    # Keep last N messages to avoid huge context
    if len(messages_for_api) > 20:
        messages_for_api = messages_for_api[-20:]

    # Call OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_for_api,
            max_tokens=250,
            temperature=0.7
        )
        bot_reply = response.choices[0].message["content"].strip()
    except Exception as e:
        bot_reply = "Sorry, I couldn't reach the AI service. Try again later."
        st.error(str(e))

    # Save assistant reply
    save_message(conn, "assistant", bot_reply)
    st.session_state.history.append({"role": "assistant", "content": bot_reply})
    st.chat_message("assistant").markdown(bot_reply)






