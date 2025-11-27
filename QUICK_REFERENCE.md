# Quick Reference Card - State & Streaming

## 🎯 Quick Answers

### How long is state available?
**5-10 seconds** (single request only)

### Where is state saved?
**RAM only** (Python process memory, destroyed after request)

### How to see streaming UI?
```bash
open streaming_test.html
# or visit http://localhost:8000/docs
```

---

## 📡 Test URLs

```bash
# Streaming Web UI (Best for visual streaming)
http://localhost:8000/ui

# Swagger UI (Best for API testing)
http://localhost:8000/docs

# Health Check
http://localhost:8000/health

# Main Endpoint
POST http://localhost:8000/travel-assistant
```

---

## 🧪 Quick Tests

### cURL Streaming:
```bash
curl -N -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "Plan Tokyo trip", "stream": true}'
```

### Python Script:
```bash
python3 test_streaming.py
```

### Browser:
```bash
open streaming_test.html
```

---

## 💾 State Facts

| Aspect | Value |
|--------|-------|
| Lifetime | 5-10 seconds |
| Storage | RAM only |
| Size | ~20 KB per request |
| Persistence | None |
| Between Requests | Not shared |

---

## 🌊 Streaming Format

```
data: {"content": "text chunk"}

data: [DONE]
```

---

## 📚 Full Docs

- `ANSWERS_TO_QUESTIONS.md` - Complete answers
- `STATE_AND_STREAMING_GUIDE.md` - Detailed guide
- `STATE_FLOW_DIAGRAMS.md` - Visual diagrams
- `QUICK_START_TESTING.md` - Testing guide
- `api_tests.http` - REST client tests
