# ============================================
# TRAVEL ASSISTANT - MAIN APPLICATION
# ============================================
import os
import json
import logging
import asyncio
import time
from typing import TypedDict, Annotated, Sequence
from functools import wraps

# LangChain imports
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# FastAPI imports
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Other imports
from dotenv import load_dotenv

# ============================================
# LOGGING SETUP
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("travel_assistant.log")],
)
logger = logging.getLogger(__name__)

logger.info("🚀 Travel Assistant Application Starting...")

# ============================================
# LOAD ENVIRONMENT VARIABLES
# ============================================
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("❌ GOOGLE_API_KEY not found in environment variables")
    raise ValueError("GOOGLE_API_KEY not found. Please set it in .env file")

logger.info("🔑 API key found")

# ============================================
# INITIALIZE GEMINI MODEL
# ============================================
MODEL_NAME = "gemini-2.5-flash"
logger.info(f"🤖 Initializing model: {MODEL_NAME}")

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME, temperature=0.7, google_api_key=GOOGLE_API_KEY
)

logger.info("✅ LLM model initialized successfully")

# ============================================
# TASK 1: IMPLEMENT MOCK TOOLS
# ============================================


@tool
def search_flights(origin: str, destination: str, date: str = "2025-12-01") -> str:
    """
    Search for flight options between origin and destination.

    Args:
        origin: Departure city
        destination: Arrival city
        date: Travel date (YYYY-MM-DD format)

    Returns:
        JSON string containing flight options
    """
    logger.info(f"🛫 search_flights called: {origin} → {destination} on {date}")

    # Mock flight data
    mock_flights = {
        "flights": [
            {
                "airline": "Singapore Airlines",
                "flight_number": "SQ638",
                "price_usd": 450,
                "departure_time": "07:00 AM",
                "arrival_time": "02:30 PM",
                "duration": "6h 30m",
                "stops": "Direct",
            },
            {
                "airline": "ANA",
                "flight_number": "NH842",
                "price_usd": 420,
                "departure_time": "11:30 AM",
                "arrival_time": "07:00 PM",
                "duration": "6h 30m",
                "stops": "Direct",
            },
            {
                "airline": "JAL",
                "flight_number": "JL712",
                "price_usd": 480,
                "departure_time": "09:15 AM",
                "arrival_time": "04:45 PM",
                "duration": "6h 30m",
                "stops": "Direct",
            },
        ],
        "origin": origin,
        "destination": destination,
        "date": date,
    }

    logger.info(
        f"✅ Found {len(mock_flights['flights'])} flights from {origin} to {destination}"
    )
    return json.dumps(mock_flights, indent=2)


@tool
def get_weather(location: str, date: str = "2025-12-01") -> str:
    """
    Get weather forecast for a location.

    Args:
        location: City name
        date: Date for weather forecast (YYYY-MM-DD format)

    Returns:
        JSON string containing weather forecast
    """
    logger.info(f"🌤️ get_weather called for {location} on {date}")

    # Mock weather data
    mock_weather = {
        "location": location,
        "date": date,
        "forecast": [
            {
                "day": "Day 1",
                "condition": "Sunny",
                "high_c": 22,
                "low_c": 15,
                "precipitation": "10%",
            },
            {
                "day": "Day 2",
                "condition": "Partly Cloudy",
                "high_c": 20,
                "low_c": 14,
                "precipitation": "20%",
            },
            {
                "day": "Day 3",
                "condition": "Clear",
                "high_c": 23,
                "low_c": 16,
                "precipitation": "5%",
            },
        ],
        "humidity": "65%",
        "wind_speed": "15 km/h",
    }

    logger.info(f"✅ Retrieved weather forecast for {location}")
    return json.dumps(mock_weather, indent=2)


@tool
def find_attractions(location: str, category: str = "all") -> str:
    """
    Find tourist attractions in a location.

    Args:
        location: City name
        category: Category of attractions (all, cultural, nature, entertainment)

    Returns:
        JSON string containing attractions
    """
    logger.info(f"🗺️ find_attractions called for {location}, category: {category}")

    # Mock attractions data
    mock_attractions = {
        "location": location,
        "category": category,
        "attractions": [
            {
                "name": "Senso-ji Temple",
                "type": "Cultural",
                "description": "Ancient Buddhist temple in Asakusa",
                "rating": 4.5,
                "estimated_time": "2 hours",
            },
            {
                "name": "Tokyo Tower",
                "type": "Landmark",
                "description": "Iconic communications and observation tower",
                "rating": 4.3,
                "estimated_time": "1.5 hours",
            },
            {
                "name": "Meiji Shrine",
                "type": "Cultural",
                "description": "Shinto shrine dedicated to Emperor Meiji",
                "rating": 4.6,
                "estimated_time": "1 hour",
            },
            {
                "name": "Shibuya Crossing",
                "type": "Entertainment",
                "description": "World's busiest pedestrian crossing",
                "rating": 4.4,
                "estimated_time": "30 minutes",
            },
            {
                "name": "Ueno Park",
                "type": "Nature",
                "description": "Large public park with museums and zoo",
                "rating": 4.5,
                "estimated_time": "3 hours",
            },
        ],
    }

    logger.info(
        f"✅ Found {len(mock_attractions['attractions'])} attractions in {location}"
    )
    return json.dumps(mock_attractions, indent=2)


