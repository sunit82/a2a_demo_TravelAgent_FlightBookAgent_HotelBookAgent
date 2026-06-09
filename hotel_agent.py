"""
Hotel Agent — A2A-compliant agent that searches for hotels.

Configuration is loaded from agents/hotel_agent.md which defines
this agent's identity, skills, and behavioral instructions.

Exposes:
  GET  /.well-known/agent.json  → Agent Card (discovery)
  POST /a2a                     → Handle A2A task (search hotels)
"""

import random
from flask import Flask, request, jsonify
from a2a_models import AgentCard, AgentSkill, Task, TaskStatus, Artifact, A2AMessage
from agent_loader import load_agent_config, get_agent_md_path

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Load configuration from agent.md
# ---------------------------------------------------------------------------
_agent_md = load_agent_config(get_agent_md_path("hotel_agent"))
_config = _agent_md["config"]
AGENT_INSTRUCTIONS = _agent_md["instructions"]

# ---------------------------------------------------------------------------
# Agent Card — built from agent.md configuration
# ---------------------------------------------------------------------------
AGENT_CARD = AgentCard(
    name=_config["name"],
    description=_config["description"],
    url=_config["url"],
    skills=[
        AgentSkill(
            id=s["id"],
            name=s["name"],
            description=s["description"],
        )
        for s in _config.get("skills", [])
    ],
)

# ---------------------------------------------------------------------------
# Simulated hotel database
# ---------------------------------------------------------------------------
HOTEL_NAMES = {
    "Paris": ["Le Grand Hôtel", "Hôtel de la Paix", "Marriott Champs-Élysées",
              "Ibis Paris Centre", "The Ritz Paris"],
    "London": ["The Savoy", "Premier Inn London", "Hilton Park Lane",
               "Travelodge Central", "Claridge's"],
    "Tokyo": ["Hotel Gracery Shinjuku", "The Peninsula Tokyo", "APA Hotel Ginza",
              "Park Hyatt Tokyo", "Dormy Inn Akihabara"],
    "New York": ["The Plaza", "Pod 51 Hotel", "Hilton Midtown",
                 "The Standard High Line", "Holiday Inn Times Square"],
}

DEFAULT_HOTELS = ["Grand Hotel", "City Inn", "Comfort Suites", "Park Plaza", "Budget Lodge"]


def search_hotels(destination: str, checkin: str) -> list[dict]:
    """Simulate a hotel search and return randomized results."""
    random.seed(hash(destination + checkin) % 2**32)

    hotel_list = HOTEL_NAMES.get(destination, DEFAULT_HOTELS)
    num_results = random.randint(2, min(4, len(hotel_list)))
    selected = random.sample(hotel_list, num_results)

    results = []
    for name in selected:
        stars = random.randint(2, 5)
        price = round(random.uniform(60, 500) * (stars / 3), 2)
        rating = round(random.uniform(3.0, 5.0), 1)
        results.append({
            "hotel_name": name,
            "destination": destination,
            "checkin_date": checkin,
            "stars": stars,
            "rating": rating,
            "price_per_night_usd": price,
            "amenities": random.sample(
                ["WiFi", "Pool", "Gym", "Spa", "Breakfast", "Parking", "Restaurant", "Bar"],
                k=random.randint(2, 5),
            ),
        })
    return sorted(results, key=lambda h: h["price_per_night_usd"])


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

    task = Task(
        id=task_data.get("id", ""),
        message=task_data.get("message", ""),
        status=TaskStatus.SUBMITTED,
    )

    print(f"\n🏨  [Hotel Agent] Received task: {task.message}")

    # --- Step 3: Process ---
    task.update_status(TaskStatus.WORKING)
    print(f"   Status: {task.status.value}")

    destination, checkin = _parse_request(task.message)
    hotels = search_hotels(destination, checkin)

    # --- Step 4: Deliver ---
    task.add_artifact(Artifact(
        name="hotel-results",
        description=f"Available hotels in {destination} from {checkin}",
        data={"hotels": hotels},
    ))
    task.update_status(TaskStatus.COMPLETED)
    print(f"   Status: {task.status.value} — found {len(hotels)} hotels")

    response = A2AMessage(
        sender="Hotel Agent",
        receiver=data.get("sender", ""),
        task=task,
    )
    return jsonify(response.to_dict())


def _parse_request(message: str) -> tuple[str, str]:
    """Simple keyword extraction from the request message."""
    destination = "Paris"
    checkin = "2026-06-15"

    msg_lower = message.lower()

    if " in " in msg_lower:
        after_in = msg_lower.split(" in ", 1)[1]
        parts = after_in.split()
        dest_words = []
        for w in parts:
            if w in ("on", "for", "from", "checkin", "check-in", "date", "starting"):
                break
            dest_words.append(w)
        if dest_words:
            destination = " ".join(dest_words).title()

    if " on " in msg_lower:
        after_on = msg_lower.split(" on ", 1)[1].strip()
        date_candidate = after_on.split()[0] if after_on.split() else checkin
        if len(date_candidate) >= 6:
            checkin = date_candidate

    return destination, checkin


if __name__ == "__main__":
    port = int(_config["url"].split(":")[-1])
    print(f"🏨  {_config['name']} starting on {_config['url']}")
    print(f"   Agent Card: {_config['url']}/.well-known/agent.json")
    print(f"   Loaded instructions from: agents/hotel_agent.md")
    app.run(port=port, debug=False)
