# 🎯 Quick Breakpoint Reference - Exact Line Numbers

Use this guide to quickly set breakpoints in VS Code.

---

## 📍 File: `server.py`

### **Critical Breakpoints (Set These First)**

| # | Line | Function | What Happens Here | Variable to Inspect |
|---|------|----------|-------------------|---------------------|
| 1️⃣ | **~145** | `travel_assistant()` | Request enters API endpoint | `request.query`, `request.stream` |
| 2️⃣ | **~153** | `travel_assistant()` | Enhanced prompt created | `system_message.content` |
| 3️⃣ | **~158** | `travel_assistant()` | State initialized | `initial_state["messages"]` |
| 4️⃣ | **~82** | `call_model()` | Agent starts thinking | `state["messages"]` |
| 5️⃣ | **~84** | `call_model()` | LLM response received | `response`, `response.tool_calls` |
| 6️⃣ | **~92** | `should_continue()` | Router decides next step | `last_message.tool_calls` |
| 7️⃣ | **~103** | `tool_node()` | Tool execution begins | `tool_call["name"]`, `tool_call["args"]` |
| 8️⃣ | **~52** | `search_flights()` | Flight search executes | `origin`, `destination`, `flights` |

---

## 🔧 How to Set Breakpoints in VS Code

### **Method 1: Click in Gutter**
1. Open `server.py`
2. Find the line number
3. Click in the **gray area** to the left of the line number
4. A **red dot** appears ✅

### **Method 2: Using Keyboard**
1. Place cursor on the line
2. Press `F9`
3. Red dot appears

### **Method 3: Right-Click**
1. Right-click on line number
2. Select "Add Breakpoint"

---

## 📊 Execution Flow with Line Numbers

```
USER REQUEST
    ↓
[Line 145] 🌐 Request arrives at /travel-assistant
    │      Variables: request.query, request.stream
    ↓
[Line 153] 🔧 System message created with enhanced prompt
    │      Variables: system_message.content
    ↓
[Line 158] 📝 Initial state prepared
    │      Variables: initial_state["messages"]
    ↓
[Line 165] 📡 Streaming starts (if enabled)
    │
    ↓
[Line 82]  🤖 AGENT NODE - Round 1
    │      LLM analyzes query
    │      Variables: state["messages"]
    ↓
[Line 84]  💭 LLM responds with tool_calls
    │      Variables: response, response.tool_calls
    │      Example: [search_flights, get_weather, find_attractions]
    ↓
[Line 92]  🔀 ROUTER - Decision 1
    │      Checks for tool_calls
    │      Variables: last_message.tool_calls
    │      Decision: → "tools" (has tool_calls)
    ↓
[Line 103] 🔧 TOOL NODE - Execute tools
    │      Loop through each tool_call
    │      Variables: tool_call["name"], tool_call["args"]
    │
    ├→ [Line 52]  🛫 search_flights(origin="Singapore", destination="Tokyo")
    │             Variables: flights (mock data)
    │
    ├→ [Line 67]  🌤️ get_weather(location="Tokyo", date="2025-12-01")
    │             Variables: weather (mock data)
    │
    └→ [Line 82]  🗼 find_attractions(location="Tokyo", category="all")
                  Variables: attractions (mock data)
    ↓
[Line 82]  🤖 AGENT NODE - Round 2
    │      LLM receives tool results
    │      Synthesizes travel plan
    │      Variables: state["messages"] (now includes tool results)
    ↓
[Line 84]  💬 LLM final response (no tool_calls)
    │      Variables: response.content (travel plan)
    ↓
[Line 92]  🔀 ROUTER - Decision 2
    │      No tool_calls found
    │      Decision: → END
    ↓
[Line 200] ✅ Stream complete / Response sent
    │      Variables: final_message.content
    ↓
RESPONSE TO USER
```

---

## 🎯 Setting Up Your First Debug Session

### **Step 1: Set Strategic Breakpoints**
Copy these line numbers and set breakpoints:
- **Line 145** - Request entry
- **Line 82** - Agent node
- **Line 92** - Router
- **Line 103** - Tool execution

### **Step 2: Start Debugger**
```
1. Press Cmd+Shift+D (Debug panel)
2. Select "Debug FastAPI with Uvicorn"
3. Press F5 (Start Debugging)
4. Wait for "Application startup complete"
```

### **Step 3: Send Test Request**
Open new terminal:
```bash
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a trip to Tokyo from Singapore",
    "stream": false
  }'
```

