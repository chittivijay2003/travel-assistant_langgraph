# AI Travel Assistant with LangGraph

A production-ready travel planning assistant powered by Google Gemini API, LangGraph workflow orchestration, and FastAPI.

## Features

- 🤖 **AI-Powered Planning**: Uses Google Gemini 2.5 Flash for intelligent travel recommendations
- 🛠️ **Multi-Tool Integration**: Coordinates flight search, weather forecasting, and attraction discovery
- 📡 **Streaming Responses**: Real-time Server-Sent Events (SSE) for progressive response delivery
- 🔄 **Resilient Design**: Exponential backoff retry logic for fault tolerance
- 🌐 **RESTful API**: FastAPI endpoints with auto-generated documentation
- 🎨 **Web UI**: Built-in chat interface for easy testing

## Architecture

```
┌─────────────────────────────────────────┐
│         Client (Web UI/API)             │
└────────────────┬────────────────────────┘
                 │ HTTP/SSE
                 ↓
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌──────────┐  ┌──────────┐            │
│  │   /ui    │  │ /travel- │            │
│  │          │  │assistant │            │
│  └──────────┘  └─────┬────┘            │
└────────────────────┼──────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────┐
│      LangGraph Workflow Engine          │
│  ┌─────────┐    ┌────────┐    ┌──────┐ │
│  │  Agent  │───→│ Tools  │───→│ Agent │ │
│  │  Node   │    │  Node  │    │ Node │ │
│  └─────────┘    └────────┘    └──┬───┘ │
│       ↓ (no tools needed)         │     │
│       └───────────────────────────┘     │
│                  ↓ END                  │
└─────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────┐
│     Google Gemini API + Tools           │
│  ┌──────────────┐  ┌────────────────┐  │
│  │ Gemini 2.5   │  │ search_flights │  │
│  │    Flash     │  │ get_weather    │  │
│  │              │  │find_attractions│  │
│  └──────────────┘  └────────────────┘  │
│  [Exponential Backoff: 1s→2s→4s→8s]    │
└─────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/chittivijay2003/travel-assistant_langgraph.git
   cd travel-assistant_langgraph
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

5. **Run the server**
   ```bash
   uvicorn main:api_app --reload --port 8000
   ```

6. **Test the application**
   - Web UI: http://localhost:8000/ui
   - API Docs: http://localhost:8000/docs
   - Run tests: `python test.py`

## API Usage

### Endpoint: `/travel-assistant`

**Request:**
```bash
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a 3-day trip to Austin from Hyderabad",
    "stream": false
  }'
```

**Response:**
```json
{
  "response": "Flights Found:\n- Hyderabad → Austin, $574, 11:30 AM\n\nWeather Forecast:\n- Day 1: Clear\n- Day 2: Cloudy\n- Day 3: Light Rain\n\nTop Attractions:\n- Texas State Capitol\n- Lady Bird Lake\n- South Congress Avenue\n\nSuggested Itinerary:\nDay 1: Explore downtown Austin\nDay 2: Zilker Park and Lady Bird Lake\nDay 3: Congress Avenue Bridge",
  "used_tools": [
    "search_flights",
    "get_weather",
    "find_attractions"
  ],
  "status": "success"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | Complete travel plan (formatted text with `\n` line breaks) |
| `used_tools` | array | List of tools executed: `["search_flights", "get_weather", "find_attractions"]` |
| `status` | string | Response status: `"success"` or `"error"` |

**How the Response Looks (formatted):**
```
Flights Found:
- Hyderabad → Austin, $574, 11:30 AM

Weather Forecast:
- Day 1: Clear
- Day 2: Cloudy
- Day 3: Light Rain

Top Attractions:
- Texas State Capitol
- Lady Bird Lake
- South Congress Avenue

Suggested Itinerary:
Day 1: Explore downtown Austin
Day 2: Zilker Park and Lady Bird Lake
Day 3: Congress Avenue Bridge
```

### Streaming Mode

```bash
curl -X POST http://localhost:8000/travel-assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "Find flights to Tokyo", "stream": true}'
```

## Project Structure

```
travel-assistant_langgraph/
├── main.py                 # Core application (988 lines)
│   ├── Tools              # search_flights, get_weather, find_attractions
│   ├── Retry Logic        # Exponential backoff implementation
│   ├── LangGraph Workflow # Agent orchestration
│   └── FastAPI Endpoints  # /travel-assistant, /health, /ui
├── test.py                # Test suite (5 comprehensive tests)
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project metadata
├── .env.example          # Environment template
├── .gitignore            # Git exclusions
└── README.md             # This file
```

## Tools

The assistant uses three specialized tools:

1. **search_flights(origin, destination, date)**
   - Searches for flight options between cities
   - Validates if destination has commercial airport
   - Returns pricing ($350-$700), times, and airlines
   - Suggests alternatives (road/train) for cities without airports
   - Dynamic pricing based on routes

2. **get_weather(location, date)**
   - Fetches weather forecasts for any location
   - Provides 3-day outlook with random conditions
   - Includes temperature (20-32°C), humidity, and precipitation
   - Returns JSON formatted weather data

3. **find_attractions(location, category)**
   - Discovers tourist attractions by location
   - City-specific recommendations for known cities
   - Includes ratings (4.0-4.8) and estimated visit times
   - Returns informative message for unknown cities

## Configuration

Edit `.env` file:

```bash
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional (defaults shown)
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
LOG_LEVEL=INFO
```

## Development

### Run Tests
```bash
python test.py
```

**Test Coverage**:
- ✅ Flight queries with tool integration
- ✅ Weather forecast queries
- ✅ Attraction discovery queries
- ✅ Input validation (missing/empty prompts)
- ✅ All 5 tests passing

### View Logs
```bash
tail -f travel_assistant.log
```

### Code Structure
- **Lines 68-145**: search_flights with airport validation
- **Lines 148-195**: get_weather with dynamic conditions
- **Lines 198-377**: find_attractions with city database
- **Lines 387-427**: Exponential backoff retry decorator
- **Lines 456-516**: LangGraph workflow (agent/tools nodes)
- **Lines 537-615**: Streaming response implementation
- **Lines 668-750**: FastAPI endpoints (/travel-assistant, /health, /ui)

## Error Handling

- **Retry Logic**: Automatic retries with exponential backoff (1s → 2s → 4s → 8s)
- **Max Retries**: 3 attempts before failure
- **Logging**: Comprehensive logging to console and `travel_assistant.log`
- **Validation**: Pydantic models for request/response validation

## Supported Cities

Pre-configured attractions for:
- **Austin**: Texas State Capitol, Lady Bird Lake, South Congress Avenue, Zilker Park, Congress Avenue Bridge, Live Music District
- **Tokyo**: Shibuya Crossing, Senso-ji Temple, Tokyo Skytree, Tokyo Tower, Meiji Shrine, Ueno Park
- **Mancheriyal**: Kala Ashram, Godavari River Banks, Local Temples, Mancheriyal Market

**No-Airport Cities** (suggests road/train alternatives):
Mancheriyal, Karimnagar, Nizamabad, Adilabad, Khammam, Warangal, Nalgonda, Mahbubnagar, Medak, Rangareddy

Informative messages provided for cities not in the database.

## License

MIT License - See LICENSE file for details

## Author

Chitti Vijay

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test.py`
5. Submit a pull request

## Support

- 📧 Email: chittivijay2003@example.com
- 📝 Issues: Use GitHub Issues for bug reports
- 📚 Docs: API documentation at `/docs` endpoint

---

**Built with** ❤️ **using LangGraph, Gemini API, and FastAPI**
