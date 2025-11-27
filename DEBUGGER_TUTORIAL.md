# 🎮 VS Code Debugger - Hands-On Tutorial

Follow these steps to debug your first request!

---

## 🚀 Part 1: Setup (5 minutes)

### Step 1: Open Project in VS Code
```bash
cd /Users/chittivijay/Documents/PythonAssignment_Day3/travel-assistant_langgraph
code .
```

### Step 2: Verify Debug Configuration
1. Check that `.vscode/launch.json` exists
2. Open it to see the debug configurations

### Step 3: Open Debug Panel
- Press `Cmd+Shift+D` (Mac) or `Ctrl+Shift+D` (Windows)
- Or click the **Debug icon** (🐛) in left sidebar

---

## 🎯 Part 2: Set Breakpoints (2 minutes)

### Open `server.py`
Find these exact lines and click in the left gutter to add red dots:

#### Breakpoint 1: Line ~145
```python
@app.post("/travel-assistant")
async def travel_assistant(request: TravelRequest):
    logger.info(f"📝 Query: {request.query[:100]}...")  # ← Click here
```

#### Breakpoint 2: Line ~82
```python
async def call_model(state: AgentState):
    logger.info("🤖 Agent processing...")
    await asyncio.sleep(0.5)  # ← Click here
```

#### Breakpoint 3: Line ~92
```python
def should_continue(state: AgentState):
    logger.info("🔀 Router: Determining next step...")
    messages = state["messages"]
    last_message = messages[-1]  # ← Click here
```

#### Breakpoint 4: Line ~103
```python
async def tool_node(state: AgentState):
    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:  # ← Click here
```

**You should now see 4 red dots!** ✅

---

## ▶️ Part 3: Start Debugging (1 minute)

### Step 1: Select Configuration
At the top of Debug panel, select:
```
"Debug FastAPI with Uvicorn"
```

### Step 2: Start Debugger
- Press `F5` or click the green ▶️ button
- Wait for terminal to show: `Application startup complete`

**Server is now running in debug mode!** 🎉

---

## 📨 Part 4: Send Test Request (1 minute)

### Open New Terminal
- Press `` Ctrl+` `` (backtick) or Terminal → New Terminal

### Send Request
```bash
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a trip to Tokyo from Singapore. Search flights, check weather, and find attractions.",
    "stream": false
  }'
