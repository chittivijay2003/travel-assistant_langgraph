# 🐛 Debugging Resources - Travel Assistant

Complete guide to debugging the Travel Assistant application in VS Code.

---

## 📚 Documentation Files

### 1. **DEBUG_GUIDE.md** - Comprehensive Debugging Guide
- Complete debugging overview
- 7 strategic breakpoint locations
- Variable inspection guide
- Step-by-step execution flow
- Advanced debugging techniques
- Common scenarios and solutions

**Start here if:** You want a complete understanding of debugging

---

### 2. **BREAKPOINT_GUIDE.md** - Quick Breakpoint Reference
- Exact line numbers for breakpoints
- Visual execution flow diagram
- Variables to inspect at each breakpoint
- Debug console commands
- Common debugging patterns

**Start here if:** You want to quickly set up breakpoints

---

### 3. **STEP_BY_STEP_WALKTHROUGH.md** - Detailed Request Flow
- Complete request execution walkthrough
- What happens at each step
- State changes after each node
- Message flow visualization
- Timing breakdown
- Code snippets with explanations

**Start here if:** You want to understand the complete flow

---

### 4. **DEBUGGER_TUTORIAL.md** - Hands-On Tutorial
- Interactive step-by-step guide
- Set up debugger from scratch
- Send test request
- Inspect variables at each breakpoint
- Practice exercises
- Common debugging scenarios

**Start here if:** You want hands-on practice

---

### 5. **DEBUG_QUICK_REF.md** - Quick Reference Card
- One-page cheat sheet
- Critical breakpoints
- Keyboard shortcuts
- Debug console commands
- Common patterns
- Troubleshooting table

**Start here if:** You need a quick reminder while debugging

---

## 🚀 Quick Start (2 Minutes)

### Step 1: Set Breakpoints
Open `server.py` and click in the left gutter on these lines:
- **Line ~145** - Request entry
- **Line ~82** - Agent node
- **Line ~92** - Router
- **Line ~103** - Tool execution

### Step 2: Start Debugger
1. Press `Cmd+Shift+D` (Debug panel)
2. Select "Debug FastAPI with Uvicorn"
3. Press `F5`

### Step 3: Send Request
```bash
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "Plan a trip to Tokyo from Singapore", "stream": false}'
```

### Step 4: Follow Breakpoints
- Press `F5` to continue between breakpoints
- Press `F10` to step through code
- Inspect variables in left panel

---

## 🎯 Learning Path

### Beginner (Day 1)
1. Read **DEBUGGER_TUTORIAL.md**
2. Set 4 basic breakpoints
3. Send one request
4. Watch variables change

### Intermediate (Day 2)
1. Read **STEP_BY_STEP_WALKTHROUGH.md**
2. Add more breakpoints
3. Use Debug Console
4. Explore state changes

### Advanced (Day 3)
1. Read **DEBUG_GUIDE.md**
2. Set conditional breakpoints
3. Use Watch panel
4. Debug streaming requests

---

## 📊 Key Debugging Locations

### File: `server.py`

| Line | Function | Purpose | What to See |
|------|----------|---------|-------------|
| ~145 | `travel_assistant()` | API entry | `request.query` |
| ~153 | System message | Enhanced prompt | Instructions to LLM |
| ~158 | State init | Graph start | Initial state |
| ~82 | `call_model()` | Agent thinks | `response.tool_calls` |
| ~92 | `should_continue()` | Router | Decision: tools vs END |
| ~103 | `tool_node()` | Execute tools | Tool loop iteration |
| ~52 | `search_flights()` | Flight tool | Mock flight data |
| ~67 | `get_weather()` | Weather tool | Mock weather data |
| ~82 | `find_attractions()` | Attractions tool | Mock attractions |

---

## 🔍 Common Debug Scenarios

### Scenario 1: Understanding Tool Calls
**Breakpoints:** Lines 82, 84, 103
**Goal:** See how LLM requests and executes tools
**What to watch:**
- `response.tool_calls` at Line 84
- Tool loop at Line 103
- Each tool execution

### Scenario 2: Tracking State Changes
**Breakpoints:** Lines 82 (both rounds)
**Goal:** See how state accumulates
**What to watch:**
- `state["messages"]` grows from 1 → 5 → 6
- Different message types added