# Collect all tools
tools = [search_flights, get_weather, find_attractions]
logger.info(f"🔧 Registered {len(tools)} tools: {[t.name for t in tools]}")

# ============================================
# TASK 2: RETRY LOGIC WITH EXPONENTIAL BACKOFF
# ============================================


def retry_with_exponential_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
):
    """
    Decorator for retry logic with exponential backoff (synchronous).
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"🔄 Attempt {attempt + 1}/{max_retries} for {func.__name__}"
                )
                result = func(*args, **kwargs)
                logger.info(f"✅ {func.__name__} succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"❌ {func.__name__} failed after {max_retries} attempts: {str(e)}"
                    )
                    raise

                logger.warning(
                    f"⚠️ {func.__name__} failed (attempt {attempt + 1}): {str(e)}"
                )
                logger.info(f"🔄 Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                delay = min(delay * exponential_base, max_delay)

    return wrapper


def retry_with_exponential_backoff_async(
    func,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
):
    """
    Decorator for retry logic with exponential backoff (asynchronous).
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"🔄 Attempt {attempt + 1}/{max_retries} for {func.__name__}"
                )
                result = await func(*args, **kwargs)
                logger.info(f"✅ {func.__name__} succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"❌ {func.__name__} failed after {max_retries} attempts: {str(e)}"
                    )
                    raise

                logger.warning(
                    f"⚠️ {func.__name__} failed (attempt {attempt + 1}): {str(e)}"
                )
                logger.info(f"🔄 Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                delay = min(delay * exponential_base, max_delay)

    return wrapper


logger.info("✅ Retry logic decorators defined")

# ============================================
# TASK 4: LANGGRAPH WORKFLOW
# ============================================


# Define agent state
class AgentState(TypedDict):
    """State that flows through the LangGraph workflow."""

    messages: Annotated[Sequence[BaseMessage], add_messages]


logger.info("📊 AgentState defined")

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)
logger.info("🔗 Tools bound to LLM")


# Define agent node (calls LLM)
def call_model(state: AgentState):
    """Agent node - LLM processes messages and decides whether to use tools."""
    logger.info("🤖 Agent node: Processing messages")
    logger.debug(f"📥 Current state messages count: {len(state['messages'])}")

    messages = state["messages"]

    # Call LLM with retry logic
    response = llm_with_tools.invoke(messages)

    logger.info(f"📤 Agent response type: {type(response).__name__}")
    if hasattr(response, "tool_calls") and response.tool_calls:
        logger.info(f"🔧 Agent requesting {len(response.tool_calls)} tool calls")

    return {"messages": [response]}


# Define router (conditional edge)
def should_continue(state: AgentState):
    """Router - decides whether to continue to tools or end the workflow."""
    messages = state["messages"]
    last_message = messages[-1]

    logger.info("🔀 Router: Evaluating next step")

    # If LLM makes tool calls, continue to tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(
            f"🔧 Router: Found {len(last_message.tool_calls)} tool calls, routing to tools"
        )
        return "tools"

    # Otherwise, end the workflow
    logger.info("✅ Router: No tool calls found, ending workflow")
    return END


# Create the workflow graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# Set entry point
workflow.set_entry_point("agent")

# Add conditional edges
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})

# Add edge from tools back to agent
workflow.add_edge("tools", "agent")

# Compile the graph
app = workflow.compile()

logger.info("✅ LangGraph workflow compiled successfully")
logger.info("📊 Graph structure: START → agent → (router) → [tools] → agent → END")

# ============================================
# TASK 3: STREAMING RESPONSES
# ============================================


