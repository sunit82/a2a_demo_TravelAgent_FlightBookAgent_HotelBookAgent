# A2A Protocol Demo — Travel Agent Booking System

This project demonstrates the **A2A (Agent-to-Agent) Protocol** using a Travel Agent
that orchestrates two sub-agents — a **Flight Agent** and a **Hotel Agent** — to fulfil
a travel booking request.

## Architecture

```
You (User)
    │
    ▼
┌─────────────┐
│ Travel Agent│  ← Orchestrator
└──────┬──────┘
       │  A2A Protocol
  ┌────┴────┐
  ▼         ▼
┌──────┐  ┌──────┐
│Flight│  │Hotel │
│Agent │  │Agent │
└──────┘  └──────┘
```

## A2A Flow (4 Steps)

| Step | Name       | What Happens |
|------|-----------|-------------|
| 1    | **Discover** | Travel Agent reads Agent Cards from sub-agents via `/.well-known/agent.json` |
| 2    | **Request**  | Travel Agent sends A2A messages (tasks) to Flight & Hotel agents |
| 3    | **Process**  | Each sub-agent processes the task (`submitted` → `working` → `completed`) |
| 4    | **Deliver**  | Sub-agents return results as artifacts; Travel Agent combines them |

## Files

| File | Description |
|------|-------------|
| `a2a_models.py` | Core A2A data models (AgentCard, Task, Artifact, A2AMessage) |
| `flight_agent.py` | Flight Agent — Flask server on port 5001 |
| `hotel_agent.py` | Hotel Agent — Flask server on port 5002 |
| `travel_agent.py` | Travel Agent — Orchestrator that coordinates sub-agents |
| `run_demo.py` | Demo runner — starts everything and runs sample bookings |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the demo
python run_demo.py
```

The demo will:
1. Start Flight Agent and Hotel Agent as background servers
2. Run the Travel Agent which discovers, requests, and combines results
3. Show two sample bookings (Paris and Tokyo)
4. Clean up all processes on exit

## Running Agents Individually

You can also start each agent separately for manual testing:

```bash
# Terminal 1 — Flight Agent
python flight_agent.py

# Terminal 2 — Hotel Agent
python hotel_agent.py

# Terminal 3 — Interactive Travel Agent
python -c "
from travel_agent import TravelAgent
agent = TravelAgent()
agent.discover_agents()
plan = agent.book_trip('London', '2026-08-10')
"
```

## API Endpoints

### Flight Agent (port 5001)
- `GET /.well-known/agent.json` — Agent Card
- `POST /a2a` — Submit a flight search task

### Hotel Agent (port 5002)
- `GET /.well-known/agent.json` — Agent Card
- `POST /a2a` — Submit a hotel search task
