import os
import time
from crewai import LLM, Agent, Crew, Process, Task
import streamlit as st

st.set_page_config(
    page_title="JARVIS Agent Studio", page_icon="🤖", layout="wide"
)

st.title("🤖 JARVIS AI Agent Studio")
st.write("Optimized for Groq Free Tier Rate Limits")

if "GROQ_API_KEY" in st.secrets:
    groq_key = st.secrets["GROQ_API_KEY"]
    os.environ["GROQ_API_KEY"] = groq_key
else:
    st.error("⚠️ GROQ_API_KEY is missing from Streamlit Secrets Settings!")
    st.stop()

topic = st.text_area(
    "Enter Command / Content Topic:",
    placeholder="e.g., 5-minute morning skin barrier routine",
)

if st.button("🚀 Execute JARVIS Protocols", type="primary"):
    if not topic:
        st.warning("Please enter a topic.")
    else:
        with st.spinner(
            "🤖 JARVIS agents are working (applying rate-limit buffers)..."
        ):
            try:
                # Using 8B model prevents token-per-minute errors on free tier
                groq_llm = LLM(
                    model="groq/llama-3.1-8b-instant",
                    temperature=0.7,
                    max_tokens=1024,
                )

                # Unified Agent reduces token exchange overhead between agents
                jarvis_agent = Agent(
                    role="JARVIS Content Director",
                    goal=f"Research hooks and write a complete short-form video script for: {topic}",
                    backstory="An all-in-one AI strategic intelligence unit capable of research and scripting.",
                    llm=groq_llm,
                    verbose=False,
                )

                task = Task(
                    description=f"""
                    Analyze top content trends for '{topic}'.
                    Then directly write:
                    1. 3 Content Angles / Hooks
                    2. A concise 30-second script (Visual Cues + Audio)
                    3. A caption with hashtags.
                    """,
                    expected_output="A complete, structured content brief with hooks, script, and caption.",
                    agent=jarvis_agent,
                )

                # Set max_rpm to 2 to enforce delays between API calls
                crew = Crew(
                    agents=[jarvis_agent],
                    tasks=[task],
                    process=Process.sequential,
                    max_rpm=2,
                )

                result = crew.kickoff()

                st.success("✅ Execution Complete!")
                st.markdown("### 📋 JARVIS Output")
                st.markdown(str(result))

            except Exception as e:
                st.error(f"Execution Error: {e}")