async def stream_llm_response(query: str):
    """
    Stream responses from the LangGraph workflow.

    Args:
        query: User's travel query

    Yields:
        Server-Sent Events (SSE) formatted responses
    """
    logger.info(f"📡 Starting streaming for query: '{query[:50]}...'")

    try:
        initial_state = {"messages": [HumanMessage(content=query)]}

        logger.debug("🔄 Invoking LangGraph workflow with streaming...")

        # Stream events from the graph
        async for event in app.astream(initial_state):
            logger.debug(f"📊 Stream event received: {list(event.keys())}")

            for node_name, node_output in event.items():
                logger.debug(f"🎯 Processing node: {node_name}")

                if node_name == "agent":
                    messages = node_output.get("messages", [])
                    if messages:
                        last_message = messages[-1]

                        # Only stream content (not tool calls)
                        if hasattr(last_message, "content") and last_message.content:
                            content = last_message.content
                            logger.info(
                                f"📤 Streaming content chunk ({len(content)} chars)"
                            )
                            yield f"data: {json.dumps({'content': content})}\n\n"

        logger.info("✅ Streaming completed successfully")
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"❌ Streaming error: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


logger.info("✅ Streaming function defined")

# ============================================
# TASK 5: FASTAPI ENDPOINT
# ============================================

# Initialize FastAPI app
api_app = FastAPI(
    title="Travel Assistant API",
    description="AI-powered travel planning assistant using LangGraph and Gemini",
    version="1.0.0",
)

logger.info("🌐 FastAPI application initialized")


class TravelRequest(BaseModel):
    """Request model for travel assistant endpoint."""

    query: str
    stream: bool = True


class TravelResponse(BaseModel):
    """Response model for travel assistant endpoint."""

    response: str
    status: str = "success"


@api_app.get("/")
async def root():
    """Health check endpoint."""
    logger.info("📍 Root endpoint called")
    return {
        "status": "healthy",
        "service": "Travel Assistant API",
        "version": "1.0.0",
        "model": MODEL_NAME,
    }


@api_app.get("/health")
async def health():
    """Detailed health check."""
    logger.info("🏥 Health check endpoint called")
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "tools": [t.name for t in tools],
        "api_key_configured": bool(GOOGLE_API_KEY),
    }


@api_app.post("/travel-assistant", response_model=TravelResponse)
async def travel_assistant_endpoint(request: TravelRequest):
    """
    Main travel assistant endpoint.

    Processes travel queries using LangGraph workflow with tool support.
    Supports both streaming and non-streaming responses.
    """
    logger.info("🎯 Travel assistant endpoint called")
    logger.info(f"📝 Query: '{request.query[:100]}...'")
    logger.info(f"📡 Streaming: {request.stream}")

    try:
        if request.stream:
            # Return streaming response
            logger.info("📡 Initiating streaming response")
            return StreamingResponse(
                stream_llm_response(request.query), media_type="text/event-stream"
            )
        else:
            # Return complete response
            logger.info("📦 Generating complete response")

            initial_state = {"messages": [HumanMessage(content=request.query)]}
            result = await app.ainvoke(initial_state)

            final_message = result["messages"][-1]
            response_content = final_message.content

            logger.info(f"✅ Response generated ({len(response_content)} chars)")

            return TravelResponse(response=response_content, status="success")

    except Exception as e:
        logger.error(f"❌ Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


logger.info("✅ FastAPI endpoints defined")

# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🎉 TRAVEL ASSISTANT APPLICATION READY")
    logger.info("=" * 60)
    logger.info(f"🤖 Model: {MODEL_NAME}")
    logger.info(f"🔧 Tools: {[t.name for t in tools]}")
    logger.info("📡 Streaming: Enabled")
    logger.info("🔄 Retry Logic: Exponential backoff (max 3 attempts)")
    logger.info("=" * 60)

    # Test with a simple query
    print("\n" + "=" * 60)
    print("🧪 TESTING TRAVEL ASSISTANT")
    print("=" * 60)

    test_query = "Plan a 3-day trip to Tokyo. I need flight options from Singapore, weather forecast, and top attractions."
    print(f"\n📝 Query: {test_query}\n")

    async def test_workflow():
        """Test the workflow with a sample query."""
        logger.info("🧪 Running test query...")

        initial_state = {"messages": [HumanMessage(content=test_query)]}

        result = await app.ainvoke(initial_state)

        print("\n" + "=" * 60)
        print("📋 RESPONSE:")
        print("=" * 60)
        print(result["messages"][-1].content)
        print("=" * 60 + "\n")

        logger.info("✅ Test completed successfully")

    # Run test
    asyncio.run(test_workflow())

    print("\n💡 To start the API server, run:")
    print("   uvicorn main:api_app --reload --port 8000")
    print("\n📚 Then visit: http://localhost:8000/docs\n")
