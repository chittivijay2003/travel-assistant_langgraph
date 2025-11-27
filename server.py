#!/usr/bin/env python3
"""
FastAPI Server for Travel Assistant
Uses the working implementation from run_assistant.py
"""

import os
import json
import logging
import asyncio
from typing import TypedDict, Annotated, Sequence
from functools import wraps

# LangChain imports
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# FastAPI imports
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Other imports
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# Initialize LLM
MODEL_NAME = "gemini-2.5-flash"
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME, temperature=0.7, google_api_key=GOOGLE_API_KEY
)

logger.info(f"✅ Initialized {MODEL_NAME}")


# Define tools
@tool
def search_flights(origin: str, destination: str, date: str = "2025-12-01") -> str:
    """Search for flight options between origin and destination."""
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
logger.info(f"✅ Registered {len(tools)} tools")


# ============================================
# RETRY LOGIC WITH EXPONENTIAL BACKOFF
# ============================================


def retry_with_exponential_backoff_async(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
):
    """Decorator for retry logic with exponential backoff (asynchronous)."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    logger.debug(
                        f"🔄 Attempt {attempt + 1}/{max_retries} for {func.__name__}"
                    )
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"✅ {func.__name__} succeeded on attempt {attempt + 1}"
                        )
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

    return decorator


logger.info("✅ Retry logic decorator defined")


# Build LangGraph workflow
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


llm_with_tools = llm.bind_tools(tools)


@retry_with_exponential_backoff_async(max_retries=3, initial_delay=1.0)
async def call_model(state: AgentState):
    logger.info("🤖 Agent processing...")
    # Add small delay to show streaming process
    await asyncio.sleep(0.5)
    response = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(f"🔧 Routing to tools ({len(last_message.tool_calls)} calls)")
        return "tools"
    logger.info("✅ Workflow complete")
    return END


async def tool_node(state: AgentState):
    """Execute tool calls manually with visible delay."""
    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        logger.info(f"🔧 Executing tool: {tool_name}")
        # Add delay to show tool execution process
        await asyncio.sleep(0.8)

        tool_result = None
        for t in tools:
            if t.name == tool_name:
                tool_result = t.invoke(tool_args)
                break

        results.append(
            ToolMessage(
                content=tool_result if tool_result else "Tool not found",
                tool_call_id=tool_id,
                name=tool_name,
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

app_graph = workflow.compile()
logger.info("✅ LangGraph workflow compiled")

# Create FastAPI app
app = FastAPI(
    title="Travel Assistant API",
    description="AI-powered travel planning with LangGraph and Gemini 2.5 Flash",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TravelRequest(BaseModel):
    query: str
    stream: bool = False


class TravelResponse(BaseModel):
    response: str
    status: str = "success"


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Travel Assistant API",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "tools": [t.name for t in tools],
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "tools": [t.name for t in tools],
        "api_key_configured": bool(GOOGLE_API_KEY),
    }


@app.post("/travel-assistant")
async def travel_assistant(request: TravelRequest):
    """
    Main travel assistant endpoint.

    Example request:
    {
        "query": "Plan a 3-day trip to Tokyo from Singapore",
        "stream": false
    }
    """
    logger.info(f"📝 Query: {request.query[:100]}...")

    try:
        # Enhanced system message to make LLM more proactive
        system_message = HumanMessage(
            content="""You are a helpful travel assistant. When users ask about trip planning:
1. ALWAYS call the available tools (search_flights, get_weather, find_attractions) to gather information
2. Use default dates (2025-12-01) if not specified
3. Do NOT ask for additional information - be proactive and use the tools immediately
4. After gathering data from tools, create a comprehensive travel plan

