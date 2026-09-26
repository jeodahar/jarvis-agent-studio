"""
Builds and runs the CrewAI crew: one agent that can search, scrape, and
act (send email via Gmail, or post a message via Slack) using Composio.
Supports multi-turn context: pass prior topics/reports so follow-up
questions build on earlier research.
"""

import os
from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq
from composio_crewai import ComposioToolSet, Action

from tools import TavilySearchTool, FirecrawlScrapeTool

ACTIONS = {
    "Email (Gmail)": Action.GMAIL_SEND_EMAIL,
    "Slack message": Action.SLACK_SEND_MESSAGE,
    "Notion page": Action.NOTION_CREATE_PAGE,
}


def build_crew(topic: str, destination: str, action_label: str, history=None):
    llm = ChatGroq(
        model="groq/openai/gpt-oss-120b",
        api_key=os.environ["GROQ_API_KEY"],
    )

    composio_toolset = ComposioToolSet(api_key=os.environ["COMPOSIO_API_KEY"])
    action_tool = composio_toolset.get_tools(actions=[ACTIONS[action_label]])

    tools = [TavilySearchTool(), FirecrawlScrapeTool()] + action_tool

    if action_label == "Email (Gmail)":
        deliver_instruction = (
            f"send the report by email to {destination} using the Gmail "
            "send action, with a clear subject line"
        )
    elif action_label == "Slack message":
        deliver_instruction = (
            f"post the report to the Slack channel {destination} using the "
            "Slack send message action"
        )
    else:
        deliver_instruction = (
            f"create a new Notion page titled '{topic}' under {destination} "
            "containing the report, using the Notion create page action"
        )

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
