# State Persistence & Server Restart Guide

## 🔄 Current Behavior: Stateless Architecture

### What Happens on Server Restart?

**Short Answer:** Nothing is lost because nothing is saved!

```
┌────────────────────────────────────────────────────────────┐
│  Current Implementation: STATELESS                         │
└────────────────────────────────────────────────────────────┘

Request Flow:
  1. Request arrives
  2. State created in RAM
  3. Processing (5-10 seconds)
  4. Response sent
  5. State DESTROYED ❌
  
Server Restart Impact:
  - No active states exist (already destroyed)
  - No data loss (nothing was saved)
  - New requests work exactly the same
```

---

## 📊 State Lifecycle vs Server Lifecycle

### Scenario 1: Normal Operation (No Restart)

```
t=0s    Request 1: "Plan Tokyo trip"
        → State created in RAM
        
t=5s    Response sent
        → State destroyed from RAM ❌
        
t=10s   Request 2: "What's the weather?"
        → NEW state created (no memory of Request 1)
        
t=15s   Response sent
        → State destroyed ❌
```

**Result:** No conversation memory between requests

---

### Scenario 2: With Server Restart

```
t=0s    Request 1: "Plan Tokyo trip"
        → State created in RAM
        
t=5s    Response sent
        → State destroyed ❌
        
t=10s   [SERVER RESTART]
        → RAM cleared (but state was already gone!)
        
t=15s   Server restarted
        
t=20s   Request 2: "What's the weather?"
        → NEW state created
        
t=25s   Response sent
        → State destroyed ❌
```

**Result:** Exactly the same as Scenario 1! No difference!

---

## ⚠️ Important Realizations

### 1. State is Already Gone Before Restart

```
Request completes → State destroyed → Time passes → Server restarts
                    ↑
                    State was already destroyed here!
```

**There's nothing in memory to lose on restart.**

### 2. Restart Impact: **NONE** (for completed requests)

| Aspect | Before Restart | After Restart |
|--------|----------------|---------------|
| Previous request state | Destroyed | Still destroyed |
| New request behavior | Creates new state | Creates new state |
| Conversation memory | None | None |
| Functional difference | ❌ None | ❌ None |

### 3. Active Request During Restart

**Only risk:** If a request is actively being processed during restart:

```
t=0s    Request starts → State created
t=2s    [SERVER CRASHES/RESTARTS] ⚠️
        → Active request LOST
        → Client gets connection error
        → State destroyed (ungracefully)

Client needs to retry the request
```

---

## 🛠️ Solutions for Persistence Across Restarts

If you need conversation memory that survives restarts, implement one of these:

### Option 1: Database Storage (Recommended for Production)

```python
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'
    
    user_id = Column(String, primary_key=True)
    messages = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

# Save state to database
def save_conversation(user_id: str, messages: list):
    """Save conversation to database."""
    db_session = Session()
    conversation = db_session.query(Conversation).filter_by(user_id=user_id).first()
    
    if conversation:
        conversation.messages = [msg.dict() for msg in messages]
        conversation.updated_at = datetime.now()
    else:
        conversation = Conversation(
            user_id=user_id,
            messages=[msg.dict() for msg in messages],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db_session.add(conversation)
    
    db_session.commit()

# Load state from database
def load_conversation(user_id: str) -> list:
    """Load conversation from database."""
    db_session = Session()
    conversation = db_session.query(Conversation).filter_by(user_id=user_id).first()
    
    if conversation:
        return [HumanMessage(**msg) if msg['type'] == 'human' 
                else AIMessage(**msg) for msg in conversation.messages]
    return []

# Modified endpoint
@app.post("/travel-assistant")
async def travel_assistant(request: TravelRequest, user_id: str):
    # Load previous conversation
    previous_messages = load_conversation(user_id)
    
    # Create state with history
    initial_state = {
        "messages": previous_messages + [HumanMessage(content=request.query)]
    }
    
    # Process
    result = await app_graph.ainvoke(initial_state)
    
    # Save updated conversation
    save_conversation(user_id, result["messages"])
    
    return result
```

**Benefits:**
- ✅ Survives server restarts
- ✅ Scales to multiple servers
- ✅ Can query conversation history
- ✅ Production-ready

---

### Option 2: LangGraph Checkpointer (Simpler)

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# Option A: In-Memory (lost on restart)
memory = MemorySaver()

# Option B: SQLite (persists across restarts)
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# Compile graph with checkpointer
app_graph = workflow.compile(checkpointer=checkpointer)

# Use with thread_id for conversation persistence
@app.post("/travel-assistant")
async def travel_assistant(request: TravelRequest, user_id: str):
    initial_state = {
        "messages": [HumanMessage(content=request.query)]
    }
    
    # Thread ID persists conversation
    config = {
        "configurable": {
            "thread_id": user_id  # Unique per user
        }
    }
    
    result = await app_graph.ainvoke(initial_state, config=config)
    return result
```

**Benefits:**
- ✅ Built-in LangGraph feature
- ✅ Survives restarts (with SqliteSaver)
- ✅ Automatic state management
- ✅ Less code to write

---

### Option 3: Redis Cache (High Performance)

```python
import redis
import json
import pickle

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def save_state(user_id: str, messages: list):
    """Save state to Redis."""
    # Serialize messages
    serialized = pickle.dumps(messages)
    
    # Store with expiration (e.g., 24 hours)
    redis_client.setex(
        f"conversation:{user_id}",
        86400,  # 24 hours
        serialized
    )

