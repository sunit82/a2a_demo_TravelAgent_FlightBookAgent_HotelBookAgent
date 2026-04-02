"""
Travel Agent — A2A Orchestrator

This is the main agent that the user interacts with. It:
1. DISCOVERS sub-agents by fetching their Agent Cards
2. REQUESTS work by sending A2A messages to Flight Agent and Hotel Agent
3. Waits while sub-agents PROCESS the tasks
4. Receives DELIVERED artifacts and combines them into a travel plan

Follows the 4-step A2A flow: Discover → Request → Process → Deliver
"""

import uuid
import requests
from a2a_models import Task, TaskStatus, A2AMessage

# ---------------------------------------------------------------------------
# Configuration — URLs where sub-agents are running
# ---------------------------------------------------------------------------
SUB_AGENT_URLS = [
    "http://localhost:5001",  # Flight Agent
    "http://localhost:5002",  # Hotel Agent
]


class TravelAgent:
    def __init__(self):
        self.name = "Travel Agent"
        self.discovered_agents: dict[str, dict] = {}

    # -----------------------------------------------------------------------
    # Step 1: DISCOVER — Read Agent Cards from sub-agents
    # -----------------------------------------------------------------------
    def discover_agents(self):
        """Fetch the Agent Card from each sub-agent's well-known endpoint."""
        print("\n" + "=" * 65)
        print("🔍  STEP 1 — DISCOVER: Reading Agent Cards")
        print("=" * 65)

        for base_url in SUB_AGENT_URLS:
            card_url = f"{base_url}/.well-known/agent.json"
            try:
                resp = requests.get(card_url, timeout=5)
                resp.raise_for_status()
                card = resp.json()
                self.discovered_agents[card["name"]] = {
                    "card": card,
                    "base_url": base_url,
                }
                print(f"\n   ✅ Discovered: {card['name']}")
                print(f"      URL: {card['url']}")
                print(f"      Description: {card['description'][:80]}...")
                skills = card.get("skills", [])
                for skill in skills:
                    print(f"      Skill: {skill['name']} — {skill['description']}")
            except requests.RequestException as e:
                print(f"\n   ❌ Failed to discover agent at {card_url}: {e}")

        print(f"\n   Discovered {len(self.discovered_agents)} agent(s) total.")

    # -----------------------------------------------------------------------
    # Step 2: REQUEST — Send A2A messages to sub-agents
    # -----------------------------------------------------------------------
    def _send_task(self, agent_name: str, message: str) -> dict | None:
        """Send an A2A task to a specific sub-agent."""
        agent_info = self.discovered_agents.get(agent_name)
        if not agent_info:
            print(f"   ❌ Agent '{agent_name}' not discovered.")
            return None

        task = Task(message=message)
        a2a_msg = A2AMessage(
            sender=self.name,
            receiver=agent_name,
            task=task,
        )

        a2a_url = f"{agent_info['base_url']}/a2a"
        print(f"\n   📤 Sending to {agent_name}: \"{message}\"")
        print(f"      Task ID: {task.id}")
        print(f"      Status:  {task.status.value}")

        try:
            resp = requests.post(a2a_url, json=a2a_msg.to_dict(), timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"   ❌ Request to {agent_name} failed: {e}")
            return None

    # -----------------------------------------------------------------------
    # Steps 3 & 4: PROCESS + DELIVER (handled by sub-agents, we receive results)
    # -----------------------------------------------------------------------
    def book_trip(self, destination: str, date: str) -> dict:
        """
        Orchestrate a full travel booking:
        - Ask Flight Agent for flights
        - Ask Hotel Agent for hotels
        - Combine results into a travel plan
        """
        print("\n" + "=" * 65)
        print(f"📋  STEP 2 — REQUEST: Booking trip to {destination} on {date}")
        print("=" * 65)

        # --- Request flights ---
        flight_response = self._send_task(
            "Flight Agent",
            f"Find a flight to {destination} on {date}"
        )

        # --- Request hotels ---
        hotel_response = self._send_task(
            "Hotel Agent",
            f"Find hotels in {destination} on {date}"
        )

        # --- Process responses (Step 3 status tracking) ---
        print("\n" + "=" * 65)
        print("⚙️   STEP 3 — PROCESS: Sub-agents processed the tasks")
        print("=" * 65)

        flights = []
        hotels = []

        if flight_response:
            flight_task = flight_response.get("task", {})
            status = flight_task.get("status", "unknown")
            print(f"\n   Flight Agent task status: {status}")
            if status == "completed":
                for artifact in flight_task.get("artifacts", []):
                    flights = artifact.get("data", {}).get("flights", [])
                    print(f"   ✅ Received {len(flights)} flight option(s)")

        if hotel_response:
            hotel_task = hotel_response.get("task", {})
            status = hotel_task.get("status", "unknown")
            print(f"\n   Hotel Agent task status: {status}")
            if status == "completed":
                for artifact in hotel_task.get("artifacts", []):
                    hotels = artifact.get("data", {}).get("hotels", [])
                    print(f"   ✅ Received {len(hotels)} hotel option(s)")

        # --- Deliver combined results (Step 4) ---
        print("\n" + "=" * 65)
        print("📦  STEP 4 — DELIVER: Combining results into travel plan")
        print("=" * 65)

        travel_plan = self._build_travel_plan(destination, date, flights, hotels)
        return travel_plan

    def _build_travel_plan(self, destination: str, date: str,
                           flights: list, hotels: list) -> dict:
        """Combine flight and hotel results into a unified travel plan."""
        plan = {
            "destination": destination,
            "date": date,
            "flights": flights,
            "hotels": hotels,
            "summary": "",
        }

        print(f"\n   🗺️  Travel Plan for {destination} on {date}")
        print("   " + "-" * 55)

        if flights:
            best_flight = flights[0]
            print(f"\n   ✈️  FLIGHTS ({len(flights)} options):")
            for i, f in enumerate(flights, 1):
                marker = " ⭐ BEST PRICE" if i == 1 else ""
                print(f"      {i}. {f['airline']} {f['flight_number']}"
                      f"  | {f['departure']}→{f['arrival']}"
                      f"  | ${f['price_usd']:.2f}{marker}")
        else:
            best_flight = None
            print("\n   ✈️  No flights found.")

        if hotels:
            best_hotel = hotels[0]
            print(f"\n   🏨  HOTELS ({len(hotels)} options):")
            for i, h in enumerate(hotels, 1):
                marker = " ⭐ BEST PRICE" if i == 1 else ""
                stars = "⭐" * h["stars"]
                print(f"      {i}. {h['hotel_name']} {stars}"
                      f"  | Rating: {h['rating']}"
                      f"  | ${h['price_per_night_usd']:.2f}/night{marker}")
                print(f"         Amenities: {', '.join(h['amenities'])}")
        else:
            best_hotel = None
            print("\n   🏨  No hotels found.")

        # Build summary
        summary_parts = [f"Travel plan for {destination} on {date}:"]
        if best_flight:
            summary_parts.append(
                f"Best flight: {best_flight['airline']} {best_flight['flight_number']} "
                f"at ${best_flight['price_usd']:.2f}"
            )
        if best_hotel:
            summary_parts.append(
                f"Best hotel: {best_hotel['hotel_name']} "
                f"at ${best_hotel['price_per_night_usd']:.2f}/night"
            )
        if best_flight and best_hotel:
            total = best_flight["price_usd"] + best_hotel["price_per_night_usd"]
            summary_parts.append(f"Estimated minimum cost: ${total:.2f} (flight + 1 night)")

        plan["summary"] = " | ".join(summary_parts)

        print("\n   " + "-" * 55)
        print(f"   📊 {plan['summary']}")
        print("   " + "-" * 55)

        return plan