### Scenario 3: Router Logic
**Breakpoints:** Line 92 (both calls)
**Goal:** Understand routing decisions
**What to watch:**
- First call: has tool_calls → "tools"
- Second call: no tool_calls → END

### Scenario 4: Full Request Flow
**Breakpoints:** All 4 main locations
**Goal:** See complete execution
**What to watch:**
- Request → Agent → Router → Tools → Agent → Router → Response

---

## 🛠️ Debug Configuration

The `.vscode/launch.json` provides:

### 1. Debug Travel Assistant Server
- Runs `server.py` directly
- For simple debugging

### 2. Debug FastAPI with Uvicorn
- Runs via uvicorn (recommended)
- Hot reload enabled
- Production-like environment

### 3. Debug Test Script
- Runs `run_assistant.py`
- For testing without server

---

## 💡 Pro Tips

### 1. Use F10 Liberally
Step over each line to see execution flow

### 2. Expand Variables
Click ▶ arrows to explore nested objects

### 3. Watch Panel
Add expressions that update automatically:
```python
len(state["messages"])
response.tool_calls if 'response' in locals() else None
```

### 4. Debug Console
Evaluate any Python expression in context:
```python
[type(m).__name__ for m in state["messages"]]
```

### 5. Conditional Breakpoints
Right-click breakpoint → Edit:
```python
tool_name == "search_flights"
```

### 6. Call Stack
Click functions to navigate execution hierarchy

### 7. Logpoints
Add logging without stopping execution

---

## 🎬 Video Walkthrough Concept

If you were recording, here's the flow:

1. **Intro** (30s)
   - Show VS Code with project open
   - Show 4 files in sidebar

2. **Setup** (1m)
   - Set 4 breakpoints
   - Start debugger
   - Show Variables panel

3. **Request** (30s)
   - Send curl request
   - Pause at first breakpoint

4. **Walkthrough** (5m)
   - Step through each breakpoint
   - Show variables at each step
   - Explain what's happening

5. **Wrap-up** (30s)
   - Show final response
   - Summarize flow

---

## 📋 Debugging Checklist

Before you start:
- [ ] VS Code Python extension installed
- [ ] `.vscode/launch.json` exists
- [ ] Breakpoints set at 4 locations
- [ ] Debug configuration selected
- [ ] Server not already running
- [ ] `.env` file configured

During debugging:
- [ ] Variables panel visible
- [ ] Debug Console open
- [ ] Call Stack visible
- [ ] Watch panel configured (optional)

After debugging:
- [ ] Understood request flow
- [ ] Saw tool calls
- [ ] Tracked state changes
- [ ] Followed router decisions

---

## 🎯 Expected Execution Pattern

```
Breakpoint Hits in Order:

1. Line 145 (Request entry)
2. Line 82 (Agent Round 1)
3. Line 92 (Router → tools)
4. Line 103 (Tool 1: search_flights)
5. Line 103 (Tool 2: get_weather)
6. Line 103 (Tool 3: find_attractions)
7. Line 82 (Agent Round 2)
8. Line 92 (Router → END)

Total: 8 breakpoint hits per request
```

---

## 🔗 Quick Links

- **Main Server**: `server.py`
- **Debug Config**: `.vscode/launch.json`
- **Test Request**: See `DEBUGGER_TUTORIAL.md`
- **Web UI**: http://localhost:8000/ui
- **API Docs**: http://localhost:8000/docs

---

## 📞 Need Help?

### Common Issues

**Debugger won't start:**
- Check Python extension installed
- Verify `launch.json` exists
- Try restart VS Code

**Breakpoints not hitting:**
- Verify server started in debug mode
- Check line numbers are correct
- Try rebuilding breakpoints

**Can't see variables:**
- Make sure Variables panel is open
- Try expanding with ▶ arrows
- Use Debug Console as fallback

**Request times out:**
- Increase timeout in curl
- Press F5 to continue if paused too long

---

## 🎉 Success Metrics

You've mastered debugging when you can:

1. ✅ Set breakpoints quickly
2. ✅ Start debugger without errors
3. ✅ Inspect variables efficiently
4. ✅ Understand tool_calls array
5. ✅ Follow message flow
6. ✅ Use Debug Console
7. ✅ Explain routing decisions
8. ✅ Track state changes

---

**Happy Debugging! 🐛✨**

For detailed guidance, start with **DEBUGGER_TUTORIAL.md**
