"""
A2A Demo Runner — Travel Agent with Flight & Hotel Sub-Agents

This script:
1. Starts the Flight-Agent and Hotel-Agent as background Flask servers
2. Runs the Travel Agent orchestrator which demonstrates the full A2A flow:
   Discover → Request → Process → Deliver

Usage:
    python run_demo.py
"""

import os
import sys
import time
import subprocess
import atexit
import requests

# Track sub-processes so we can clean up on exit
processes: list[subprocess.Popen] = []


def cleanup():
    """Terminate all background agent processes."""
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


atexit.register(cleanup)


def start_agent(script: str, name: str) -> subprocess.Popen:
    """Start a sub-agent Flask server in a background process."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen(
        [sys.executable, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
    )
    processes.append(proc)
    print(f"   Started {name} (PID: {proc.pid})")
    return proc


def wait_for_server(url: str, name: str, timeout: int = 15):
    """Poll a server URL until it responds or timeout is reached."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                print(f"   ✅ {name} is ready")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(0.5)
    print(f"   ❌ {name} did not start within {timeout}s")
    return False


def main():
    print("╔" + "═" * 63 + "╗")
    print("║     A2A Protocol Demo — Travel Agent Booking System          ║")
    print("╠" + "═" * 63 + "╣")
    print("║  Agents:                                                     ║")
    print("║    🚌 Travel Agent  — Orchestrator (this process)            ║")
    print("║    ✈️  Flight-Agent  — http://localhost:5001                  ║")
    print("║    🏨 Hotel-Agent   — http://localhost:5002                  ║")
    print("║                                                              ║")
    print("║  A2A Flow: Discover → Request → Process → Deliver           ║")
    print("╚" + "═" * 63 + "╝")

    # ------------------------------------------------------------------
    # Start sub-agent servers
    # ------------------------------------------------------------------
    print("\n🚀 Starting sub-agent servers...")
    start_agent("flight_agent.py", "Flight-Agent (port 5001)")
    start_agent("hotel_agent.py", "Hotel-Agent (port 5002)")

    # Wait for servers to be ready
    print("   Waiting for servers to be ready...")
    wait_for_server("http://localhost:5001/.well-known/agent.json", "Flight-Agent")
    wait_for_server("http://localhost:5002/.well-known/agent.json", "Hotel-Agent")

    # ------------------------------------------------------------------
    # Run the Travel Agent demo
    # ------------------------------------------------------------------
    from travel_agent import TravelAgent

    agent = TravelAgent()

    # Step 1: Discover sub-agents
    agent.discover_agents()

    # Steps 2-4: Book a trip (Request → Process → Deliver)
    print("\n\n" + "🌍" * 30)
    print("   USER REQUEST: \"Book me a trip to Paris on 2026-06-15\"")
    print("🌍" * 30)

    travel_plan = agent.book_trip("Paris", "2026-06-15")

    # ------------------------------------------------------------------
    # Second demo — different destination
    # ------------------------------------------------------------------
    print("\n\n" + "🌏" * 30)
    print("   USER REQUEST: \"Book me a trip to Tokyo on 2026-07-20\"")
    print("🌏" * 30)

    travel_plan_2 = agent.book_trip("Tokyo", "2026-07-20")

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    print("\n\n" + "=" * 65)
    print("✅  A2A DEMO COMPLETE")
    print("=" * 65)
    print("""
    This demo showed the A2A (Agent-to-Agent) protocol in action:

    1. DISCOVER — Travel Agent read the "business cards" (Agent Cards)
       of the Flight-Agent and Hotel-Agent via /.well-known/agent.json

    2. REQUEST — Travel Agent sent standardized A2A messages to each
       sub-agent with the user's travel requirements

    3. PROCESS — Each sub-agent processed the task independently,
       with status transitions: submitted → working → completed

    4. DELIVER — Sub-agents returned results as artifacts.
       Travel Agent combined them into a unified travel plan.

    Architecture:
       You → Travel Agent → Flight-Agent  (via A2A Protocol)
                           → Hotel-Agent   (via A2A Protocol)
    """)

    # Clean up
    cleanup()


if __name__ == "__main__":
    main()
