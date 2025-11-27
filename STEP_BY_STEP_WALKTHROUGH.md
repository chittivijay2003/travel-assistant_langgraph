# 🎬 Step-by-Step Request Walkthrough

This document explains **exactly** what happens when you send a request to the Travel Assistant, line by line.

---

## 📝 Sample Request

```bash
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a 3-day trip to Tokyo from Singapore. Search flights, check weather, and find attractions.",
    "stream": false
  }'
```

---

## 🔄 Complete Execution Flow

### **STEP 1: Request Arrives at FastAPI** 🌐

**File:** `server.py`  
**Line:** ~145  
**Function:** `travel_assistant()`

```python
@app.post("/travel-assistant")
async def travel_assistant(request: TravelRequest):
    logger.info(f"📝 Query: {request.query[:100]}...")
```

**What Happens:**
1. FastAPI receives HTTP POST request
2. Pydantic validates request body
3. Creates `TravelRequest` object
4. Extracts `query` and `stream` fields

**Variables at This Point:**
```python
request.query = "Plan a 3-day trip to Tokyo from Singapore..."
request.stream = False
```

**Debug:** Set breakpoint here to see the incoming request

---

### **STEP 2: Enhanced System Prompt Created** 🔧

**File:** `server.py`  
**Line:** ~150  

```python
system_message = HumanMessage(content="""You are a helpful travel assistant. When users ask about trip planning:
1. ALWAYS call the available tools (search_flights, get_weather, find_attractions) to gather information
2. Use default dates (2025-12-01) if not specified
3. Do NOT ask for additional information - be proactive and use the tools immediately
4. After gathering data from tools, create a comprehensive travel plan

User query: """ + request.query)
```

