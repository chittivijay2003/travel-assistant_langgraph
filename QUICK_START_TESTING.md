# Quick Start Guide - Testing Streaming

## 🚀 Quick Test Methods

### Method 1: Interactive Web UI (EASIEST - URL Based)
```bash
# Open in your browser - NO FILE SYSTEM ACCESS NEEDED!
http://localhost:8000/ui
```

**Alternative: File-based access**
```bash
# Open the HTML test UI file from file system
open streaming_test.html
# or on Linux/WSL
xdg-open streaming_test.html
```

### Method 2: Python Test Script
```bash
python3 test_streaming.py
```

### Method 3: cURL (Command Line)

**Streaming:**
```bash
curl -N -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a 3-day trip to Tokyo from Singapore. Search flights, check weather, and find attractions.",
    "stream": true
  }'
```

**Non-Streaming:**
```bash
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a trip to Tokyo",
    "stream": false
  }'
```

### Method 4: VS Code REST Client Extension

1. Install "REST Client" extension
2. Open `api_tests.http`
3. Click "Send Request" above any test case

---

## 📋 All Available URLs

| Endpoint | URL | Method | Description |
|----------|-----|--------|-------------|
| **Streaming UI** | http://localhost:8000/ui | GET | Interactive web interface |
| **API Docs (Swagger)** | http://localhost:8000/docs | GET | Interactive API documentation |
| **ReDoc** | http://localhost:8000/redoc | GET | Alternative API docs |
| **Health Check** | http://localhost:8000/health | GET | Server status |
| **Travel Assistant** | http://localhost:8000/travel-assistant | POST | Main endpoint |

---

## 🎯 State Management Summary

### Current Implementation:
- **State Lifetime**: 5-10 seconds (single request only)
- **Storage**: In-memory (RAM) during request
- **Persistence**: ❌ None (stateless)
- **Between Requests**: ❌ No memory
- **Location**: Python process memory

### State Timeline:
```
t=0s    Request arrives
        ↓
t=0s    State created: {"messages": [HumanMessage(...)]}
        ↓
t=2s    Agent adds: AIMessage(tool_calls=[...])
        ↓
t=3s    Tools add: ToolMessage("results")
        ↓
t=5s    Agent adds: AIMessage("final response")
        ↓
t=6s    Response sent to client
        ↓
t=6s    State DESTROYED (garbage collected)
```

### To Add Conversation Memory:

**Option 1 - Client-Side (Frontend maintains history):**
```javascript
let history = [];
function sendMessage(query) {
    const fullContext = history.join("\n") + "\n" + query;
    // Send fullContext to API
    history.push(query, response);
}
```

**Option 2 - LangGraph Checkpointer:**
```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)

# Use thread_id for conversation
result = app_graph.invoke(
    state, 
    config={"configurable": {"thread_id": "user_123"}}
)
```

**Option 3 - Database:**
```python
# Save to DB after each request
db.save_conversation(user_id, messages)

# Load on next request
previous = db.load_conversation(user_id)
state = {"messages": previous + [new_message]}
```

---

## 🌊 Streaming Details

### How Streaming Works:

1. **Client** sends request with `"stream": true`
2. **Server** returns `StreamingResponse` with `text/event-stream`
3. **Server** yields chunks as they're generated:
   ```
   data: {"content": "I can help"}
   
   data: {"content": " you plan"}
   
   data: [DONE]
   ```
4. **Client** receives and displays chunks incrementally

### Benefits of Streaming:
- ✅ User sees content immediately (better UX)
- ✅ Lower perceived latency
- ✅ Progress indication
- ✅ Can cancel mid-stream
- ❌ Slightly more complex to implement

### When to Use Streaming:
- ✅ Long responses (travel itineraries)
- ✅ Real-time chat interfaces
- ✅ When user engagement is important
- ❌ Short responses (single facts)
- ❌ When you need the full response before processing

---

## 🧪 Testing Examples

### Example 1: Basic Test
```bash
# Check server is running
curl http://localhost:8000/health

# Send simple query (non-streaming)
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about Tokyo", "stream": false}'
```

### Example 2: Streaming Test
```bash
# Streaming with explicit tool usage
curl -N -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a 3-day trip to Tokyo from Singapore. IMPORTANT: Use the search_flights, get_weather, and find_attractions tools.",
    "stream": true
  }'
```

### Example 3: Python Script
```python
import requests

response = requests.post(
    'http://localhost:8000/travel-assistant',
    json={'query': 'Plan a trip to Tokyo', 'stream': True},
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

---

## 📝 Key Points to Remember

1. **State is temporary** - only exists during request processing
2. **No persistence** - each request starts fresh
3. **Streaming is real-time** - content sent as generated
4. **Use -N flag** with curl for streaming (disables buffering)
5. **SSE format** - lines start with "data: "
6. **Browser testing** - Use streaming_test.html for visual feedback
7. **API docs** - http://localhost:8000/docs for interactive testing

---

## 🔧 Troubleshooting

**Server not responding:**
```bash
# Check if server is running
lsof -i :8000

# Restart server
python3 server.py
```

**Streaming not working:**
```bash
# Use -N flag to disable buffering
curl -N -X POST ...

# Check response headers for 'text/event-stream'
curl -i -X POST ...
```

**No output visible:**
```bash
# Check server logs
tail -f server.log

# Test with simple query first
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "stream": false}'
```