def load_state(user_id: str) -> list:
    """Load state from Redis."""
    serialized = redis_client.get(f"conversation:{user_id}")
    
    if serialized:
        return pickle.loads(serialized)
    return []

@app.post("/travel-assistant")
async def travel_assistant(request: TravelRequest, user_id: str):
    # Load from Redis
    previous_messages = load_state(user_id)
    
    initial_state = {
        "messages": previous_messages + [HumanMessage(content=request.query)]
    }
    
    result = await app_graph.ainvoke(initial_state)
    
    # Save to Redis
    save_state(user_id, result["messages"])
    
    return result
```

**Benefits:**
- ✅ Very fast
- ✅ Survives restarts
- ✅ Can set expiration
- ✅ Scales well

---

### Option 4: File-Based Storage (Development)

```python
import json
import os
from pathlib import Path

STORAGE_DIR = Path("./conversations")
STORAGE_DIR.mkdir(exist_ok=True)

def save_to_file(user_id: str, messages: list):
    """Save conversation to file."""
    filepath = STORAGE_DIR / f"{user_id}.json"
    
    data = {
        "user_id": user_id,
        "messages": [
            {
                "type": msg.__class__.__name__,
                "content": msg.content if hasattr(msg, 'content') else str(msg)
            }
            for msg in messages
        ],
        "updated_at": datetime.now().isoformat()
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_from_file(user_id: str) -> list:
    """Load conversation from file."""
    filepath = STORAGE_DIR / f"{user_id}.json"
    
    if not filepath.exists():
        return []
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    messages = []
    for msg in data["messages"]:
        if msg["type"] == "HumanMessage":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["type"] == "AIMessage":
            messages.append(AIMessage(content=msg["content"]))
    
    return messages
```

**Benefits:**
- ✅ Simple to implement
- ✅ Survives restarts
- ✅ Easy to debug
- ❌ Not scalable
- ❌ Development only

---

## 🎯 Comparison Table

| Method | Survives Restart | Scalable | Complexity | Best For |
|--------|------------------|----------|------------|----------|
| **Current (Stateless)** | ❌ N/A | ✅ Yes | ⭐ Simple | Simple queries |
| **Database (PostgreSQL)** | ✅ Yes | ✅ Yes | ⭐⭐⭐ Medium | Production |
| **LangGraph Checkpointer** | ✅ Yes | ✅ Yes | ⭐⭐ Easy | LangGraph apps |
| **Redis Cache** | ✅ Yes | ✅ Yes | ⭐⭐ Medium | High traffic |
| **File Storage** | ✅ Yes | ❌ No | ⭐ Simple | Development |

---

## 🚀 Migration Example: Adding Persistence

Here's how to upgrade current stateless server to persistent:

```python
# server.py - Modified with LangGraph Checkpointer

from langgraph.checkpoint.sqlite import SqliteSaver

# Create checkpointer
checkpointer = SqliteSaver.from_conn_string("./checkpoints.db")

# Compile with checkpointer
app_graph = workflow.compile(checkpointer=checkpointer)

# Modified request model
class TravelRequest(BaseModel):
    query: str
    stream: bool = False
    user_id: str = "default"  # NEW: User identifier

@app.post("/travel-assistant")
async def travel_assistant(request: TravelRequest):
    initial_state = {
        "messages": [HumanMessage(content=request.query)]
    }
    
    # Configuration with thread_id
    config = {
        "configurable": {
            "thread_id": request.user_id  # Conversation persistence
        }
    }
    
    if request.stream:
        async def event_generator():
            async for event in app_graph.astream(initial_state, config=config):
                # ... streaming logic ...
                yield event
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    else:
        result = await app_graph.ainvoke(initial_state, config=config)
        return TravelResponse(response=result["messages"][-1].content)
```

**Now conversations persist across:**
- ✅ Multiple requests
- ✅ Server restarts
- ✅ Different sessions

---

## 💡 Key Takeaways

### Current Implementation:
1. **Stateless by design** - No persistence needed
2. **State destroyed after each request** - Nothing in memory
3. **Server restart has NO impact** - State was already gone
4. **Simple and scalable** - No shared state between requests

### When to Add Persistence:
1. **Multi-turn conversations** needed
2. **"Remember my last query"** use case
3. **Context across sessions** required
4. **User history** important

### Restart Behavior:

**Without Persistence:**
```
Request → State created → Response → State destroyed
[RESTART - No impact, state already gone]
Request → New state → Response → Destroyed
```

**With Persistence (e.g., LangGraph Checkpointer):**
```
Request 1 → State → Response → Saved to DB
[RESTART]
Request 2 → Load from DB → Append → Response → Save to DB
```

---

## 📚 Documentation

- Current design: `STATE_AND_STREAMING_GUIDE.md`
- Visual diagrams: `STATE_FLOW_DIAGRAMS.md`
- LangGraph persistence: https://langchain-ai.github.io/langgraph/concepts/persistence/

---

## ✅ Summary

**Q: What happens to state when server restarts?**

**A: Nothing, because:**
1. State only exists during active requests (5-10 seconds)
2. State is destroyed immediately after response
3. No state exists in memory when server restarts
4. Each request creates fresh state regardless

**Current architecture is intentionally stateless for simplicity and scalability.**

**To add conversation memory that survives restarts, implement one of the persistence solutions above.**