**What Happens:**
1. Creates enhanced prompt with instructions
2. Tells LLM to be proactive (don't ask for more info)
3. Instructs to use default dates
4. Wraps user query with system instructions

**Variables at This Point:**
```python
system_message.content = "You are a helpful travel assistant...\n\nUser query: Plan a 3-day trip..."
```

**Why This Matters:** This is why the LLM calls tools immediately instead of asking for dates!

---

### **STEP 3: Initial State Prepared** 📝

**File:** `server.py`  
**Line:** ~158  

```python
initial_state = {"messages": [system_message]}
```

**What Happens:**
1. Creates graph state dictionary
2. Initializes with enhanced system message
3. This becomes the starting point for LangGraph

**State Structure:**
```python
{
    "messages": [
        HumanMessage(content="You are a helpful travel assistant...User query: Plan...")
    ]
}
```

---

### **STEP 4: Graph Execution Begins** 📡

**File:** `server.py`  
**Line:** ~165  

```python
async for event in app_graph.astream(initial_state):
```

**What Happens:**
1. Passes initial state to compiled LangGraph
2. Graph starts executing from entry point ("agent")
3. Begins streaming events asynchronously

**Graph Structure:**
```
START → agent → [conditional: tools or END]
              ↓
            tools → agent (loop)
```

---

### **STEP 5: Agent Node - Round 1** 🤖

**File:** `server.py`  
**Line:** 82  
**Function:** `call_model()`

```python
async def call_model(state: AgentState):
    logger.info("🤖 Agent processing...")
    await asyncio.sleep(0.5)  # Visible delay
    response = await llm_with_tools.ainvoke(state["messages"])
```

**What Happens:**
1. Agent node receives state
2. Sleeps 0.5s (for visible streaming)
3. LLM analyzes the enhanced prompt
4. LLM decides to call tools based on instructions
5. Returns response with `tool_calls` array

**State at Entry:**
```python
state = {
    "messages": [
        HumanMessage("You are a helpful travel assistant...Plan a 3-day trip to Tokyo from Singapore...")
    ]
}
```

**LLM Analysis:**
- Sees: "Plan a 3-day trip"
- Identifies: Need flights, weather, attractions
- Has instructions: "ALWAYS call the available tools"
- Decision: Call all 3 tools

**Response After LLM Call:**
```python
response = AIMessage(
    content="",  # Empty initially
    tool_calls=[
        {
            "name": "search_flights",
            "args": {"origin": "Singapore", "destination": "Tokyo", "date": "2025-12-01"},
            "id": "call_abc123"
        },
        {
            "name": "get_weather",
            "args": {"location": "Tokyo", "date": "2025-12-01"},
            "id": "call_def456"
        },
        {
            "name": "find_attractions",
            "args": {"location": "Tokyo", "category": "all"},
            "id": "call_ghi789"
        }
    ]
)
```

**Debug:** Inspect `response.tool_calls` to see what tools LLM wants to call

---

### **STEP 6: Router Decision - Round 1** 🔀

**File:** `server.py`  
**Line:** 92  
**Function:** `should_continue()`

```python
def should_continue(state: AgentState):
    logger.info("🔀 Router: Determining next step...")
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        logger.info(f"➡️  Router decision: TOOLS ({len(last_message.tool_calls)} tool calls pending)")
        return "tools"
    else:
        logger.info("➡️  Router decision: END")
        return "__end__"
```

**What Happens:**
1. Router checks last message in state
2. Finds `tool_calls` array (3 tools)
3. Decides to route to "tools" node
4. Graph will execute tools next

**Decision Logic:**
```python
last_message.tool_calls = [
    {name: "search_flights", ...},
    {name: "get_weather", ...},
    {name: "find_attractions", ...}
]

# Has tool_calls? Yes → route to "tools"
```

**Debug:** Watch the routing decision being made

---

### **STEP 7: Tool Execution Node** 🔧

**File:** `server.py`  
**Line:** 103  
**Function:** `tool_node()`

```python
async def tool_node(state: AgentState):
    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        logger.info(f"🔧 Executing tool: {tool_name}")
        await asyncio.sleep(0.8)  # Visible delay per tool
        
        # Find and execute tool
        tool_result = None
        for t in tools:
            if t.name == tool_name:
                tool_result = t.invoke(tool_args)
                break
        
        results.append(ToolMessage(
            content=tool_result,
            tool_call_id=tool_id,
            name=tool_name
        ))
    
    return {"messages": results}
```

**What Happens:**
1. Loops through each tool_call (3 times)
2. Sleeps 0.8s per tool (visible delay)
3. Finds matching tool function
4. Executes tool with arguments
5. Collects results in ToolMessage objects

**Loop Iterations:**

#### **Iteration 1: search_flights**
```python
tool_call = {
    "name": "search_flights",
    "args": {"origin": "Singapore", "destination": "Tokyo", "date": "2025-12-01"}
}

# Executes search_flights tool (Line 52)
tool_result = {
    "flights": [
        {"airline": "Singapore Airlines", "price_usd": 450, ...},
        {"airline": "ANA", "price_usd": 420, ...},
        {"airline": "JAL", "price_usd": 480, ...}
    ]
}

# Creates ToolMessage
results.append(ToolMessage(
    content='{"flights": [...]}',
    tool_call_id="call_abc123",
    name="search_flights"
))
```

#### **Iteration 2: get_weather**
```python
tool_call = {
    "name": "get_weather",
    "args": {"location": "Tokyo", "date": "2025-12-01"}
}

# Executes get_weather tool (Line 67)
tool_result = {
    "location": "Tokyo",
    "forecast": [
        {"day": "Day 1", "condition": "Sunny", "high_c": 22, ...},
        {"day": "Day 2", "condition": "Partly Cloudy", ...},
        {"day": "Day 3", "condition": "Clear", ...}
    ]
}

# Creates ToolMessage
results.append(ToolMessage(...))
```

#### **Iteration 3: find_attractions**
```python
tool_call = {
    "name": "find_attractions",
    "args": {"location": "Tokyo", "category": "all"}
}

# Executes find_attractions tool (Line 82)
tool_result = {
    "attractions": [
        {"name": "Senso-ji Temple", "type": "Cultural", "rating": 4.5},
        {"name": "Tokyo Tower", "type": "Landmark", "rating": 4.3},
        ...
    ]
}

# Creates ToolMessage
results.append(ToolMessage(...))
```

**Debug:** Watch each tool execute in the loop

---

### **STEP 8: State Updated with Tool Results** 📊

**After Tool Node:**
```python
state = {
    "messages": [
        HumanMessage("You are a helpful travel assistant...Plan a 3-day trip..."),
        AIMessage(content="", tool_calls=[...]),  # Agent's tool request
        ToolMessage(content='{"flights": [...]}', name="search_flights"),
        ToolMessage(content='{"forecast": [...]}', name="get_weather"),
        ToolMessage(content='{"attractions": [...]}', name="find_attractions")
    ]
}
```

**Conversation History Now Has:**
1. Original user query (enhanced)
2. LLM's request to call tools
3. Results from search_flights
4. Results from get_weather
5. Results from find_attractions

---

### **STEP 9: Agent Node - Round 2** 🤖

**File:** `server.py`  
**Line:** 82 (again)  
**Function:** `call_model()`

```python
async def call_model(state: AgentState):
    logger.info("🤖 Agent processing...")
    await asyncio.sleep(0.5)
    response = await llm_with_tools.ainvoke(state["messages"])
```

**What Happens:**
1. Agent receives updated state with tool results
2. LLM now has all the data it needs
3. Synthesizes information into travel plan
4. Returns final response with NO tool_calls

**LLM Sees:**
- Flight options: 3 airlines, prices, times
- Weather: 3-day forecast, temperatures
- Attractions: 5 top places to visit
- Task: Create comprehensive travel plan

**Response After LLM Call:**
```python
response = AIMessage(
    content="""Based on the search results, here's your comprehensive 3-day Tokyo travel plan:

🛫 **Flights from Singapore to Tokyo**
I found three excellent direct flight options:
1. Singapore Airlines (SQ638) - $450 USD, departing 7:00 AM
2. ANA (NH842) - $420 USD, departing 11:30 AM ✨ Best value!
3. JAL (JL712) - $480 USD, departing 9:15 AM

🌤️ **Weather Forecast for Tokyo**
- Day 1: Sunny, 22°C high / 15°C low
- Day 2: Partly Cloudy, 20°C high / 14°C low
- Day 3: Clear, 23°C high / 16°C low

Perfect weather for sightseeing!

🗼 **Top Attractions**
1. Senso-ji Temple (Cultural) - Rating 4.5/5
2. Tokyo Tower (Landmark) - Rating 4.3/5
3. Meiji Shrine (Cultural) - Rating 4.6/5
4. Shibuya Crossing (Entertainment) - Rating 4.4/5
5. Ueno Park (Nature) - Rating 4.5/5

📅 **Suggested 3-Day Itinerary**

**Day 1: Traditional Tokyo**
- Morning: Visit Senso-ji Temple in Asakusa
- Afternoon: Explore Meiji Shrine
- Evening: Experience Shibuya Crossing

**Day 2: Modern & Cultural**
- Morning: Tokyo Tower observation
- Afternoon: Ueno Park and museums
- Evening: Shopping and dining

**Day 3: Final Exploration**
- Morning: Last-minute shopping
- Afternoon: Relax at hotel before flight

💡 **Travel Tips**
- Book the ANA flight for best value
- Weather is perfect - pack light layers
- All attractions are easily accessible via Tokyo Metro

Have an amazing trip! 🌸""",
    tool_calls=[]  # No more tool calls - we're done!
)
```

**Debug:** Inspect the full travel plan in `response.content`

---

### **STEP 10: Router Decision - Round 2** 🔀

**File:** `server.py`  
**Line:** 92 (again)  
**Function:** `should_continue()`

```python
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    else:
        logger.info("➡️  Router decision: END")
        return "__end__"
```

**What Happens:**
1. Router checks last message
2. Finds NO tool_calls (empty array)
3. Decides to route to END
4. Graph execution will terminate

**Decision Logic:**
```python
last_message.tool_calls = []  # Empty!

# Has tool_calls? No → route to END
```

---

### **STEP 11: Final Response Sent** 📤

**File:** `server.py`  
**Line:** ~200  

```python
result = await app_graph.ainvoke(initial_state)
messages = result.get("messages", [])

if messages:
    final_message = messages[-1]
    response_content = final_message.content
    
    return TravelResponse(
        response=response_content,
        status="success"
    )
```

**What Happens:**
1. Graph execution completes
2. Extracts final message from state
3. Gets content (the travel plan)
4. Returns TravelResponse to client

**Final State:**
```python
{
    "messages": [
        HumanMessage(...),           # Original query
        AIMessage(tool_calls=[...]), # Tool request
        ToolMessage(...),            # search_flights result
        ToolMessage(...),            # get_weather result
        ToolMessage(...),            # find_attractions result
        AIMessage(content="..."),    # Final travel plan ← THIS ONE
    ]
}
```

**Response to Client:**
```json
{
    "response": "Based on the search results, here's your comprehensive 3-day Tokyo travel plan...",
    "status": "success"
}
```

---

## 🔄 Complete Message Flow Summary

```
Message 1: HumanMessage
├─ Type: User Input (Enhanced)
├─ Content: "You are a helpful travel assistant...Plan a 3-day trip to Tokyo..."
└─ Purpose: Initial query with proactive instructions

Message 2: AIMessage (Round 1)
├─ Type: LLM Response
├─ Content: "" (empty)
├─ Tool Calls: [search_flights, get_weather, find_attractions]
└─ Purpose: Request tool data

Message 3: ToolMessage
├─ Type: Tool Result
├─ Name: search_flights
├─ Content: {"flights": [...]}
└─ Purpose: Provide flight data

Message 4: ToolMessage
├─ Type: Tool Result
├─ Name: get_weather
├─ Content: {"forecast": [...]}
└─ Purpose: Provide weather data

Message 5: ToolMessage
├─ Type: Tool Result
├─ Name: find_attractions
├─ Content: {"attractions": [...]}
└─ Purpose: Provide attractions data

Message 6: AIMessage (Round 2)
├─ Type: LLM Response
├─ Content: "Based on the search results, here's your comprehensive 3-day Tokyo travel plan..."
├─ Tool Calls: [] (none)
└─ Purpose: Final travel plan → SENT TO USER
```

---

## ⏱️ Timing Breakdown

| Step | Duration | Reason |
|------|----------|--------|
| Request processing | ~0.01s | FastAPI validation |
| Agent Round 1 | ~0.5s + LLM time | Delay + LLM analysis |
| Tool execution | ~2.4s | 0.8s × 3 tools |
| Agent Round 2 | ~0.5s + LLM time | Delay + synthesis |
| Response formatting | ~0.01s | JSON serialization |
| **Total** | **~5-8 seconds** | Visible workflow! |

---

## 🎯 Key Takeaways

1. **Enhanced Prompt** prevents LLM from asking for more info
2. **Graph loops** between agent and tools until no more tool calls
3. **State accumulates** all messages for context
4. **Strategic delays** make the process visible
5. **Router decides** when to end based on tool_calls presence

---

**🎉 Now you understand exactly how each request flows through the system!**
