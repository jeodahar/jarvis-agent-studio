# Multi-Tool Research Agent — Beginner Setup Guide

You **speak or type a topic** → it **searches the web** (Tavily) →
**reads the best pages in full** (Firecrawl) → **writes a report**
(Groq + CrewAI) → **delivers it** via Gmail, Slack, or Notion
(Composio) → **reads it back out loud** (gTTS). It also **remembers
the conversation** so you can ask follow-ups, and has an experimental
**"Jarvis" wake-word** mode.

Everything is free — no paid voice APIs (Deepgram/ElevenLabs) used.

---

## ⚠️ Important honesty note on the wake-word feature

This app includes a "say Jarvis to activate" mode using the browser's
built-in speech recognition — completely free, no key. But be aware:

- It only works while the browser **tab is open and in focus** — it is
  not a background process like a phone assistant
- It needs **Chrome or Edge** (Safari/Firefox don't support this API)
- Streamlit embeds it in an iframe, and some browsers/security setups
  **block microphone access inside iframes** — if it doesn't work, this
  is why, and it's not something a code fix can force around
- **Push-to-talk (the record button) always works reliably** — use it
  as the fallback if wake-word doesn't respond

A true always-on assistant (like Jarvis) needs a phone or desktop app
with OS-level background permissions — a website fundamentally can't
do that, free or paid.

---

## 🔒 Security note (read this once)

In March 2026, the `litellm` package (which CrewAI uses to talk to
Groq) was hit by a real supply-chain attack — two malicious versions
briefly published to PyPI stole credentials from machines that
installed them. It was fixed fast, but `requirements.txt` **pins
`litellm>=1.83.14`** on purpose, to a version confirmed after both that
incident and a later critical bug were patched. Please don't loosen
that pin to "just get it working" without knowing why it's there.


## Step 1 — Create free accounts and get API keys

| # | Service | Used for | Link |
|---|---|---|---|
| 1 | Groq | The AI model that writes the report | https://console.groq.com → API Keys |
| 2 | Tavily | Web search | https://tavily.com → sign up → dashboard |
| 3 | Firecrawl | Reading full page content | https://firecrawl.dev → sign up → dashboard |
| 4 | Composio | Delivering the report | https://app.composio.dev → sign up |

**Composio one-time connections:** in the Composio dashboard, go to
**Apps** and click **Connect** for whichever you plan to use:
- **Gmail** — log in with the sending account
- **Slack** — install to your workspace
- **Notion** — authorize the integration and share the target page/database with it

You only need to connect the ones you'll actually use.

---

## Step 2 — Create a GitHub repository

1. https://github.com/new
2. Name it e.g. `multi-tool-agent`, set Public, **Create repository**

## Step 3 — Upload the files

Upload all 6 files (shown under this message) via **Add file → Upload files**:
`app.py`, `agent.py`, `tools.py`, `requirements.txt`, `packages.txt`, `README.md`

## Step 4 — Deploy on Streamlit Cloud

1. https://share.streamlit.io → **Create app** → pick your repo
2. Main file path: `app.py`
3. **Settings → Secrets**, paste:

```toml
GROQ_API_KEY = "..."
TAVILY_API_KEY = "..."
FIRECRAWL_API_KEY = "..."
COMPOSIO_API_KEY = "..."
```

4. **Save** → **Deploy** (first build takes a few minutes)

## Step 5 — Use it

1. Open the app URL
2. Either allow mic access and try saying "Jarvis, [your topic]", or
   just click **Start recording** and speak, or type your topic
3. Pick a delivery method (Gmail / Slack / Notion) and fill in the
   destination field
4. **Run Agent** → wait ~1-2 minutes
5. Read/listen to the result. Ask a follow-up topic afterward — it
   remembers what you researched earlier in the session

---

## Troubleshooting

- **Wake-word never triggers** → use push-to-talk instead (see honesty
  note above); this is a browser limitation, not a bug to "fix"
- **"Missing API keys"** → check Secrets key names match exactly
- **Composio action fails** → Composio's tool slugs (e.g.
  `SLACK_SEND_MESSAGE`) occasionally change; if you get a "tool not
  found" error, search https://docs.composio.dev's toolkit catalog for
  the current slug and update the `ACTIONS` dict in `agent.py`
- **No message/page/email arrives** → confirm you connected that app
  in the Composio dashboard first
- **Conversation memory resets** → it's per-browser-session; refreshing
  the page clears it (this is normal for a Streamlit app without a
  database)
