# 🐛 VS Code Debugging Guide - Travel Assistant

This guide explains how to debug the Travel Assistant application step-by-step using VS Code debugger.

---

## 🚀 Quick Start

### 1. **Install Python Extension**
Make sure you have the **Python extension** installed in VS Code:
- Extension ID: `ms-python.python`
- Includes debugpy debugger

### 2. **Open Debug Panel**
- Press `Cmd+Shift+D` (Mac) or `Ctrl+Shift+D` (Windows/Linux)
- Or click the **Debug icon** (bug symbol) in the left sidebar

### 3. **Select Debug Configuration**
Choose **"Debug FastAPI with Uvicorn"** from the dropdown at the top

### 4. **Start Debugging**
Press `F5` or click the **green play button**

---

## 🎯 Strategic Breakpoints

Here are the key locations where you should set breakpoints to understand the flow:

### **File: `server.py`**

#### **Breakpoint 1: Request Entry Point**
```python
@app.post("/travel-assistant")
async def travel_assistant(request: TravelRequest):
    """Main travel assistant endpoint."""
    logger.info(f"📝 Query: {request.query[:100]}...")  # <-- SET BREAKPOINT HERE
```
**What to inspect:**
- `request.query` - User's travel query
- `request.stream` - Whether streaming is enabled

---

#### **Breakpoint 2: System Message Creation**
```python
    system_message = HumanMessage(content="""You are a helpful travel assistant...
    
User query: """ + request.query)

    initial_state = {"messages": [system_message]}  # <-- SET BREAKPOINT HERE
```
**What to inspect:**
- `system_message.content` - The enhanced prompt with instructions
- `initial_state` - Initial graph state

---

#### **Breakpoint 3: Streaming Event Generator**
```python
async def event_generator():
    try:
        step_number = 0
        async for event in app_graph.astream(initial_state):  # <-- SET BREAKPOINT HERE
            step_number += 1
```
**What to inspect:**
- `event` - Current graph execution step
- `step_number` - Which step we're on
- Loop through to see each node execution

---

#### **Breakpoint 4: Agent Node (LLM Thinking)**
```python
async def call_model(state: AgentState):
    """Call the LLM with tools bound."""
    logger.info("🤖 Agent processing...")
    await asyncio.sleep(0.5)  # <-- SET BREAKPOINT HERE
    response = await llm_with_tools.ainvoke(state["messages"])
```
**What to inspect:**
- `state["messages"]` - Conversation history
- `response` - LLM's response (after stepping over ainvoke)
- `response.tool_calls` - Which tools LLM wants to call

---

#### **Breakpoint 5: Router Decision**
```python
def should_continue(state: AgentState):
    """Determine if we should call tools or end."""
    logger.info("🔀 Router: Determining next step...")
    messages = state["messages"]
    last_message = messages[-1]  # <-- SET BREAKPOINT HERE
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
```
**What to inspect:**
- `last_message` - The last message in the conversation
- `last_message.tool_calls` - Tool calls if any
- Watch which path is taken (tools vs END)

---

#### **Breakpoint 6: Tool Execution**
```python
async def tool_node(state: AgentState):
    """Execute tool calls manually with visible delay."""
    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:  # <-- SET BREAKPOINT HERE
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
```
**What to inspect:**
- `tool_call["name"]` - Which tool is being called
- `tool_call["args"]` - Arguments passed to the tool
- `tool_result` - Result from tool execution

---

#### **Breakpoint 7: Individual Tool Functions**
```python
@tool
def search_flights(origin: str, destination: str, date: str = "2025-12-01") -> str:
    """Search for flight options."""
    flights = {  # <-- SET BREAKPOINT HERE
        "flights": [...]
    }
```
**What to inspect:**
- `origin`, `destination`, `date` - Tool arguments
- `flights` - Mock data being returned

---

## 📊 Step-by-Step Execution Flow

When you send this request:
```
"Plan a 3-day trip to Tokyo from Singapore. Search flights, check weather, and find attractions."
```

Here's what happens (follow with debugger):

### **Step 1: Request Arrives** 🌐
- **Breakpoint 1** hits
- FastAPI receives POST request
- Request object contains query and stream flag

