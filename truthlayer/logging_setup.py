"""Structured logging: key=value lines by default, JSON lines with --log-json. Never logs secrets."""
from __future__ import annotations
import json
import logging
import sys

from .fixer import scrub


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({"time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"), "level": record.levelname,
                           "logger": record.name, "message": scrub(record.getMessage())})


class KVFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return scrub(f"{self.formatTime(record, '%H:%M:%S')} {record.levelname:<7} {record.name} {record.getMessage()}")


def setup(json_logs: bool = False, level: str = "INFO") -> None:
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(JsonFormatter() if json_logs else KVFormatter())
    root = logging.getLogger("truthlayer")
    root.handlers[:] = [h]
    root.setLevel(level.upper())
    root.propagate = False
