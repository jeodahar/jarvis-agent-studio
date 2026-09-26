import io
import os

import speech_recognition as sr
import streamlit as st
import streamlit.components.v1 as components
from gtts import gTTS
from pydub import AudioSegment
from streamlit_mic_recorder import mic_recorder

from agent import run_agent, ACTIONS

st.set_page_config(page_title="Multi-Tool Research Agent", page_icon="🔎")

for key in [
    "GROQ_API_KEY",
    "TAVILY_API_KEY",
    "FIRECRAWL_API_KEY",
    "COMPOSIO_API_KEY",
]:
    if key in st.secrets:
        os.environ[key] = st.secrets[key]

st.title("🔎 Multi-Tool Research Agent")
st.caption(
    "Say \"Jarvis, [topic]\", click record, or type. It searches, reads "
    "sources, writes a report, delivers it, reads it back, and remembers "
    "the conversation."
)

# ---------- helpers ----------

def transcribe(audio_bytes: bytes) -> str:
    webm_audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    wav_io = io.BytesIO()
    webm_audio.export(wav_io, format="wav")
    wav_io.seek(0)
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_io) as source:
        audio_data = recognizer.record(source)
    return recognizer.recognize_google(audio_data)


def speak(text: str) -> bytes:
    tts = gTTS(text=text, lang="en")
    mp3_io = io.BytesIO()
    tts.write_to_fp(mp3_io)
    mp3_io.seek(0)
    return mp3_io.read()


# ---------- session state ----------
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "history" not in st.session_state:
    st.session_state.history = []  # list of {"topic": ..., "report": ...}
if "last_voice_cmd" not in st.session_state:
    st.session_state.last_voice_cmd = None
if "auto_run" not in st.session_state:
    st.session_state.auto_run = False

# ---------- wake word listener (free, browser-based, Chrome/Edge only) ----------
components.html(
    """
    <div style="font-family:sans-serif;font-size:14px;color:#888;">
      🎙️ Always listening for "Jarvis..." (Chrome/Edge, allow mic access)
    </div>
    <script>
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.lang = 'en-US';
      let awaitingCommand = false;

      function sendCommand(text) {
        const url = new URL(window.top.location.href);
        url.searchParams.set('voice_cmd', text);
        window.top.location.href = url.toString();
      }

      recognition.onresult = function(event) {
        for (let i = event.resultIndex; i < event.results.length; i++) {
          let transcript = event.results[i][0].transcript.trim();
          let lower = transcript.toLowerCase();
          if (!awaitingCommand) {
            if (lower.includes("jarvis")) {
              let idx = lower.indexOf("jarvis");
              let rest = transcript.substring(idx + 6).trim();
              if (rest.length > 2) {
                sendCommand(rest);
                return;
              } else {
                awaitingCommand = true;
              }
            }
          } else {
            sendCommand(transcript);
            return;
          }
        }
      };
      recognition.onend = function() { recognition.start(); };
      recognition.onerror = function() {};
      recognition.start();
    }
    </script>
    """,
    height=40,
)

# ---------- pick up wake-word command from URL ----------
voice_cmd = st.query_params.get("voice_cmd")
if voice_cmd and voice_cmd != st.session_state.last_voice_cmd:
    st.session_state.last_voice_cmd = voice_cmd
    st.session_state.topic = voice_cmd
    st.session_state.auto_run = True
    st.query_params.clear()

# ---------- manual mic recorder (fallback / precise control) ----------
st.subheader("🎙️ Push-to-talk")
audio = mic_recorder(start_prompt="Start recording", stop_prompt="Stop recording", key="recorder")
if audio:
    with st.spinner("Transcribing..."):
        try:
            st.session_state.topic = transcribe(audio["bytes"])
            st.success(f"Heard: \"{st.session_state.topic}\"")
        except sr.UnknownValueError:
            st.warning("Couldn't understand the audio — please try again or type below.")
        except Exception as e:
            st.error(f"Transcription failed: {e}")

# ---------- conversation history ----------
if st.session_state.history:
    st.subheader("💬 Conversation")
    for turn in st.session_state.history:
        with st.chat_message("user"):
            st.write(turn["topic"])
        with st.chat_message("assistant"):
            st.write(turn["report"])

# ---------- inputs ----------
st.subheader("Topic")
topic = st.text_input("What should the agent research?", value=st.session_state.topic)

st.subheader("Deliver via")
action_label = st.selectbox("Action", list(ACTIONS.keys()))
destination_label = {
    "Email (Gmail)": "Email address",
    "Slack message": "Slack channel (e.g. #general)",
    "Notion page": "Notion parent page/database name",
}[action_label]
destination = st.text_input(destination_label)

run_clicked = st.button("Run Agent", type="primary") or st.session_state.auto_run
st.session_state.auto_run = False

if run_clicked:
    missing = [
        k for k in ["GROQ_API_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY", "COMPOSIO_API_KEY"]
        if k not in os.environ
    ]
    if missing:
        st.error(f"Missing API keys in secrets: {', '.join(missing)}")
    elif not topic or not destination:
        st.warning("Please enter both a topic and a destination.")
    else:
        with st.spinner("Researching... this can take a minute or two."):
            try:
                result = run_agent(topic, destination, action_label, st.session_state.history)
                st.session_state.history.append({"topic": topic, "report": result})
                st.session_state.topic = ""
                st.success("Done!")
                st.markdown(result)

                st.subheader("🔊 Voice output")
                with st.spinner("Generating audio..."):
                    audio_bytes = speak(result)
                    st.audio(audio_bytes, format="audio/mp3")
            except Exception as e:
                st.error(f"Something went wrong: {e}")
