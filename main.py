# ============================================
# TRAVEL ASSISTANT - MAIN APPLICATION
# ============================================
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
from langgraph.prebuilt import ToolNode

# FastAPI imports
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
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

    # List of cities that typically don't have airports or commercial flights
    no_airport_cities = [
        "mancheriyal",
        "karimnagar",
        "nizamabad",
        "adilabad",
        "khammam",
        "warangal",
        "nalgonda",
        "mahbubnagar",
        "medak",
        "rangareddy",
    ]

    # Check if destination doesn't have an airport
    if destination.lower() in no_airport_cities:
        result = {
            "message": f"No commercial flights available to {destination}. This destination does not have a commercial airport.",
            "alternatives": [
                {
                    "option": "Road Transport",
                    "description": f"Consider travelling by bus or car from {origin}. Estimated journey time: 3-5 hours.",
                    "recommended": True,
                },
                {
                    "option": "Train",
                    "description": f"Check Indian Railways for train services from {origin} to nearby stations.",
                    "recommended": True,
                },
            ],
            "origin": origin,
            "destination": destination,
            "date": date,
        }
        logger.info(f"ℹ️ No flights available to {destination}")
        return json.dumps(result, indent=2)

    # Generate dynamic flight data for cities with airports
    import random

    base_price = random.randint(350, 700)

    mock_flights = {
        "flights": [
            {
                "airline": "Direct Airlines",
                "flight_number": "DA101",
                "price_usd": base_price,
                "departure_time": "07:00 AM",
                "arrival_time": "02:30 PM",
                "duration": "6h 30m",
                "stops": "Direct",
            },
            {
                "airline": "Express Air",
                "flight_number": "EA202",
                "price_usd": base_price - 30,
                "departure_time": "11:30 AM",
                "arrival_time": "07:00 PM",
                "duration": "6h 30m",
                "stops": "Direct",
            },
            {
                "airline": "Sky Connect",
                "flight_number": "SC303",
                "price_usd": base_price + 30,
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

    # Generate dynamic weather data
    import random

    conditions = ["Sunny", "Partly Cloudy", "Clear", "Cloudy", "Light Rain"]

    mock_weather = {
        "location": location,
        "date": date,
        "forecast": [
            {
                "day": "Day 1",
                "condition": random.choice(conditions),
                "high_c": random.randint(20, 32),
                "low_c": random.randint(12, 20),
                "precipitation": f"{random.randint(5, 30)}%",
            },
            {
                "day": "Day 2",
                "condition": random.choice(conditions),
                "high_c": random.randint(20, 32),
                "low_c": random.randint(12, 20),
                "precipitation": f"{random.randint(5, 30)}%",
            },
            {
                "day": "Day 3",
                "condition": random.choice(conditions),
                "high_c": random.randint(20, 32),
                "low_c": random.randint(12, 20),
                "precipitation": f"{random.randint(5, 30)}%",
            },
        ],
        "humidity": f"{random.randint(50, 80)}%",
        "wind_speed": f"{random.randint(10, 25)} km/h",
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

    # City-specific attractions database
    attractions_db = {
        "Mancheriyal": [
            {
                "name": "Kala Ashram",
                "type": "Cultural",
                "description": "Art and cultural center promoting local arts and crafts",
                "rating": 4.2,
                "estimated_time": "1.5 hours",
            },
            {
                "name": "Godavari River Banks",
                "type": "Nature",
                "description": "Scenic river views and peaceful walking areas",
                "rating": 4.3,
                "estimated_time": "2 hours",
            },
            {
                "name": "Local Temples",
                "type": "Cultural",
                "description": "Historic temples showcasing regional architecture",
                "rating": 4.0,
                "estimated_time": "1 hour",
            },
            {
                "name": "Mancheriyal Market",
                "type": "Entertainment",
                "description": "Local market for regional crafts and produce",
                "rating": 3.8,
                "estimated_time": "1.5 hours",
            },
        ],
        "Austin": [
            {
                "name": "Texas State Capitol",
                "type": "Cultural",
                "description": "Historic government building with free tours",
                "rating": 4.7,
                "estimated_time": "1.5 hours",
            },
            {
                "name": "Lady Bird Lake",
                "type": "Nature",
                "description": "Urban lake perfect for kayaking and paddle boarding",
                "rating": 4.6,
                "estimated_time": "2 hours",
            },
            {
                "name": "South Congress Avenue",
                "type": "Entertainment",
                "description": "Trendy street with shops, restaurants, and live music",
                "rating": 4.5,
                "estimated_time": "2 hours",
            },
            {
                "name": "Zilker Park",
                "type": "Nature",
                "description": "Large park with trails, gardens, and Barton Springs Pool",
                "rating": 4.8,
                "estimated_time": "3 hours",
            },
            {
                "name": "Congress Avenue Bridge",
                "type": "Nature",
                "description": "Famous bat colony viewing at sunset",
                "rating": 4.6,
                "estimated_time": "1 hour",
            },
            {
                "name": "Live Music District",
                "type": "Entertainment",
                "description": "6th Street entertainment district with live music venues",
                "rating": 4.4,
                "estimated_time": "3 hours",
            },
        ],
        "Tokyo": [
            {
                "name": "Shibuya Crossing",
                "type": "Entertainment",
                "description": "World's busiest pedestrian crossing",
                "rating": 4.4,
                "estimated_time": "30 minutes",
            },
            {
                "name": "Senso-ji Temple",
                "type": "Cultural",
                "description": "Ancient Buddhist temple in Asakusa",
                "rating": 4.5,
                "estimated_time": "2 hours",
            },
            {
                "name": "Tokyo Skytree",
                "type": "Landmark",
                "description": "Tallest structure in Japan with observation decks",
                "rating": 4.6,
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
                "name": "Ueno Park",
                "type": "Nature",
                "description": "Large public park with museums and zoo",
                "rating": 4.5,
                "estimated_time": "3 hours",
            },
        ],
    }

    # Get attractions for the location or return informative message
    if location in attractions_db:
        attractions_list = attractions_db[location]
        mock_attractions = {
            "location": location,
            "category": category,
            "attractions": attractions_list,
        }
    else:
        # Return informative message for unknown cities
        mock_attractions = {
            "location": location,
            "category": category,
            "message": f"Detailed attraction data for {location} is not available in our database.",
            "recommendation": "Consider searching online travel guides, local tourism websites, or popular review platforms like TripAdvisor, Google Maps, or local government tourism pages for up-to-date information about attractions in this area.",
            "attractions": [],
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


logger.info("✅ Retry logic with exponential backoff implemented")

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


# Define wrapper function with retry logic
async def call_llm_with_retry(messages):
    """Call LLM with retry logic using exponential backoff."""
    delay = 1.0
    max_retries = 3
    exponential_base = 2.0
    max_delay = 60.0

    for attempt in range(max_retries):
        try:
            logger.debug(f"🔄 Attempt {attempt + 1}/{max_retries} for LLM call")
            result = await llm_with_tools.ainvoke(messages)
            if attempt > 0:
                logger.info(f"✅ LLM call succeeded on attempt {attempt + 1}")
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(
                    f"❌ LLM call failed after {max_retries} attempts: {str(e)}"
                )
                raise
            logger.warning(f"⚠️ LLM call failed (attempt {attempt + 1}): {str(e)}")
            logger.info(f"🔄 Retrying in {delay:.2f} seconds...")
            await asyncio.sleep(delay)
            delay = min(delay * exponential_base, max_delay)


async def call_model(state: AgentState):
    """Agent node - LLM processes messages and decides whether to use tools."""
    logger.info("🤖 Agent node: Processing messages")
    logger.debug(f"📥 Current state messages count: {len(state['messages'])}")

    messages = state["messages"]

    # Call LLM with retry logic
    response = await call_llm_with_retry(messages)

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

                        # Check if agent is requesting tool calls
                        if (
                            hasattr(last_message, "tool_calls")
                            and last_message.tool_calls
                        ):
                            yield f"data: {json.dumps({'content': '\\n🤖 AI Agent is analyzing your request...\\n'})}\n\n"
                            await asyncio.sleep(1.5)

                            for tool_call in last_message.tool_calls:
                                tool_info = f"🔧 Calling {tool_call['name']}...\n"
                                logger.info(tool_info)
                                yield f"data: {json.dumps({'content': tool_info})}\n\n"
                                await asyncio.sleep(0.5)
                        # Stream final content
                        elif hasattr(last_message, "content") and last_message.content:
                            content = last_message.content
                            logger.info(
                                f"📤 Streaming content chunk ({len(content)} chars)"
                            )
                            yield f"data: {json.dumps({'content': '\\n\\n🤖 AI Agent is preparing your travel plan...\\n'})}\n\n"
                            await asyncio.sleep(2)
                            yield f"data: {json.dumps({'content': f'\\n📋 **Travel Plan:**\\n{content}'})}\n\n"

                elif node_name == "tools":
                    # Stream tool results with delays
                    messages = node_output.get("messages", [])
                    for msg in messages:
                        if hasattr(msg, "name"):
                            tool_result = f"✓ {msg.name} completed\\n"
                            logger.info(tool_result)
                            yield f"data: {json.dumps({'content': tool_result})}\n\n"
                            await asyncio.sleep(1.5)

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

    query: str = None
    prompt: str = None  # Support both 'query' and 'prompt' for compatibility
    stream: bool = False

    def get_query(self) -> str:
        """Get the query/prompt, supporting both field names."""
        return self.query or self.prompt or ""


class TravelResponse(BaseModel):
    """Response model for travel assistant endpoint."""

    response: str
    used_tools: list = []
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

    # Get query from either 'query' or 'prompt' field
    user_query = request.get_query()
    if not user_query:
        raise HTTPException(
            status_code=422, detail="Missing required field: 'query' or 'prompt'"
        )

    logger.info(f"📝 Query: '{user_query[:100]}...'")
    logger.info(f"📡 Streaming: {request.stream}")

    # Enhanced system prompt to make LLM use tools proactively and format output correctly
    enhanced_query = f"""You are a proactive travel assistant. When users ask about trip planning, you MUST:
1. Immediately call the available tools (search_flights, get_weather, find_attractions) without asking for more details
2. Use reasonable defaults: today's date is 2025-12-06, use "2025-12-15" as default travel date if not specified
3. After gathering tool results, format your response EXACTLY like this:

Flights Found:
- [Origin] → [Destination], $[Price], [Time]

Weather Forecast:
- Day 1: [Condition]
- Day 2: [Condition]
- Day 3: [Condition]

Top Attractions:
- [Attraction 1]
- [Attraction 2]
- [Attraction 3]

Suggested Itinerary:
Day 1: [Area/Activity]
Day 2: [Area/Activity]
Day 3: [Area/Activity]

User query: {user_query}

Remember: USE THE TOOLS FIRST, then format the response as shown above."""

    try:
        if request.stream:
            # Return streaming response
            logger.info("📡 Initiating streaming response")
            return StreamingResponse(
                stream_llm_response(enhanced_query), media_type="text/event-stream"
            )
        else:
            # Return complete response
            logger.info("📦 Generating complete response")

            initial_state = {"messages": [HumanMessage(content=enhanced_query)]}
            result = await app.ainvoke(initial_state)

            # Track used tools
            used_tools = []
            for msg in result["messages"]:
                if hasattr(msg, "name") and msg.name:
                    if msg.name not in used_tools:
                        used_tools.append(msg.name)

            final_message = result["messages"][-1]
            response_content = final_message.content

            logger.info(f"✅ Response generated ({len(response_content)} chars)")
            logger.info(f"🔧 Used tools: {used_tools}")

            return TravelResponse(
                response=response_content, used_tools=used_tools, status="success"
            )

    except Exception as e:
        logger.error(f"❌ Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_app.get("/ui", response_class=HTMLResponse)
async def chat_ui():
    """Interactive chat UI for travel assistant."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Travel Assistant - Chat UI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .content { padding: 30px; }
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 14px;
            resize: vertical;
            min-height: 80px;
            font-family: inherit;
        }
        textarea:focus { outline: none; border-color: #667eea; }
        .checkbox-group { display: flex; align-items: center; gap: 10px; margin: 15px 0; }
        button {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transition: all 0.3s;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .output-box {
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            min-height: 200px;
            max-height: 500px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin-top: 20px;
        }
        .streaming { display: none; color: #667eea; font-weight: 600; margin-top: 10px; }
        .streaming.active { display: flex; align-items: center; gap: 10px; }
        .spinner {
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #495057; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 Travel Assistant</h1>
            <p>AI-Powered Trip Planning</p>
        </div>
        <div class="content">
            <label>Enter your travel query:</label>
            <textarea id="query" placeholder="Example: Plan a 3-day trip to Tokyo from Singapore">Plan a 3-day trip to Tokyo from Singapore. Search flights, check weather, and find attractions.</textarea>
            <div class="checkbox-group">
                <input type="checkbox" id="stream" checked>
                <label for="stream" style="margin:0">Enable Streaming</label>
            </div>
            <button id="sendBtn" onclick="sendRequest()">🚀 Send Request</button>
            <div class="streaming" id="streaming"><div class="spinner"></div><span>Processing...</span></div>
            <div class="output-box" id="output"><span style="color: #6c757d;">Response will appear here...</span></div>
        </div>
    </div>
    <script>
        const API_URL = window.location.origin;
        
        async function sendRequest() {
            const query = document.getElementById('query').value.trim();
            const stream = document.getElementById('stream').checked;
            const output = document.getElementById('output');
            const btn = document.getElementById('sendBtn');
            const streaming = document.getElementById('streaming');
            
            if (!query) { alert('Please enter a query!'); return; }
            
            output.textContent = '';
            btn.disabled = true;
            btn.textContent = '⏳ Processing...';
            streaming.classList.add('active');
            
            try {
                if (stream) {
                    const response = await fetch(`${API_URL}/travel-assistant`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query, stream: true })
                    });
                    
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data === '[DONE]') {
                                    output.textContent += '\\n\\n✅ Complete!';
                                    continue;
                                }
                                try {
                                    const parsed = JSON.parse(data);
                                    if (parsed.content) {
                                        output.textContent += parsed.content;
                                        output.scrollTop = output.scrollHeight;
                                    }
                                } catch (e) {}
                            }
                        }
                    }
                } else {
                    const response = await fetch(`${API_URL}/travel-assistant`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query, stream: false })
                    });
                    const data = await response.json();
                    output.textContent = data.response || data.error || 'No response';
                }
            } catch (error) {
                output.textContent = `Error: ${error.message}`;
            } finally {
                btn.disabled = false;
                btn.textContent = '🚀 Send Request';
                streaming.classList.remove('active');
            }
        }
        
        document.getElementById('query').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendRequest();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


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
