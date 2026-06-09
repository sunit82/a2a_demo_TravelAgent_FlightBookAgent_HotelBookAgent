"""
Agent Card Loader — Reads agent md files and parses YAML frontmatter.

Each agent md file (e.g. agents/flight_agent.md) contains YAML frontmatter
(between --- delimiters) with structured configuration, followed by markdown
instructions describing the agent's behavior.
"""

import os
import yaml


def load_agent_config(agent_md_path: str) -> dict:
    """
    Load and parse an agent.md file.

    Returns a dict with:
      - 'config': parsed YAML frontmatter (dict)
      - 'instructions': markdown body (str)
    """
    with open(agent_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse YAML frontmatter between --- delimiters
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            instructions = parts[2].strip()
            config = yaml.safe_load(frontmatter) or {}
            return {"config": config, "instructions": instructions}

    # No frontmatter found — treat entire content as instructions
    return {"config": {}, "instructions": content}


def get_agent_md_path(agent_name: str) -> str:
    """Get the absolute path to an agent's md file (e.g. agents/flight_agent.md)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "agents", f"{agent_name}.md")