### **Step 2: State Initialization** 🔧
- **Breakpoint 2** hits
- System message created with instructions
- Initial state prepared with enhanced prompt

### **Step 3: Stream Starts** 📡
- **Breakpoint 3** hits
- Event generator begins
- Graph starts executing asynchronously

### **Step 4: Agent Node (First Call)** 🤖
- **Breakpoint 4** hits
- LLM receives the query
- 0.5s delay for visibility
- LLM analyzes and decides to call tools
- Returns response with `tool_calls` array

### **Step 5: Router Decision** 🔀
- **Breakpoint 5** hits
- Checks last message for tool_calls
- Finds tool calls → routes to "tools" node

### **Step 6: Tool Execution Node** 🔧
- **Breakpoint 6** hits
- Iterates through each tool call:
  1. `search_flights` (Singapore → Tokyo)
  2. `get_weather` (Tokyo, 3 days)
  3. `find_attractions` (Tokyo, limit 5)

### **Step 7: Individual Tools Execute** 🛫🌤️🗼
- **Breakpoint 7** hits (for each tool)
- Tool receives arguments
- Returns mock data
- 0.8s delay per tool

### **Step 8: Back to Agent** 🔄
- **Breakpoint 4** hits again
- Agent receives tool results
- LLM synthesizes information
- Creates comprehensive travel plan
- No more tool_calls in response

### **Step 9: Router to END** ✅
- **Breakpoint 5** hits again
- No tool_calls found
- Routes to END
- Stream completes

### **Step 10: Response Sent** 📤
- **Breakpoint 3** continues streaming
- Final response sent to client
- Stream marked as [DONE]

---

## 🎬 Debugging Session Example

### **1. Set All Breakpoints**
Open `server.py` and click in the left margin next to these lines:
- Line ~150: `logger.info(f"📝 Query: {request.query[:100]}...")`
- Line ~160: `initial_state = {"messages": [system_message]}`
- Line ~170: `async for event in app_graph.astream(initial_state):`
- Line ~80: `await asyncio.sleep(0.5)`
- Line ~100: `last_message = messages[-1]`
- Line ~120: `for tool_call in last_message.tool_calls:`
- Line ~35: `flights = {`

### **2. Start Debugging**
- Press `F5`
- Wait for server to start
- You'll see: `"Application startup complete"`

### **3. Send Test Request**
Open a new terminal and run:
```bash
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a 3-day trip to Tokyo from Singapore. Search flights, check weather, and find attractions.",
    "stream": false
  }'
```

Or use the Web UI: http://localhost:8000/ui

### **4. Follow the Breakpoints**
- **First hit**: Request entry point
  - Inspect `request.query`
  - Press `F10` (Step Over) or `F5` (Continue)

- **Second hit**: Agent node
  - Inspect `state["messages"]`
  - Watch `response` after LLM call
  - Check `response.tool_calls`

- **Third hit**: Tool execution
  - See which tools are called
  - Watch the loop iterate 3 times

- **Fourth hit**: Agent node again
  - Now has tool results
  - Creates final response
  - No more tool_calls

### **5. Inspect Variables**
Use the **Variables panel** on the left to see:
- Local variables
- Function arguments
- Return values
- Object properties

### **6. Use Debug Console**
Type commands to inspect:
```python
state["messages"][-1].content
tool_call["name"]
len(response.tool_calls)
```

---

## 🔍 Key Variables to Watch

| Variable | Location | What to Inspect |
|----------|----------|----------------|
| `request.query` | Breakpoint 1 | User's travel query |
| `system_message.content` | Breakpoint 2 | Enhanced prompt with instructions |
| `state["messages"]` | Breakpoint 4 | Conversation history |
| `response.tool_calls` | Breakpoint 4 | Tools LLM wants to call |
| `last_message` | Breakpoint 5 | Last message for routing decision |
| `tool_call["name"]` | Breakpoint 6 | Which tool is executing |
| `tool_call["args"]` | Breakpoint 6 | Arguments passed to tool |
| `tool_result` | Breakpoint 6 | Data returned from tool |
| `event` | Breakpoint 3 | Current graph execution event |

---

## 🎓 Advanced Debugging Tips

