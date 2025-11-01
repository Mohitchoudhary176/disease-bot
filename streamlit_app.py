# streamlit_app.py
import os
import base64
import json
from io import BytesIO
import streamlit as st
from openai import OpenAI
from PIL import Image
from fpdf import FPDF
import datetime

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Full Medical Assistant", layout="wide")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    st.error("OPENAI_API_KEY not found. Add it in Streamlit Secrets and restart the app.")
    st.stop()

client = OpenAI(api_key=OPENAI_KEY)

# -------------------------
# Helpers
# -------------------------
HISTORY_FILE = "chat_history.json"

def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    # default system prompt
    return [
        {"role":"system","content":(
            "You are a friendly medical assistant. Reply simply and clearly in English or Hinglish. "
            "When asked symptoms, provide: most likely condition (with a risk percent), other possible causes, "
            "recommended tests, safe home-care steps, warning signs, and whether to see a doctor. "
            "Always include a short disclaimer: this is educational and not a diagnosis. "
        )}
    ]

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def encode_image_to_dataurl(file_bytes, mime):
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def create_pdf_report(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    lines = text.split("\n")
    for line in lines:
        pdf.multi_cell(0, 8, txt=line)
    filename = f"medical_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

# -------------------------
# UI: sidebar settings
# -------------------------
st.sidebar.title("Settings")
child_mode = st.sidebar.checkbox("Child-friendly mode (simpler language)", value=False)
language = st.sidebar.selectbox("Preferred reply language", ["English", "Hinglish", "Both"])
include_hospitals = st.sidebar.checkbox("Include nearby hospitals (template)", value=False)
# (Optional) city input for hospitals (used if include_hospitals True)
city_for_hospitals = st.sidebar.text_input("City for hospital list (optional)", value="")

st.sidebar.markdown("---")
st.sidebar.info("This app provides educational information only. Not a medical diagnosis.")

# -------------------------
# Load or initialize conversation history
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# top header
st.title("🩺 AI Medical Assistant — full features")
st.caption("Symptoms → probable condition + risk% • Image analysis • Voice transcription • PDF report")

# layout: left chat, right controls
left_col, right_col = st.columns([3,1])

# -------------------------
# RIGHT: upload / tools
# -------------------------
with right_col:
    st.header("Tools")
    # Image upload
    uploaded_image = st.file_uploader("Upload image/report (jpg/png/pdf)", type=["jpg","png","jpeg","pdf"])
    # Audio upload (voice input)
    uploaded_audio = st.file_uploader("Upload audio (voice) to transcribe (mp3/wav/m4a)", type=["mp3","wav","m4a","ogg"])
    st.markdown("---")
    if include_hospitals:
        st.info("Hospital list included in PDF as a template. To fetch real nearby hospitals, add Google Places API and call it in backend.")
    st.markdown("**Export**")
    if st.button("Download full chat as JSON"):
        st.download_button("Download JSON", data=json.dumps(st.session_state.messages, ensure_ascii=False, indent=2), file_name="chat_history.json")
    st.markdown("")

# -------------------------
# LEFT: chat area
# -------------------------
with left_col:
    # Display chat history with bubbles
    for m in st.session_state.messages[1:]:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "user":
            st.markdown(f"<div style='text-align:right;background:#DCF8C6;padding:8px;border-radius:8px;margin:6px 0'>{content}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:left;background:#E8EAF6;padding:8px;border-radius:8px;margin:6px 0'>{content}</div>", unsafe_allow_html=True)

    # Input
    user_text = st.chat_input("Describe your symptoms or ask a question (or upload image/audio on the right).")

    # If audio uploaded: transcribe first
    if uploaded_audio:
        st.info("Transcribing audio...")
        audio_bytes = uploaded_audio.read()
        # Use OpenAI transcription endpoint (new SDK); if not available, ask user to paste transcript
        try:
            # Save to temp file
            tmp_name = f"temp_audio_{datetime.datetime.now().timestamp()}.mp3"
            with open(tmp_name, "wb") as af:
                af.write(audio_bytes)
            # Using new OpenAI API for transcription
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-transcribe", # may vary; fallback to "whisper-1" if not available
                file=open(tmp_name, "rb")
            )
            text_transcribed = transcription.text if hasattr(transcription, "text") else transcription["text"]
            st.success("Transcription complete. Transcribed text added to input box.")
            # Set user_text if empty
            if not user_text:
                user_text = text_transcribed
        except Exception as e:
            st.warning("Automatic transcription failed — please paste transcript manually.")
            st.exception(e)

    # If image uploaded: show preview and prepare description prompt
    image_dataurl = None
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded file preview", use_column_width=True)
        try:
            # read bytes and prepare data url
            file_bytes = uploaded_image.read()
            mime = uploaded_image.type or "image/jpeg"
            image_dataurl = encode_image_to_dataurl(file_bytes, mime)
        except Exception:
            pass

    # When user submits text (or transcription filled)
    if user_text:
        # Build language/system modifiers
        system_extra = ""
        if child_mode:
            system_extra += " Use very simple and gentle language suitable for explaining to a child.\n"
        if language == "Hinglish":
            system_extra += " Reply in Hinglish.\n"
        elif language == "Both":
            system_extra += " Reply in both simple English and short Hinglish sentences.\n"

        # Append user message to session history (user)
        st.session_state.messages.append({"role":"user","content": user_text})

        # If image present, insert an assistant-user message describing we have image
        if image_dataurl:
            # attach an explicit image note to conversation so model can refer
            st.session_state.messages.append({"role":"user","content":"I have uploaded an image/report (see file). Please analyze it along with the symptoms."})
            # We will pass the image as inline base64 data inside the assistant request below.

        # Prepare messages to send: start with system + history, but override system prompt with child/language
        messages_to_send = []
        # base system prompt
        base_system = (
            "You are a friendly, careful medical assistant. "
            "When given symptoms, return:\n"
            "1) Most likely condition with a probability (0-100%)\n"
            "2) Short explanation why\n"
            "3) Other possible causes\n"
            "4) Recommended simple tests\n"
            "5) Safe home-care steps\n"
            "6) Warning signs that need immediate medical attention\n"
            "7) Short list of medicines doctors commonly prescribe (general, non-prescriptive)\n"
            "8) A short one-line disclaimer: this is educational and not a diagnosis."
        )
        base_system += system_extra
        messages_to_send.append({"role":"system","content": base_system})

        # Append the prior conversation messages except original system
        for m in st.session_state.messages[1:]:
            messages_to_send.append({"role": m["role"], "content": m["content"]})

        # If image_dataurl exists: attach a short instruction with data url
        if image_dataurl:
            # Note: the OpenAI model must support vision or the model will ignore the data URL.
            # We include the image as a data URL for models that can parse it; if not, model should at least describe what to look for.
            messages_to_send.append({"role":"user","content": f"Attached image (data URL): {image_dataurl}\nPlease analyze visible findings and relate to symptoms."})

        # Call OpenAI Chat Completions (new API)
        try:
            with st.spinner("Analyzing — this may take a few seconds..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # use the model you have access to; gpt-4o-mini recommended
                    messages=messages_to_send,
                    temperature=0.6,
                    max_tokens=600
                )
                bot_reply = response.choices[0].message.content
        except Exception as e:
            st.error("API error: " + str(e))
            bot_reply = "Sorry, I couldn't reach the AI service. Try again in a moment."

        # Append bot reply to history
        st.session_state.messages.append({"role":"assistant","content": bot_reply})

        # Display the bot reply
        st.experimental_rerun()

