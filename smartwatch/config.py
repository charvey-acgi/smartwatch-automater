from __future__ import annotations
from enum import Enum
from pathlib import Path
import yaml
from pydantic import BaseModel, field_validator


class EventType(str, Enum):
    created = "created"
    modified = "modified"
    deleted = "deleted"
    moved = "moved"


class ActionType(str, Enum):
    log = "log"
    copy = "copy"
    move = "move"
    run = "run"


class Action(BaseModel):
    type: ActionType
    destination: str | None = None   # for copy/move
    command: str | None = None       # for run

    @field_validator("destination", mode="before")
    @classmethod
    def validate_destination(cls, v, info):
        # Only required for copy/move
        return v

    def validate_for_action(self):
        if self.type in (ActionType.copy, ActionType.move) and not self.destination:
            raise ValueError(f"Action '{self.type}' requires a 'destination'")
        if self.type == ActionType.run and not self.command:
            raise ValueError("Action 'run' requires a 'command'")


class Rule(BaseModel):
    name: str
    patterns: list[str] = ["*"]
    on_events: list[EventType] = [EventType.created, EventType.modified]
    action: Action

    def model_post_init(self, __context):
        self.action.validate_for_action()


class WatchConfig(BaseModel):
    path: str
    recursive: bool = True
    rules: list[Rule]


class Config(BaseModel):
    watch: list[WatchConfig]

    @field_validator("watch")
    @classmethod
    def must_have_watches(cls, v):
        if not v:
            raise ValueError("Config must define at least one watch path")
        return v


def load_config(path: str) -> Config:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    return Config(**raw)