### **Step 4: Follow Breakpoints**
- **Hit 1**: Line 145 - Inspect `request.query`
- **Hit 2**: Line 82 - Inspect `state["messages"]`
- **Hit 3**: Line 84 - Inspect `response.tool_calls`
- **Hit 4**: Line 92 - Watch routing decision
- **Hit 5**: Line 103 - See tools execute
- **Hit 6**: Line 82 (again) - See final synthesis
- **Hit 7**: Line 92 (again) - Route to END

---

## 🔍 Variables Panel - What to Expand

When debugger pauses, expand these in Variables panel:

### **At Line 145 (Request Entry)**
```
▼ request
  ▶ query: "Plan a trip to Tokyo..."
  ▶ stream: false
```

### **At Line 82 (Agent Node - Round 1)**
```
▼ state
  ▼ messages
    ▼ [0] HumanMessage
      ▶ content: "You are a helpful travel assistant..."
```

### **At Line 84 (After LLM Response)**
```
▼ response
  ▶ content: ""
  ▼ tool_calls
    ▼ [0]
      ▶ name: "search_flights"
      ▼ args
        ▶ origin: "Singapore"
        ▶ destination: "Tokyo"
    ▼ [1]
      ▶ name: "get_weather"
    ▼ [2]
      ▶ name: "find_attractions"
```

### **At Line 103 (Tool Execution)**
```
▼ tool_call
  ▶ name: "search_flights"
  ▼ args
    ▶ origin: "Singapore"
    ▶ destination: "Tokyo"
    ▶ date: "2025-12-01"
  ▶ id: "call_xyz123"
```

### **At Line 82 (Agent Node - Round 2)**
```
▼ state
  ▼ messages
    [0] HumanMessage (user query)
    [1] AIMessage (tool_calls request)
    [2] ToolMessage (search_flights result)
    [3] ToolMessage (get_weather result)
    [4] ToolMessage (find_attractions result)
```

---

## 🎬 Debug Console Commands

While paused at breakpoints, type these in Debug Console:

```python
# See all messages
state["messages"]

# Get last message content
state["messages"][-1].content

# Check if there are tool calls
hasattr(state["messages"][-1], 'tool_calls')

# Get tool call names
[tc["name"] for tc in response.tool_calls] if response.tool_calls else []

# Pretty print tool results
import json; print(json.dumps(tool_result, indent=2))

# Count messages
len(state["messages"])

# Get conversation flow
[type(msg).__name__ for msg in state["messages"]]
```

---

## 🐛 Common Issues & Debug Points

### **Issue: LLM Not Calling Tools**
**Set breakpoint:** Line 82
**Check in Variables:**
- `llm_with_tools` - Are tools bound?
- `state["messages"][0].content` - Is system prompt correct?

### **Issue: Wrong Tool Arguments**
**Set breakpoint:** Line 103
**Check in Variables:**
- `tool_call["args"]` - What arguments are being passed?
- Use Debug Console: `print(tool_call)`

### **Issue: Tools Not Returning Data**
**Set breakpoint:** Line 52, 67, 82 (tool functions)
**Check in Variables:**
- Function parameters
- Return value

### **Issue: Response Not Streaming**
**Set breakpoint:** Line 165
**Check in Variables:**
- `request.stream` - Is it true?
- Watch the async loop

---

## ⚡ Pro Tips

### **1. Conditional Breakpoints**
Right-click breakpoint → Edit → Condition:
```python
tool_call["name"] == "search_flights"
```

### **2. Log Points (No Pause)**
Right-click → Add Logpoint:
```
Executing tool: {tool_call["name"]} with args: {tool_call["args"]}
```

### **3. Watch Panel**
Add these expressions to watch continuously:
```python
len(state["messages"])
response.tool_calls if hasattr(response, 'tool_calls') else None
```

### **4. Keyboard Shortcuts**
- `F5` - Continue to next breakpoint
- `F10` - Step over (execute current line)
- `F11` - Step into (go inside function)
- `Shift+F11` - Step out (exit function)
- `Cmd+K Cmd+I` - Show hover information

---

## 📋 Checklist Before Starting

- [ ] Python extension installed
- [ ] `.vscode/launch.json` exists
- [ ] Server not already running on port 8000
- [ ] `.env` file has `GOOGLE_API_KEY`
- [ ] Breakpoints set at key lines
- [ ] Debug configuration selected

---

## 🎓 Learning Path

1. **First Time**: Set only Line 145, see request arrive
2. **Second Time**: Add Line 82, watch agent process
3. **Third Time**: Add Line 92, understand routing
4. **Fourth Time**: Add Line 103, see tool execution
5. **Fifth Time**: Add all breakpoints, see full flow

---

**Ready to debug? Press F5 and explore the Travel Assistant internals! 🚀**
