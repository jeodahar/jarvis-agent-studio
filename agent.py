"""
Builds and runs the CrewAI crew: one agent that can search, scrape, and
act (send email via Gmail, post to Slack, or create a Notion page) using
Composio. Supports multi-turn context: pass prior topics/reports so
follow-up questions build on earlier research.
"""

import os
from crewai import Agent, Task, Crew, LLM
from composio import Composio
from composio_crewai import CrewAIProvider

from tools import TavilySearchTool, FirecrawlScrapeTool

# Each entry maps a friendly label to the Composio toolkit + tool slug
# that delivers the report. (Composio's newer SDK identifies actions by
# these string slugs rather than the old Action enum.)
ACTIONS = {
    "Email (Gmail)": {"toolkit": "gmail", "tool": "GMAIL_SEND_EMAIL"},
    "Slack message": {"toolkit": "slack", "tool": "SLACK_SEND_MESSAGE"},
    "Notion page": {"toolkit": "notion", "tool": "NOTION_CREATE_PAGE"},
}


def _delivery_instruction(action_label: str, destination: str, topic: str) -> str:
    if action_label == "Email (Gmail)":
        return (
            f"send the report by email to {destination} using the Gmail "
            "send email tool, with a clear subject line"
        )
    elif action_label == "Slack message":
        return (
            f"post the report to the Slack channel {destination} using the "
            "Slack send message tool"
        )
    else:
        return (
            f"create a new Notion page titled '{topic}' under {destination} "
            "containing the report, using the Notion create page tool"
        )


def build_crew(topic: str, destination: str, action_label: str, history=None):
    # CrewAI's native LLM class talks to Groq through its LiteLLM fallback
    # (Groq isn't one of the five natively-integrated providers). No
    # langchain-groq needed.
    llm = LLM(model="groq/openai/gpt-oss-120b", api_key=os.environ["GROQ_API_KEY"])

    config = ACTIONS[action_label]
    composio = Composio(
        api_key=os.environ["COMPOSIO_API_KEY"],
        provider=CrewAIProvider(),
    )
    # Scope the session to just the one toolkit/tool this run needs, so
    # the agent can't reach for unrelated connected apps.
    session = composio.create(
        user_id="default",
        toolkits=[config["toolkit"]],
        preload={"tools": [config["tool"]]},
    )
    action_tools = session.tools()

    tools = [TavilySearchTool(), FirecrawlScrapeTool()] + action_tools

    deliver_instruction = _delivery_instruction(action_label, destination, topic)

    history_context = ""
    if history:
        past = "\n".join(f"- Topic: {h['topic']}\n  Summary: {h['report'][:400]}" for h in history)
        history_context = (
            "\n\nEarlier in this conversation, you already researched:\n"
            f"{past}\n"
            "If the new topic below is a follow-up (e.g. 'tell me more about "
            "that', 'what about X instead'), use this prior context to "
            "understand what it refers to.\n"
        )

    researcher = Agent(
        role="Research Agent",
        goal=(
            "Research the given topic thoroughly using web search and page "
            f"reading, write a clear concise report, then {deliver_instruction}."
        ),
        backstory=(
            "You are a careful research assistant with memory of the "
            "ongoing conversation. You search the web, read the most "
            "relevant pages in full, synthesize findings into a "
            "well-organized report, and finally deliver it."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
    )

    task = Task(
        description=(
            f"Research this topic: '{topic}'.{history_context}\n"
            "1. Use web_search to find 3-5 good sources.\n"
            "2. Use read_webpage on the most promising 2-3 URLs to get full detail.\n"
            "3. Write a well-structured report (headline, key findings, sources).\n"
            f"4. Then {deliver_instruction}."
        ),
        expected_output=(
            "Confirmation that the report was written and delivered, "
            "plus the report text itself."
        ),
        agent=researcher,
    )

    return Crew(agents=[researcher], tasks=[task], verbose=True)


def run_agent(topic: str, destination: str, action_label: str, history=None) -> str:
    crew = build_crew(topic, destination, action_label, history)
    result = crew.kickoff()
    return str(result)