### **1. Conditional Breakpoints**
Right-click a breakpoint → Edit Breakpoint → Add condition:
```python
tool_name == "search_flights"
```

### **2. Logpoints**
Instead of breakpoints, add log messages without stopping:
```python
Tool: {tool_name}, Args: {tool_args}
```

### **3. Watch Expressions**
Add to Watch panel:
```python
len(state["messages"])
response.tool_calls[0]["name"] if response.tool_calls else None
```

### **4. Call Stack**
View the function call hierarchy to understand how you got to current point

### **5. Step Into vs Step Over**
- `F11` (Step Into): Go inside function calls
- `F10` (Step Over): Execute function and move to next line
- `Shift+F11` (Step Out): Exit current function

---

## 📋 Common Debug Scenarios

### **Scenario 1: LLM Not Calling Tools**
**Set breakpoint at:** Line ~80 (call_model)
**Check:**
- Is `system_message` properly formatted?
- Are tools bound to LLM? (`llm_with_tools`)
- What's in `response.tool_calls`?

### **Scenario 2: Tools Not Executing**
**Set breakpoint at:** Line ~100 (should_continue)
**Check:**
- Does `last_message` have `tool_calls`?
- Is router returning "tools" or END?

### **Scenario 3: Wrong Tool Arguments**
**Set breakpoint at:** Line ~120 (tool_node loop)
**Check:**
- `tool_call["args"]` values
- Are they matching expected format?

### **Scenario 4: Streaming Not Working**
**Set breakpoint at:** Line ~170 (event_generator)
**Check:**
- Is `request.stream` true?
- Are events being generated?
- Check network tab in browser

---

## 🛠️ Debugging Tools Overview

| Tool | Shortcut | Purpose |
|------|----------|---------|
| Start Debugging | `F5` | Begin debug session |
| Stop | `Shift+F5` | End debug session |
| Restart | `Cmd+Shift+F5` | Restart debugger |
| Continue | `F5` | Run to next breakpoint |
| Step Over | `F10` | Execute current line |
| Step Into | `F11` | Go inside function |
| Step Out | `Shift+F11` | Exit current function |
| Toggle Breakpoint | `F9` | Add/remove breakpoint |

---

## 📸 Visual Debugging Flow

```
1. REQUEST ARRIVES
   ↓
   [Breakpoint 1: Entry Point]
   - Check request.query
   - Check request.stream
   ↓

2. INITIALIZE STATE
   ↓
   [Breakpoint 2: State Setup]
   - Check system_message
   - Check initial_state
   ↓

3. START GRAPH EXECUTION
   ↓
   [Breakpoint 4: Agent Node - Round 1]
   - LLM analyzes query
   - Decides to call tools
   - Returns tool_calls
   ↓

4. ROUTER DECISION
   ↓
   [Breakpoint 5: Router - Round 1]
   - Detects tool_calls
   - Routes to "tools"
   ↓

5. EXECUTE TOOLS
   ↓
   [Breakpoint 6: Tool Loop]
   - Call search_flights
   - Call get_weather
   - Call find_attractions
   ↓
   [Breakpoint 7: Individual Tools]
   - Execute each tool
   - Return mock data
   ↓

6. BACK TO AGENT
   ↓
   [Breakpoint 4: Agent Node - Round 2]
   - LLM receives tool results
   - Synthesizes information
   - Creates final response
   - No tool_calls
   ↓

7. ROUTER TO END
   ↓
   [Breakpoint 5: Router - Round 2]
   - No tool_calls
   - Routes to END
   ↓

8. STREAM RESPONSE
   ↓
   [Breakpoint 3: Event Generator]
   - Send final response
   - Mark as [DONE]
   ↓

9. COMPLETE ✅
```

---

## 🎯 Try It Now!

1. **Open VS Code**
2. **Open Debug Panel** (`Cmd+Shift+D`)
3. **Set breakpoints** at the 7 locations listed above
4. **Select** "Debug FastAPI with Uvicorn"
5. **Press F5** to start
6. **Send a request** via curl or Web UI
7. **Step through** each breakpoint to see the flow!

---

**🎉 Happy Debugging! You'll now see exactly how the Travel Assistant processes requests step-by-step!**
