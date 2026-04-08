"""
Agent Logger for Observability Stack

Standardized logging for AI agents (Kilo, OpenCode, etc.)
Compatible with Loki, Grafana, and LangGraph pipeline.
"""

import os
import json
import logging
import traceback
from datetime import datetime
from typing import Any
from pathlib import Path

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class AgentLogger:
    """
    Structured logger for AI agents.

    Features:
    - JSON structured logging
    - Loki push integration
    - Standardized labels for observability
    - Task tracking
    """

    def __init__(
        self,
        agent_name: str,
        loki_url: str | None = None,
        log_file: str | None = None,
        level: str = "INFO",
        environment: str = "production",
    ):
        self.agent_name = agent_name
        self.loki_url = loki_url or os.getenv("LOKI_URL", "http://100.91.164.109:3100")
        self.log_file = log_file
        self.environment = environment

        # Setup JSON logger
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.logger.setLevel(getattr(logging, level.upper()))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JsonFormatter(agent_name))
        self.logger.addHandler(console_handler)

        # File handler
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(JsonFormatter(agent_name))
            self.logger.addHandler(file_handler)

        # HTTP client for Loki
        self._client = None
        if HAS_HTTPX:
            self._client = httpx.Client(timeout=10.0)

    def _build_entry(self, level: str, message: str, event: str | None = None, **kwargs) -> dict:
        """Build a structured log entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent": self.agent_name,
            "level": level.lower(),
            "message": message,
            "environment": self.environment,
        }

        if event:
            entry["event"] = event

        entry["metadata"] = kwargs

        return entry

    def _log(self, level: str, message: str, event: str | None = None, **kwargs):
        """Internal log method."""
        entry = self._build_entry(level, message, event, **kwargs)

        # Log to standard logger
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(entry))

        # Push to Loki
        if self._client:
            self._push_to_loki(entry)

    def _push_to_loki(self, entry: dict):
        """Push a log entry to Loki."""
        try:
            labels = {
                "job": "ai-agent",
                "agent": self.agent_name,
                "environment": self.environment,
                "level": entry.get("level", "info"),
            }

            if "event" in entry:
                labels["event"] = entry["event"]

            payload = {
                "streams": [
                    {
                        "stream": labels,
                        "values": [
                            [str(int(datetime.utcnow().timestamp() * 1e9)), json.dumps(entry)]
                        ],
                    }
                ]
            }

            self._client.post(f"{self.loki_url}/loki/api/v1/push", json=payload)
        except Exception as e:
            self.logger.warning(f"Failed to push to Loki: {e}")

    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log("CRITICAL", message, **kwargs)

    # Convenience methods for common events

    def task_start(self, task_id: str, task_type: str, **kwargs):
        """Log task start."""
        self.info(
            f"Task started: {task_type}",
            event="task_start",
            task_id=task_id,
            task_type=task_type,
            **kwargs,
        )

    def task_complete(self, task_id: str, task_type: str, duration_ms: int, **kwargs):
        """Log task completion."""
        self.info(
            f"Task completed: {task_type}",
            event="task_complete",
            task_id=task_id,
            task_type=task_type,
            duration_ms=duration_ms,
            **kwargs,
        )

    def task_error(self, task_id: str, task_type: str, error: Exception, **kwargs):
        """Log task error."""
        self.error(
            f"Task failed: {task_type}",
            event="task_error",
            task_id=task_id,
            task_type=task_type,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            **kwargs,
        )

    def tool_call(self, tool_name: str, duration_ms: int, success: bool, **kwargs):
        """Log tool call."""
        self.info(
            f"Tool call: {tool_name}",
            event="tool_call",
            tool_name=tool_name,
            duration_ms=duration_ms,
            success=success,
            **kwargs,
        )

    def llm_call(
        self, model: str, prompt_tokens: int, completion_tokens: int, duration_ms: int, **kwargs
    ):
        """Log LLM API call."""
        self.info(
            f"LLM call: {model}",
            event="llm_call",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration_ms=duration_ms,
            **kwargs,
        )

    def agent_action(self, action: str, target: str | None = None, **kwargs):
        """Log agent action."""
        self.info(
            f"Agent action: {action}", event="agent_action", action=action, target=target, **kwargs
        )

    def file_operation(self, operation: str, path: str, success: bool, **kwargs):
        """Log file operation."""
        self.info(
            f"File operation: {operation}",
            event="file_operation",
            operation=operation,
            path=path,
            success=success,
            **kwargs,
        )

    def close(self):
        """Close the logger and HTTP client."""
        if self._client:
            self._client.close()


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, agent_name: str):
        super().__init__()
        self.agent_name = agent_name

    def format(self, record: logging.LogRecord) -> str:
        try:
            return record.getMessage()
        except Exception:
            return record.getMessage()


# ============================================
# Decorators for automatic logging
# ============================================


def logged(agent_name: str, loki_url: str | None = None):
    """Decorator to automatically log function calls."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = AgentLogger(agent_name, loki_url)
            task_id = f"{func.__name__}_{datetime.utcnow().timestamp()}"

            logger.task_start(task_id, func.__name__)
            start = datetime.utcnow()

            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start).total_seconds() * 1000
                logger.task_complete(task_id, func.__name__, int(duration))
                return result
            except Exception as e:
                logger.task_error(task_id, func.__name__, e)
                raise
            finally:
                logger.close()

        return wrapper

    return decorator


# ============================================
# Singleton logger for easy import
# ============================================

_default_logger: AgentLogger | None = None


def get_logger(agent_name: str = "default", **kwargs) -> AgentLogger:
    """Get or create the default logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = AgentLogger(agent_name, **kwargs)
    return _default_logger