```

**The debugger will pause at first breakpoint!** 🛑

---

## 🔍 Part 5: Inspect Variables (10 minutes)

### Breakpoint 1 Hits (Request Entry)

**You'll see:**
- Yellow highlight on Line ~145
- Execution paused
- Variables panel on left shows local variables

#### What to Inspect:
1. **Left Panel → Variables → Local**
   ```
   ▼ request: TravelRequest
     ▶ query: "Plan a trip to Tokyo from Singapore..."
     ▶ stream: false
   ```

2. **Hover over `request.query`**
   - See full query text

3. **Debug Console (bottom)**
   - Type: `request.query`
   - Press Enter
   - See: `"Plan a trip to Tokyo from Singapore..."`

#### Actions:
- Press `F10` (Step Over) to execute current line
- Or press `F5` (Continue) to go to next breakpoint

---

### Breakpoint 2 Hits (Agent Node)

**You'll see:**
- Paused at `await asyncio.sleep(0.5)`
- This is the agent thinking

#### What to Inspect:
1. **Variables → Local → state**
   ```
   ▼ state: dict
     ▼ messages: list
       ▼ [0]: HumanMessage
         ▶ content: "You are a helpful travel assistant..."
   ```

2. **Debug Console**
   ```python
   # Type these commands:
   state["messages"]
   len(state["messages"])
   state["messages"][0].content
   ```

3. **Expand in Variables Panel**
   - Click ▶ next to `state`
   - Click ▶ next to `messages`
   - Click ▶ next to `[0]`
   - Read the enhanced prompt!

#### Actions:
- Press `F10` to skip the sleep
- Press `F10` again to execute LLM call
- **After LLM call**, inspect `response`:

```python
# In Debug Console:
response
response.tool_calls
len(response.tool_calls)  # Should be 3
```

**You'll see the 3 tools LLM wants to call!**

---

### Breakpoint 3 Hits (Router)

**You'll see:**
- Paused at `last_message = messages[-1]`
- Router is deciding next step

#### What to Inspect:
1. **Variables → last_message**
   ```
   ▼ last_message: AIMessage
     ▶ content: ""
     ▼ tool_calls: list (3 items)
       ▼ [0]: dict
         ▶ name: "search_flights"
         ▼ args: dict
           ▶ origin: "Singapore"
           ▶ destination: "Tokyo"
   ```

2. **Debug Console**
   ```python
   last_message.tool_calls
   [tc["name"] for tc in last_message.tool_calls]
   # Output: ['search_flights', 'get_weather', 'find_attractions']
   ```

#### Actions:
- Press `F10` multiple times
- Watch the `if` statement evaluate
- See it return `"tools"`

**Router decided to execute tools!**

---

### Breakpoint 4 Hits (Tool Loop)

**You'll see:**
- Paused at `for tool_call in last_message.tool_calls:`
- About to execute tools

#### What to Inspect:
1. **First Iteration**
   ```
   ▼ tool_call: dict
     ▶ name: "search_flights"
     ▼ args: dict
       ▶ origin: "Singapore"
       ▶ destination: "Tokyo"
       ▶ date: "2025-12-01"
   ```

2. **Debug Console**
   ```python
   tool_call["name"]   # "search_flights"
   tool_call["args"]   # {'origin': 'Singapore', ...}
   ```

3. **Step Through Loop**
   - Press `F10` to see `tool_name = tool_call["name"]`
   - Press `F10` to see `tool_args = tool_call["args"]`
   - Press `F10` to skip sleep
   - Press `F10` to execute tool
   - Check `tool_result` in Variables!

#### Actions:
- Press `F5` to continue
- Breakpoint 4 will hit **3 times** (one per tool)
- Watch each tool execute

---

### Breakpoint 2 Hits Again (Agent Round 2)

**You'll see:**
- Back at agent node
- Now has tool results!

#### What to Inspect:
1. **Variables → state → messages**
   ```
   ▼ messages: list (5 items)
     [0] HumanMessage (original query)
     [1] AIMessage (tool request)
     [2] ToolMessage (search_flights result)
     [3] ToolMessage (get_weather result)
     [4] ToolMessage (find_attractions result)
   ```

2. **Debug Console**
   ```python
   len(state["messages"])  # 5
   state["messages"][2].content  # Flight data
   state["messages"][3].content  # Weather data
   state["messages"][4].content  # Attractions data
   ```

3. **After LLM Call**
   ```python
   response.content  # Full travel plan!
   response.tool_calls  # Empty list []
   ```

**Agent synthesized all data into final plan!**

---

### Breakpoint 3 Hits Again (Router Round 2)

**You'll see:**
- Router checking again
- This time NO tool_calls

#### What to Inspect:
1. **Variables → last_message**
   ```
   ▼ last_message: AIMessage
     ▶ content: "Based on the search results, here's your comprehensive..."
     ▶ tool_calls: []  ← Empty!
   ```

2. **Debug Console**
   ```python
   last_message.tool_calls  # []
   len(last_message.tool_calls)  # 0
   ```

#### Actions:
- Press `F10` through the if statement
- See it return `"__end__"`

**Router decided to END - we're done!**

---

### Execution Completes

- Press `F5` one more time
- Debugger releases
- Response sent to client
- Terminal shows curl output with travel plan!

---

## 🎓 Part 6: Advanced Inspection

### Using Call Stack
1. Look at **Call Stack panel** (left side)
2. See function hierarchy:
   ```
   tool_node (server.py:103)
   ├─ <async generator>
   ├─ event_generator (server.py:170)
   └─ travel_assistant (server.py:145)
   ```

3. Click any function to jump to it

### Using Watch Panel
1. Click **Watch** (above Variables)
2. Click **+** to add expression
3. Add these:
   ```python
   len(state["messages"])
   response.tool_calls if 'response' in locals() else None
   ```

4. Watch them update as you step!

### Using Debug Console
Try these commands:
```python
# Pretty print JSON
import json
print(json.dumps(tool_call["args"], indent=2))

