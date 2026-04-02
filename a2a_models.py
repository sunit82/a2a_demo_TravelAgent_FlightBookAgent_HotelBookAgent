"""
A2A (Agent-to-Agent) Protocol - Core Models

Defines the standard data structures used in agent-to-agent communication:
- AgentCard: Discovery mechanism ("business card" for agents)
- A2AMessage: Standard request/response format
- Task: Tracks work status across agents
- Artifact: Structured result data returned by agents
"""

import uuid
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional


class TaskStatus(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentSkill:
    """A capability that an agent advertises."""
    id: str
    name: str
    description: str
    input_modes: list[str] = field(default_factory=lambda: ["text"])
    output_modes: list[str] = field(default_factory=lambda: ["text"])


@dataclass
class AgentCard:
    """
    Agent Card — the 'business card' an agent publishes for discovery.
    Other agents read this to understand what the agent can do and how to reach it.
    """
    name: str
    description: str
    url: str
    version: str = "1.0"
    skills: list[AgentSkill] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Artifact:
    """Structured result data returned by an agent upon task completion."""
    name: str
    description: str
    data: dict
    mime_type: str = "application/json"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Task:
    """Represents a unit of work assigned to an agent."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.SUBMITTED
    message: str = ""
    artifacts: list[Artifact] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def update_status(self, status: TaskStatus):
        self.status = status
        self.updated_at = datetime.now().isoformat()

    def add_artifact(self, artifact: Artifact):
        self.artifacts.append(artifact)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value,
            "message": self.message,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class A2AMessage:
    """
    Standard A2A message format for inter-agent communication.
    Wraps a task with metadata about sender/receiver.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""
    task: Optional[Task] = None
    payload: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "task": self.task.to_dict() if self.task else None,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }
