import os
from crewai import LLM, Agent, Crew, Process, Task
import streamlit as st

st.set_page_config(
    page_title="JARVIS Agent Studio", page_icon="🤖", layout="wide"
)

st.title("🤖 JARVIS AI Agent Studio")
st.write("Powered by CrewAI and Groq LLaMA 3.3 (70B)")

# Fetch API Key securely from Streamlit Secrets
if "GROQ_API_KEY" in st.secrets:
    groq_key = st.secrets["GROQ_API_KEY"]
    os.environ["GROQ_API_KEY"] = groq_key
else:
    st.error("⚠️ GROQ_API_KEY is missing from Streamlit Secrets Settings!")
    st.stop()

# Topic Input
topic = st.text_area(
    "Enter Command / Content Topic:",
    placeholder="e.g., 5-minute morning skin barrier routine",
)

if st.button("🚀 Execute JARVIS Protocols", type="primary"):
    if not topic:
        st.warning("Please enter a topic.")
    else:
        with st.spinner("🤖 JARVIS agents are working..."):
            try:
                groq_llm = LLM(
                    model="groq/llama-3.3-70b-versatile",
                    temperature=0.7,
                    max_tokens=2048,
                )

                researcher = Agent(
                    role="JARVIS Research Sub-system",
                    goal=f"Analyze top hooks and viral concepts for: {topic}",
                    backstory="An elite intelligence sub-system designed to mine social trends.",
                    llm=groq_llm,
                )

                writer = Agent(
                    role="JARVIS Scripting Sub-system",
                    goal="Draft a short video script and captions based on research.",
                    backstory="A tactical copywriter agent skilled in short-form social engagement.",
                    llm=groq_llm,
                )

                task1 = Task(
                    description=f"Analyze top trends and content hooks for: {topic}.",
                    expected_output="3 strong content angles with visual concepts.",
                    agent=researcher,
                )

                task2 = Task(
                    description="Write a complete 30-second script (Visuals + Audio) and caption based on the research.",
                    expected_output="Visual Cues, Audio Script, Caption, and Hashtags.",
                    agent=writer,
                )

                crew = Crew(
                    agents=[researcher, writer],
                    tasks=[task1, task2],
                    process=Process.sequential,
                )

                result = crew.kickoff()

                st.success("✅ Execution Complete!")
                st.markdown("### 📋 JARVIS Output")
                st.markdown(str(result))

            except Exception as e:
                st.error(f"Execution Error: {e}")