User query: """
            + request.query
        )

        initial_state = {"messages": [system_message]}

        if request.stream:
            # Streaming response
            async def event_generator():
                try:
                    step_number = 0
                    async for event in app_graph.astream(initial_state):
                        step_number += 1
                        for node_name, node_output in event.items():
                            # Send node execution info
                            yield f"data: {json.dumps({'step': step_number, 'node': node_name, 'type': 'node_start'})}\n\n"
                            await asyncio.sleep(0.3)  # Small delay for visibility

                            if node_name == "agent":
                                messages = node_output.get("messages", [])
                                if messages:
                                    last_message = messages[-1]

                                    # Check if agent is making tool calls or giving final response
                                    if (
                                        hasattr(last_message, "tool_calls")
                                        and last_message.tool_calls
                                    ):
                                        for tc in last_message.tool_calls:
                                            yield f"data: {json.dumps({'type': 'tool_request', 'tool': tc['name'], 'args': tc['args']})}\n\n"
                                            await asyncio.sleep(0.2)
                                    elif (
                                        hasattr(last_message, "content")
                                        and last_message.content
                                    ):
                                        # This is the final response - send it with special type
                                        content = last_message.content
                                        if isinstance(content, list):
                                            content = " ".join(
                                                [
                                                    item.get("text", "")
                                                    if isinstance(item, dict)
                                                    else str(item)
                                                    for item in content
                                                ]
                                            )
                                        yield f"data: {json.dumps({'type': 'final_response', 'content': content})}\n\n"

                            elif node_name == "tools":
                                messages = node_output.get("messages", [])
                                for msg in messages:
                                    if hasattr(msg, "name"):
                                        yield f"data: {json.dumps({'type': 'tool_result', 'tool': msg.name, 'result': msg.content[:200]})}\n\n"
                                        await asyncio.sleep(0.3)

                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logger.error(f"❌ Streaming error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")
        else:
            # Non-streaming response
            result = await app_graph.ainvoke(initial_state)
            final_message = result["messages"][-1]

            # Extract content properly
            if hasattr(final_message, "content"):
                response_content = final_message.content
                # Handle if content is a list (for some LLM responses)
                if isinstance(response_content, list):
                    response_content = " ".join(
                        [
                            item.get("text", "")
                            if isinstance(item, dict)
                            else str(item)
                            for item in response_content
                        ]
                    )
            else:
                response_content = str(final_message)

            logger.info(f"✅ Response generated ({len(response_content)} chars)")

            return TravelResponse(response=response_content, status="success")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return JSONResponse(
            status_code=500, content={"error": str(e), "status": "error"}
        )


@app.get("/docs-info")
async def docs_info():
    """Information about API documentation."""
    return {
        "message": "API Documentation available",
        "swagger_ui": "/docs",
        "redoc": "/redoc",
        "streaming_ui": "/ui",
        "example_request": {
            "url": "POST /travel-assistant",
            "body": {
                "query": "Plan a 3-day trip to Tokyo from Singapore",
                "stream": False,
            },
        },
    }


@app.get("/ui", response_class=HTMLResponse)
async def streaming_ui():
    """Interactive streaming test UI."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Travel Assistant - Streaming Test</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

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

        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        .header p {
            opacity: 0.9;
        }

        .status-bar {
            background: #f8f9fa;
            padding: 15px 30px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #28a745;
            animation: pulse 2s infinite;
        }

        .status-dot.disconnected {
            background: #dc3545;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .content {
            padding: 30px;
        }

        .input-section {
            margin-bottom: 30px;
        }

        .input-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #495057;
        }

        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            resize: vertical;
            min-height: 80px;
            transition: border-color 0.3s;
        }

        textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }

        .button-group {
            display: flex;
            gap: 10px;
        }

        button {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
        }

        .btn-secondary:hover {
            background: #5a6268;
        }

        .output-section {
            margin-top: 30px;
        }

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
        }

        .streaming-indicator {
            display: none;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
            color: #667eea;
            font-weight: 600;
        }

        .streaming-indicator.active {
            display: flex;
        }

        .spinner {
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .metric-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }

        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }

        .metric-label {
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }

        .sample-queries {
            margin-top: 20px;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 8px;
        }

        .sample-queries h3 {
            color: #0066cc;
            margin-bottom: 10px;
            font-size: 14px;
        }

        .sample-query {
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.2s;
            font-size: 13px;
        }

        .sample-query:hover {
            background: #f0f8ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 Travel Assistant</h1>
            <p>Real-time Streaming Test Interface</p>
        </div>

        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">Server: Checking...</span>
            </div>
            <div id="serverInfo"></div>
        </div>

        <div class="content">
            <div class="input-section">
                <div class="input-group">
                    <label for="queryInput">Enter your travel query:</label>
                    <textarea 
                        id="queryInput" 
                        placeholder="Example: Plan a 3-day trip to Tokyo from Singapore. Search flights, get weather forecast, and find top attractions."
                    >Plan a 3-day trip to Tokyo from Singapore. Search flights, check weather, and find attractions.</textarea>
                </div>

                <div class="input-group checkbox-group">
                    <input type="checkbox" id="streamCheckbox" checked>
                    <label for="streamCheckbox" style="margin-bottom: 0;">Enable Streaming</label>
                </div>

                <div class="button-group">
                    <button class="btn-primary" id="sendBtn">
                        🚀 Send Request
                    </button>
                    <button class="btn-secondary" id="clearBtn">
                        🗑️ Clear Output
                    </button>
                </div>

                <div class="sample-queries">
                    <h3>📝 Sample Queries (Click to use):</h3>
                    <div class="sample-query" data-query="Plan a 3-day trip to Tokyo from Singapore. Search flights, get weather, and find attractions.">
                        🗾 Tokyo trip planning with all tools
                    </div>
                    <div class="sample-query" data-query="I want to visit Paris next month. Can you search for flights from New York and tell me about the weather?">
                        🗼 Paris vacation planning
                    </div>
                    <div class="sample-query" data-query="Find me flights to London, check the weather forecast, and suggest top tourist attractions.">
                        🇬🇧 London travel package
                    </div>
                </div>
            </div>

            <div class="streaming-indicator" id="streamingIndicator">
                <div class="spinner"></div>
                <span>Streaming response...</span>
            </div>

            <div class="output-section">
                <label>Response:</label>
                <div class="output-box" id="outputBox">
                    <span style="color: #6c757d;">Output will appear here...</span>
                </div>
            </div>

            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value" id="charCount">0</div>
                    <div class="metric-label">Characters</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="chunkCount">0</div>
                    <div class="metric-label">Chunks</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="duration">0s</div>
                    <div class="metric-label">Duration</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;
        const outputBox = document.getElementById('outputBox');
        const queryInput = document.getElementById('queryInput');
        const streamCheckbox = document.getElementById('streamCheckbox');
        const sendBtn = document.getElementById('sendBtn');
        const clearBtn = document.getElementById('clearBtn');
        const streamingIndicator = document.getElementById('streamingIndicator');
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const serverInfo = document.getElementById('serverInfo');

        let charCount = 0;
        let chunkCount = 0;
        let startTime = 0;

        async function checkServerHealth() {
            try {
                const response = await fetch(`${API_URL}/health`);
                const data = await response.json();
                
                statusDot.classList.remove('disconnected');
                statusText.textContent = 'Server: Connected ✓';
                serverInfo.textContent = `Model: ${data.model}`;
            } catch (error) {
                statusDot.classList.add('disconnected');
                statusText.textContent = 'Server: Disconnected ✗';
                serverInfo.textContent = 'Check if server is running';
            }
        }

        async function sendRequest() {
            const query = queryInput.value.trim();
            if (!query) {
                alert('Please enter a query!');
                return;
            }

            const stream = streamCheckbox.checked;
            charCount = 0;
            chunkCount = 0;
            startTime = Date.now();
            outputBox.textContent = '';
            updateMetrics();
            sendBtn.disabled = true;
            sendBtn.textContent = '⏳ Processing...';

            if (stream) {
                streamingIndicator.classList.add('active');
                await streamRequest(query);
            } else {
                await regularRequest(query);
            }

            sendBtn.disabled = false;
            sendBtn.textContent = '🚀 Send Request';
            streamingIndicator.classList.remove('active');
        }

        async function streamRequest(query) {
            try {
                const response = await fetch(`${API_URL}/travel-assistant`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, stream: true })
                });

                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

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
                                appendToOutput('\\n\\n✅ Stream complete!');
                                return;
                            }

                            try {
                                const parsed = JSON.parse(data);
                                
                                if (parsed.type === 'node_start') {
                                    appendToOutput(`\\n\\n🔹 Step ${parsed.step}: ${parsed.node.toUpperCase()} node executing...\\n`);
                                    chunkCount++;
                                    updateMetrics();
                                }
                                else if (parsed.type === 'tool_request') {
                                    appendToOutput(`\\n🔧 Calling tool: ${parsed.tool}\\n   Args: ${JSON.stringify(parsed.args, null, 2)}\\n`);
                                    chunkCount++;
                                    updateMetrics();
                                }
                                else if (parsed.type === 'tool_result') {
                                    appendToOutput(`\\n✓ Tool ${parsed.tool} completed\\n`);
                                    chunkCount++;
                                    updateMetrics();
                                }
                                else if (parsed.type === 'final_response' && parsed.content) {
                                    appendToOutput(`\\n\\n${'='.repeat(60)}\\n📋 FINAL TRAVEL PLAN:\\n${'='.repeat(60)}\\n\\n${parsed.content}\\n`);
                                    chunkCount++;
                                    charCount += parsed.content.length;
                                    updateMetrics();
                                }
                                else if (parsed.content) {
                                    appendToOutput(parsed.content);
                                    chunkCount++;
                                    charCount += parsed.content.length;
                                    updateMetrics();
                                }
                                else if (parsed.error) {
                                    appendToOutput(`\\n❌ Error: ${parsed.error}`);
                                }
                            } catch (e) {}
                        }
                    }
                }
            } catch (error) {
                appendToOutput(`\\n❌ Error: ${error.message}`);
            }
        }

        async function regularRequest(query) {
            try {
                const response = await fetch(`${API_URL}/travel-assistant`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, stream: false })
                });

                const data = await response.json();

                if (data.status === 'success') {
                    outputBox.textContent = data.response;
                    charCount = data.response.length;
                    chunkCount = 1;
                } else {
                    outputBox.textContent = `Error: ${data.error || 'Unknown error'}`;
                }
                updateMetrics();
            } catch (error) {
                outputBox.textContent = `Error: ${error.message}`;
            }
        }

        function appendToOutput(text) {
            outputBox.textContent += text;
            outputBox.scrollTop = outputBox.scrollHeight;
        }

        function updateMetrics() {
            document.getElementById('charCount').textContent = charCount;
            document.getElementById('chunkCount').textContent = chunkCount;
            const duration = ((Date.now() - startTime) / 1000).toFixed(1);
            document.getElementById('duration').textContent = `${duration}s`;
        }

        function clearOutput() {
            outputBox.innerHTML = '<span style="color: #6c757d;">Output will appear here...</span>';
            charCount = 0;
            chunkCount = 0;
            updateMetrics();
        }

        document.querySelectorAll('.sample-query').forEach(element => {
            element.addEventListener('click', () => {
                queryInput.value = element.getAttribute('data-query');
            });
        });

        sendBtn.addEventListener('click', sendRequest);
        clearBtn.addEventListener('click', clearOutput);

        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendRequest();
            }
        });

        checkServerHealth();
        setInterval(checkServerHealth, 30000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting server on http://0.0.0.0:8000")
    logger.info("📚 API Docs: http://localhost:8000/docs")
    logger.info("🎨 Streaming UI: http://localhost:8000/ui")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
