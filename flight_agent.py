"""
Flight Agent — A2A-compliant agent that searches for flights.

Exposes:
  GET  /.well-known/agent.json  → Agent Card (discovery)
  POST /a2a                     → Handle A2A task (search flights)
"""

import json
import random
from flask import Flask, request, jsonify
from a2a_models import AgentCard, AgentSkill, Task, TaskStatus, Artifact, A2AMessage

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Agent Card (the "business card" other agents read for discovery)
# ---------------------------------------------------------------------------
AGENT_CARD = AgentCard(
    name="Flight Agent",
    description="Searches for available flights based on destination and date. "
                "Returns a list of flight options with airlines, times, and prices.",
    url="http://localhost:5001",
    skills=[
        AgentSkill(
            id="flight-search",
            name="Flight Search",
            description="Find available flights to a destination on a given date.",
        )
    ],
)

# ---------------------------------------------------------------------------
# Simulated flight database
# ---------------------------------------------------------------------------
AIRLINES = ["Air France", "Delta Airlines", "United Airlines", "Emirates", "Lufthansa"]
FLIGHT_PREFIXES = {"Air France": "AF", "Delta Airlines": "DL", "United Airlines": "UA",
                   "Emirates": "EK", "Lufthansa": "LH"}


def search_flights(destination: str, date: str) -> list[dict]:
    """Simulate a flight search and return randomized results."""
    random.seed(hash(destination + date) % 2**32)
    num_results = random.randint(2, 4)
    results = []
    for _ in range(num_results):
        airline = random.choice(AIRLINES)
        prefix = FLIGHT_PREFIXES[airline]
        flight_number = f"{prefix}{random.randint(100, 999)}"
        departure_hour = random.randint(6, 20)
        duration_hours = random.randint(2, 12)
        price = round(random.uniform(150, 1200), 2)
        results.append({
            "airline": airline,
            "flight_number": flight_number,
            "destination": destination,
            "date": date,
            "departure": f"{departure_hour:02d}:00",
            "arrival": f"{(departure_hour + duration_hours) % 24:02d}:00",
            "duration_hours": duration_hours,
            "price_usd": price,
        })
    return sorted(results, key=lambda f: f["price_usd"])


# ---------------------------------------------------------------------------
# A2A Endpoints
# ---------------------------------------------------------------------------
@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card():
    """Step 1 — Discover: return the agent card."""
    return jsonify(AGENT_CARD.to_dict())


@app.route("/a2a", methods=["POST"])
def handle_task():
    """Steps 2-4 — Request → Process → Deliver."""
    data = request.get_json(force=True)
    task_data = data.get("task", {})

    # Build task from incoming message
    task = Task(
        id=task_data.get("id", ""),
        message=task_data.get("message", ""),
        status=TaskStatus.SUBMITTED,
    )

    print(f"\n✈️  [Flight Agent] Received task: {task.message}")

    # --- Step 3: Process ---
    task.update_status(TaskStatus.WORKING)
    print(f"   Status: {task.status.value}")

    # Parse destination and date from the message
    destination, date = _parse_request(task.message)
    flights = search_flights(destination, date)

    # --- Step 4: Deliver ---
    task.add_artifact(Artifact(
        name="flight-results",
        description=f"Available flights to {destination} on {date}",
        data={"flights": flights},
    ))
    task.update_status(TaskStatus.COMPLETED)
    print(f"   Status: {task.status.value} — found {len(flights)} flights")

    response = A2AMessage(
        sender="Flight Agent",
        receiver=data.get("sender", ""),
        task=task,
    )
    return jsonify(response.to_dict())


def _parse_request(message: str) -> tuple[str, str]:
    """Simple keyword extraction from the request message."""
    # Defaults
    destination = "Paris"
    date = "2026-06-15"

    msg_lower = message.lower()

    # Try to extract destination after 'to'
    if " to " in msg_lower:
        after_to = msg_lower.split(" to ", 1)[1]
        parts = after_to.split()
        if parts:
            # Take words until we hit a keyword like 'on', 'for', 'from'
            dest_words = []
            for w in parts:
                if w in ("on", "for", "from", "departing", "arriving", "date"):
                    break
                dest_words.append(w)
            if dest_words:
                destination = " ".join(dest_words).title()

    # Try to extract date after 'on'
    if " on " in msg_lower:
        after_on = msg_lower.split(" on ", 1)[1].strip()
        date_candidate = after_on.split()[0] if after_on.split() else date
        # Accept ISO dates or simple text
        if len(date_candidate) >= 6:
            date = date_candidate

    return destination, date


if __name__ == "__main__":
    print("✈️  Flight Agent starting on http://localhost:5001")
    print(f"   Agent Card: http://localhost:5001/.well-known/agent.json")
    app.run(port=5001, debug=False)