# Type inspection
type(last_message).__name__

# List comprehension
[type(msg).__name__ for msg in state["messages"]]

# Conditional expression
"Has tools" if last_message.tool_calls else "No tools"
```

---

## 🎯 Part 7: Practice Exercises

### Exercise 1: Find Where Date is Set
**Goal:** Find where "2025-12-01" default date comes from

1. Set breakpoint in `search_flights` function
2. Send request without date
3. Inspect function parameters
4. Answer: Line 52, parameter default value

### Exercise 2: Count Message Exchanges
**Goal:** How many messages are in final state?

1. Set breakpoint at final router decision
2. Inspect `state["messages"]`
3. Count: 1 user + 1 AI request + 3 tool results + 1 AI response = **6 messages**

### Exercise 3: Tool Execution Order
**Goal:** Which tool executes first?

1. Set breakpoint in tool loop
2. Watch `tool_call["name"]` each iteration
3. Answer: Depends on LLM, usually alphabetical or by importance

### Exercise 4: Response Size
**Goal:** How long is the final travel plan?

1. Set breakpoint after agent round 2
2. Inspect `response.content`
3. Use Debug Console: `len(response.content)`
4. Answer: ~1000-2000 characters

---

## 🐛 Part 8: Common Debugging Scenarios

### Scenario: LLM Not Calling Tools

**Hypothesis:** System prompt not working

**Debug Steps:**
1. Breakpoint at Line ~153 (system_message creation)
2. Inspect `system_message.content`
3. Verify it contains: "ALWAYS call the available tools"
4. Breakpoint at Line 84 (after LLM response)
5. Check `response.tool_calls` - is it empty?

### Scenario: Wrong Tool Arguments

**Hypothesis:** LLM extracting wrong data

**Debug Steps:**
1. Breakpoint at Line 103 (tool loop)
2. Inspect `tool_call["args"]`
3. Compare with expected values
4. Check original user query
5. Verify system prompt instructions

### Scenario: Tools Not Executing

**Hypothesis:** Router not routing to tools

**Debug Steps:**
1. Breakpoint at Line 92 (router)
2. Check `last_message.tool_calls`
3. Watch if statement evaluation
4. See what router returns
5. If returns END instead of "tools", check why

---

## 🎬 Quick Reference

| Key | Action |
|-----|--------|
| `F5` | Continue to next breakpoint |
| `F10` | Step Over (execute line) |
| `F11` | Step Into (enter function) |
| `Shift+F11` | Step Out (exit function) |
| `F9` | Toggle breakpoint |
| `Cmd+K Cmd+I` | Hover info |
| `Shift+F5` | Stop debugging |

---

## ✅ Checklist

After this tutorial, you should be able to:

- [ ] Set breakpoints in VS Code
- [ ] Start debugger with F5
- [ ] Inspect variables in Variables panel
- [ ] Use Debug Console to evaluate expressions
- [ ] Step through code with F10
- [ ] See LLM tool_calls array
- [ ] Watch tool execution loop
- [ ] Understand message flow
- [ ] Use Call Stack panel
- [ ] Add Watch expressions

---

**🎉 Congratulations! You're now a Travel Assistant debugging expert!**

**Next steps:**
- Try debugging with `stream: true`
- Set conditional breakpoints
- Use logpoints instead of breakpoints
- Debug the notebook version
