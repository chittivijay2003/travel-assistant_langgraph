#!/usr/bin/env python3
"""
TRAVEL ASSISTANT - Standalone Version
Works without FastAPI server - just runs a test query
"""

import os
import json
import logging
import asyncio
from typing import TypedDict, Annotated, Sequence

# LangChain imports
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Other imports
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

print("\n" + "=" * 70)
print("🚀 TRAVEL ASSISTANT - LANGGRAPH + GEMINI")
print("=" * 70 + "\n")

# Load environment
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ Error: GOOGLE_API_KEY not found in .env file")
    exit(1)

print("✅ API Key loaded")

# Initialize LLM
MODEL_NAME = "gemini-2.5-flash"
print(f"🤖 Initializing {MODEL_NAME}...")

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME, temperature=0.7, google_api_key=GOOGLE_API_KEY
)

print("✅ LLM initialized\n")

# ============================================
# DEFINE TOOLS
# ============================================


@tool
def search_flights(origin: str, destination: str, date: str = "2025-12-01") -> str:
    """Search for flight options between origin and destination."""
    logger.info(f"🛫 Searching flights: {origin} → {destination}")

    flights = {
        "flights": [
            {"airline": "Singapore Airlines", "price_usd": 450, "duration": "6h 30m"},
            {"airline": "ANA", "price_usd": 420, "duration": "6h 30m"},
            {"airline": "JAL", "price_usd": 480, "duration": "6h 30m"},
        ]
    }
    return json.dumps(flights, indent=2)


@tool
def get_weather(location: str, date: str = "2025-12-01") -> str:
    """Get weather forecast for a location."""
    logger.info(f"🌤️  Getting weather for {location}")

    weather = {
        "location": location,
        "forecast": [
            {"day": "Day 1", "condition": "Sunny", "high_c": 22, "low_c": 15},
            {"day": "Day 2", "condition": "Partly Cloudy", "high_c": 20, "low_c": 14},
            {"day": "Day 3", "condition": "Clear", "high_c": 23, "low_c": 16},
        ],
    }
    return json.dumps(weather, indent=2)


@tool
def find_attractions(location: str, category: str = "all") -> str:
    """Find tourist attractions in a location."""
    logger.info(f"🗺️  Finding attractions in {location}")

    attractions = {
        "attractions": [
            {"name": "Senso-ji Temple", "type": "Cultural", "rating": 4.5},
            {"name": "Tokyo Tower", "type": "Landmark", "rating": 4.3},
            {"name": "Meiji Shrine", "type": "Cultural", "rating": 4.6},
            {"name": "Shibuya Crossing", "type": "Entertainment", "rating": 4.4},
            {"name": "Ueno Park", "type": "Nature", "rating": 4.5},
        ]
    }
    return json.dumps(attractions, indent=2)


tools = [search_flights, get_weather, find_attractions]
print(f"🔧 Tools registered: {[t.name for t in tools]}\n")

# ============================================
# BUILD LANGGRAPH WORKFLOW
# ============================================


# Define state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)


# Agent node
def call_model(state: AgentState):
    logger.info("🤖 Agent processing...")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# Router
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(f"🔧 Routing to tools ({len(last_message.tool_calls)} calls)")
        return "tools"
    logger.info("✅ Workflow complete")
    return END


# Manual tool node (avoiding prebuilt to fix import issues)
def tool_node(state: AgentState):
    """Execute tool calls manually."""
    from langchain_core.messages import ToolMessage

    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        # Find and execute the tool
        tool_result = None
        for t in tools:
            if t.name == tool_name:
                tool_result = t.invoke(tool_args)
                break

        results.append(
            ToolMessage(
                content=tool_result if tool_result else "Tool not found",
                tool_call_id=tool_id,
                name=tool_name,  # Important: include name field
            )
        )

    return {"messages": results}


# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

app = workflow.compile()

print("📊 LangGraph workflow compiled")
print("   Structure: agent → router → [tools] → agent → END\n")

# ============================================
# RUN TEST QUERY
# ============================================


async def run_query(query: str):
    """Run a travel query through the workflow."""
    print("=" * 70)
    print(f"📝 QUERY: {query}")
    print("=" * 70 + "\n")

    initial_state = {"messages": [HumanMessage(content=query)]}
    result = await app.ainvoke(initial_state)

    final_response = result["messages"][-1].content

    print("\n" + "=" * 70)
    print("📋 RESPONSE:")
    print("=" * 70)
    print(final_response)
    print("=" * 70 + "\n")

    return final_response


# Main execution
if __name__ == "__main__":
    test_query = """Plan a 3-day trip to Tokyo starting December 1st, 2025. 
    
    Use the available tools to:
    1. Search for flights from Singapore to Tokyo
    2. Get the weather forecast for Tokyo  
    3. Find top tourist attractions in Tokyo
    
    Then create a detailed 3-day itinerary."""

    try:
        asyncio.run(run_query(test_query))
        print("✅ Test completed successfully!\n")
        print("💡 To start the API server (if uvicorn is installed):")
        print("   uvicorn main:api_app --reload --port 8000\n")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        print(f"\n❌ Error occurred: {e}\n")
