"""
Agent runners for owlex.
Each agent knows how to construct and run its specific CLI commands.
"""

from .base import AgentRunner
from .codex import CodexRunner
from .claude import ClaudeRunner
from .gemini import GeminiRunner
from .opencode import OpenCodeRunner
from .claudeor import ClaudeORRunner

__all__ = ["AgentRunner", "CodexRunner", "ClaudeRunner", "GeminiRunner", "OpenCodeRunner", "ClaudeORRunner"]
