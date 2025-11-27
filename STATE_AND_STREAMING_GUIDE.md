# State Management & Streaming Guide

## 📊 State Messaging Handling

### How State Works in LangGraph

#### 1. **State Lifetime**
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
```

- **Duration**: State exists **only for the duration of a single request**
- **Scope**: Each API call creates a NEW state from scratch
- **No Persistence**: State is **NOT saved** between requests (stateless architecture)

#### 2. **State Flow Timeline**
```
REQUEST START (t=0)
    ↓
[1] Initial State Created
    messages: [HumanMessage("Plan a trip to Tokyo")]
    
    ↓
[2] Agent Node (t=1-3s)
    messages: [HumanMessage(...), AIMessage(tool_calls=[...])]
    
    ↓
[3] Tools Node (t=3-4s)
    messages: [..., AIMessage(...), ToolMessage("Flight data")]
    
    ↓
[4] Agent Node Again (t=4-7s)
    messages: [..., ToolMessage(...), AIMessage("Here's your plan...")]
    
    ↓
REQUEST END (t=7s)
State is DESTROYED ❌
```

**Total Lifetime**: ~5-10 seconds per request

#### 3. **Where State is Stored**

**During Execution:**
- ✅ **In-Memory**: Python process memory (RAM)
- ✅ **Per-Request**: Each request has isolated state
- ❌ **Not in Database**: No persistence layer
- ❌ **Not in Redis**: No caching
- ❌ **Not on Disk**: No file storage

**After Request Completes:**
- State is **garbage collected** by Python
- No state survives between requests
- Each new query starts fresh

#### 4. **State Accumulation Example**

```python
# Request 1: "Search flights to Tokyo"
state = {
    "messages": [
        HumanMessage("Search flights to Tokyo"),
        AIMessage(tool_calls=[...]),
        ToolMessage("Flight data"),
        AIMessage("Here are flights...")
    ]
}
# → Response sent → State DELETED

# Request 2: "What's the weather there?"
# ❌ Previous context LOST
# ✅ NEW state starts from scratch
state = {
    "messages": [
        HumanMessage("What's the weather there?")
        # No memory of Tokyo from Request 1!
    ]
}
```

### 5. **Memory & Persistence Options**

If you need conversation memory, you must implement:

**Option A: Client-Side State Management**
```javascript
// Frontend maintains conversation history
let conversationHistory = [];

async function sendMessage(newQuery) {
    // Build context from history
    const fullContext = [
        ...conversationHistory,
        newQuery
    ].join("\n\n");
    
    const response = await fetch('/travel-assistant', {
        body: JSON.stringify({ query: fullContext })
    });
    
    conversationHistory.push(newQuery, response);
}
```

**Option B: LangGraph Checkpointer (Advanced)**
```python
from langgraph.checkpoint.memory import MemorySaver

# Add persistence to graph
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)

# Use thread_id to maintain conversation
result = await app_graph.ainvoke(
    initial_state,
    config={"configurable": {"thread_id": "user_123"}}
)
```

**Option C: Database Storage**
```python
# Store conversation in DB
class Conversation(Model):
    user_id = CharField()
    messages = JSONField()
    created_at = DateTimeField()

# On each request
conversation = Conversation.get(user_id="user_123")
initial_state = {
    "messages": conversation.messages + [new_message]
}
```

---

## 🌊 Streaming Functionality

### Current Streaming Implementation

The server supports **Server-Sent Events (SSE)** streaming:

```python
@app.post("/travel-assistant")
async def travel_assistant(request: TravelRequest):
    if request.stream:
        async def event_generator():
            async for event in app_graph.astream(initial_state):
                for node_name, node_output in event.items():
                    if node_name == "agent":
                        messages = node_output.get("messages", [])
                        if messages:
                            last_message = messages[-1]
                            if hasattr(last_message, "content") and last_message.content:
                                yield f"data: {json.dumps({'content': last_message.content})}\n\n"
            
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## 🧪 Testing Streaming Responses

### Method 1: cURL (Command Line)

```bash
# Basic streaming test
curl -N -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a 3-day trip to Tokyo from Singapore. Search flights, check weather, find attractions.",
    "stream": true
  }'

# Expected output:
# data: {"content": "I'll help you plan..."}
# 
# data: {"content": "Based on the flight search..."}
# 
# data: [DONE]
```

### Method 2: Python Client

Save as `test_streaming.py`:

```python
import requests
import json

def test_streaming():
    url = "http://localhost:8000/travel-assistant"
    
    payload = {
        "query": "Plan a 3-day trip to Tokyo from Singapore. Use tools to search flights, get weather, and find attractions.",
        "stream": True
    }
    
    print("🌊 Starting streaming request...\n")
    
    with requests.post(url, json=payload, stream=True) as response:
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    data = decoded[6:]  # Remove 'data: ' prefix
                    
                    if data == '[DONE]':
                        print("\n✅ Stream complete!")
                        break
                    
                    try:
                        parsed = json.loads(data)
                        if 'content' in parsed:
                            print(parsed['content'], end='', flush=True)
                    except json.JSONDecodeError:
                        pass

if __name__ == "__main__":
    test_streaming()
```

Run:
```bash
python3 test_streaming.py
```

### Method 3: JavaScript Fetch API

```javascript
async function testStreaming() {
    const response = await fetch('http://localhost:8000/travel-assistant', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: 'Plan a 3-day trip to Tokyo from Singapore',
            stream: true
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                    console.log('Stream complete!');
                    return;
                }
                
                try {
                    const parsed = JSON.parse(data);
                    if (parsed.content) {
                        console.log(parsed.content);
                    }
                } catch (e) {}
            }
        }
    }
}

testStreaming();
```

### Method 4: Postman

1. **Open Postman**
2. **Create New Request**:
   - Method: `POST`
   - URL: `http://localhost:8000/travel-assistant`
   - Headers: `Content-Type: application/json`
   - Body (raw JSON):
     ```json
     {
       "query": "Plan a 3-day trip to Tokyo from Singapore. Search flights, get weather, find attractions.",
       "stream": true
     }
     ```
3. **Click Send**
4. **View Response**: You'll see SSE events in the response body

### Method 5: Thunder Client (VS Code Extension)

1. Install Thunder Client extension
2. Create new request:
   - Method: POST
   - URL: `http://localhost:8000/travel-assistant`
   - Body:
     ```json
     {
       "query": "Plan a trip to Tokyo",
       "stream": true
     }
     ```
3. Send and watch streaming response

---

## 🎨 Interactive Web UI for Streaming

See the separate `streaming_test.html` file for a complete interactive UI!

---

## 📡 API Endpoints Summary

### 1. Root Endpoint
```bash
GET http://localhost:8000/
```
Returns: Service status and configuration

### 2. Health Check
```bash
GET http://localhost:8000/health
```
Returns: Detailed health information

### 3. Travel Assistant (Non-Streaming)
```bash
POST http://localhost:8000/travel-assistant
Content-Type: application/json

{
  "query": "Plan a trip to Tokyo",
  "stream": false
}
```

### 4. Travel Assistant (Streaming)
```bash
POST http://localhost:8000/travel-assistant
Content-Type: application/json

{
  "query": "Plan a trip to Tokyo",
  "stream": true
}
```

### 5. API Documentation
```bash
# Swagger UI
http://localhost:8000/docs

# ReDoc
http://localhost:8000/redoc
```

---

## 🔍 Debugging Streaming

### Check if streaming is working:

```bash
# Test 1: Check server is running
curl http://localhost:8000/health

# Test 2: Non-streaming (should work)
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "stream": false}'

# Test 3: Streaming (check for SSE format)
curl -N -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "stream": true}' \
  | head -20
```

### Common Issues:

**Issue 1**: No streaming visible
- Solution: Use `-N` flag with curl
- Solution: Enable streaming in client (don't buffer response)

**Issue 2**: Stream cuts off early
- Solution: Check server logs for errors
- Solution: Increase timeout settings

**Issue 3**: Garbled output
- Solution: Parse SSE format correctly (remove "data: " prefix)

---

## 📊 State vs Streaming Comparison

| Aspect | State Management | Streaming |
|--------|-----------------|-----------|
| **Lifetime** | Single request (~5-10s) | Duration of response |
| **Storage** | In-memory (RAM) | Not stored, sent directly |
| **Persistence** | No (destroyed after response) | No (real-time transmission) |
| **Between Requests** | Not shared | Not applicable |
| **Memory Usage** | ~1-10 KB per request | Minimal (chunks sent immediately) |
| **Use Case** | Track conversation flow | Real-time UX feedback |

---

## 💡 Key Takeaways

1. **State is Ephemeral**: Lives only during a single request execution
2. **No Built-in Memory**: Each request is independent (stateless)
3. **Streaming is Real-Time**: Content sent as it's generated
4. **For Conversations**: Implement external state management (DB, checkpointer, or client-side)
5. **Testing Streaming**: Use curl with `-N` flag or browser EventSource API