# -------------------------
# Footer controls (PDF, hospitals)
# -------------------------
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("Generate PDF Report for last conversation"):
        # create a text summary from the last assistant reply
        summary_lines = []
        if st.session_state.messages:
            # take last user and assistant pair
            last = st.session_state.messages[-1]
            summary_lines.append("Medical AI Report\n")
            for m in st.session_state.messages[-6:]:
                role = "You" if m["role"]=="user" else "Bot"
                summary_lines.append(f"{role}: {m['content']}")
        report_text = "\n".join(summary_lines)
        # optionally add hospitals template
        if include_hospitals and city_for_hospitals:
            report_text += f"\n\nSuggested hospitals near {city_for_hospitals}:\n1) Example Hospital A — address\n2) Example Hospital B — address\n(Replace with real Google Places results if connected)"
        pdf_file = create_pdf_report(report_text)
        with open(pdf_file, "rb") as f:
            st.download_button("Download medical_report.pdf", f, file_name=pdf_file)

with col2:
    if st.button("Clear local chat history"):
        st.session_state.messages = load_history()[:1]  # keep system only
        save_history(st.session_state.messages)
        st.experimental_rerun()

# -------------------------
# Always save to disk (so Streamlit instance retains between reloads until redeploy)
# -------------------------
save_history(st.session_state.messages)

st.caption("Disclaimer: This tool provides educational information only. Not a medical diagnosis.")


