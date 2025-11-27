# 🎯 Debug Quick Reference Card

Print this or keep it handy while debugging!

---

## 🔴 Critical Breakpoints

| Line | Function | What Happens |
|------|----------|--------------|
| **~145** | `travel_assistant()` | 🌐 Request arrives |
| **~82** | `call_model()` | 🤖 Agent thinks |
| **~92** | `should_continue()` | 🔀 Router decides |
| **~103** | `tool_node()` | 🔧 Tools execute |

---

## ⌨️ Keyboard Shortcuts

| Key | Action | Use When |
|-----|--------|----------|
| `F5` | Continue | Go to next breakpoint |
| `F10` | Step Over | Execute current line |
| `F11` | Step Into | Enter function |
| `Shift+F11` | Step Out | Exit function |
| `F9` | Toggle BP | Add/remove breakpoint |
| `Shift+F5` | Stop | End debug session |

---

## 🔍 What to Inspect

### At Request Entry (Line ~145)
```python
request.query    # User's travel query
request.stream   # Streaming enabled?
```

### At Agent Node (Line ~82)
```python
state["messages"]           # Conversation history
response.tool_calls         # Tools to call
len(response.tool_calls)    # How many?
```

### At Router (Line ~92)
```python
last_message.tool_calls     # Are there tool calls?
# If yes → "tools", if no → END
```

### At Tool Loop (Line ~103)
```python
tool_call["name"]    # Which tool?
tool_call["args"]    # What arguments?
tool_result          # What data returned?
```

---

## 🎬 Execution Flow

```
1. Request Entry      [Line ~145]
   ↓
2. Agent Round 1      [Line ~82]
   ↓ (has tool_calls)
3. Router → tools     [Line ~92]
   ↓
4. Execute 3 tools    [Line ~103]
   ↓
5. Agent Round 2      [Line ~82]
   ↓ (no tool_calls)
6. Router → END       [Line ~92]
   ↓
7. Response sent
```

---

## 💬 Debug Console Commands

```python
# See all messages
state["messages"]

# Count messages
len(state["messages"])

# Get last message
state["messages"][-1].content

# List tool calls
[tc["name"] for tc in response.tool_calls]

# Pretty print JSON
import json
print(json.dumps(tool_result, indent=2))

# Type of each message
[type(msg).__name__ for msg in state["messages"]]
```

---

## 🎯 Common Patterns

### Check if tools will be called
```python
hasattr(last_message, 'tool_calls') and last_message.tool_calls
```

### Get tool names
```python
[tc["name"] for tc in last_message.tool_calls]
```

### Count conversation turns
```python
len([m for m in state["messages"] if isinstance(m, HumanMessage)])
```

---

## 📊 Message Types in Order

```
Round 1:
  [0] HumanMessage    ← User query
  [1] AIMessage       ← Tool request

Round 2 (after tools):
  [2] ToolMessage     ← search_flights
  [3] ToolMessage     ← get_weather
  [4] ToolMessage     ← find_attractions

Round 3:
  [5] AIMessage       ← Final plan
```

---

## 🐛 Troubleshooting

| Issue | Check Here |
|-------|------------|
| No tools called | Line 82 - `response.tool_calls` |
| Wrong arguments | Line 103 - `tool_call["args"]` |
| Router wrong | Line 92 - if statement |
| No response | Line 200 - final message |

---

## 🎓 Pro Tips

1. **Watch Panel**: Add `len(state["messages"])`
2. **Conditional BP**: `tool_name == "search_flights"`
3. **Logpoints**: Instead of print statements
4. **Call Stack**: See function hierarchy
5. **Hover**: Hold over variable to see value

---

## 🚀 Quick Start

```bash
# 1. Set 4 breakpoints (lines 145, 82, 92, 103)
# 2. Press Cmd+Shift+D (Debug panel)
# 3. Select "Debug FastAPI with Uvicorn"
# 4. Press F5 (Start)
# 5. Send request via curl or UI
# 6. Watch magic happen! ✨
```

---

**Keep this handy while debugging! 🎯**
