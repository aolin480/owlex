"""
Claude CLI agent runner.
"""

import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from ..config import config
from .base import AgentRunner, AgentCommand


async def get_latest_claude_session(
    since_mtime: float | None = None,
    max_retries: int = 3,
    retry_delay: float = 0.3,
) -> str | None:
    """
    Find the most recent Claude session ID from filesystem.
    
    Claude stores session history in ~/.claude/history.jsonl
    We parse the latest session ID from this file.
    
    Args:
        since_mtime: Only consider sessions created after this timestamp.
        max_retries: Number of retries if no session found (handles I/O lag).
        retry_delay: Delay between retries in seconds.
    
    Returns:
        Session ID if found, None otherwise
    """
    history_file = Path.home() / ".claude" / "history.jsonl"
    if not history_file.exists():
        return None
    
    for attempt in range(max_retries):
        try:
            # Check file modification time first
            file_mtime = history_file.stat().st_mtime
            if since_mtime is not None and file_mtime < since_mtime:
                # File hasn't been updated since we started, no new session
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return None
            
            # Read history file and find most recent session
            with open(history_file, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return None
            
            # Parse the last line (most recent session)
            import json
            try:
                last_entry = json.loads(lines[-1].strip())
                session_id = last_entry.get('id')
                if session_id:
                    return session_id
            except (json.JSONDecodeError, KeyError):
                pass
                
        except (OSError, IOError):
            pass
        
        # Retry with delay if no session found
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    
    return None


def clean_claude_output(raw_output: str, original_prompt: str = "") -> str:
    """Clean Claude CLI output by removing noise."""
    # No special cleaning for Claude CLI by default
    cleaned = raw_output
    # Remove excessive newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


class ClaudeRunner(AgentRunner):
    """Runner for Claude CLI."""
    
    @property
    def name(self) -> str:
        return "claude"
    
    def build_exec_command(
        self,
        prompt: str,
        working_directory: str | None = None,
        enable_search: bool = False,
        **kwargs,
    ) -> AgentCommand:
        """Build command for starting a new Claude session."""
        full_command = ["claude", "--print"]  # Non-interactive mode
        
        # Add permission mode (dontAsk for non-interactive auto-approval)
        full_command.extend(["--permission-mode", "dontAsk"])
        
        if working_directory:
            # Claude doesn't have a --cd flag, we set cwd instead
            pass
        
        # Prompt is passed as positional argument
        full_command.append(prompt)
        
        return AgentCommand(
            command=full_command,
            prompt="",  # Prompt passed as CLI arg, not stdin
            cwd=working_directory,
            output_prefix="Claude Output",
            not_found_hint="Please ensure Claude CLI is installed and in your PATH.",
            stream=False,  # Claude --print outputs all at once
        )
    
    def build_resume_command(
        self,
        session_ref: str,
        prompt: str,
        working_directory: str | None = None,
        enable_search: bool = False,
        **kwargs,
    ) -> AgentCommand:
        """Build command for resuming an existing Claude session."""
        full_command = ["claude", "--print"]  # Non-interactive mode
        
        # Add permission mode (dontAsk for non-interactive auto-approval)
        full_command.extend(["--permission-mode", "dontAsk"])
        
        # Resume session
        if session_ref == "--continue":
            full_command.append("--continue")
        else:
            # Validate session_ref to prevent flag injection
            if session_ref.startswith("-"):
                raise ValueError(f"Invalid session_ref: '{session_ref}' - cannot start with '-'")
            full_command.extend(["--resume", session_ref])
        
        # Prompt as positional argument
        full_command.append(prompt)
        
        return AgentCommand(
            command=full_command,
            prompt="",  # Prompt passed as CLI arg, not stdin
            cwd=working_directory,
            output_prefix="Claude Resume Output",
            not_found_hint="Please ensure Claude CLI is installed and in your PATH.",
            stream=False,
        )
    
    def get_output_cleaner(self) -> Callable[[str, str], str]:
        return clean_claude_output
    
    async def parse_session_id(
        self,
        output: str,
        since_mtime: float | None = None,
        working_directory: str | None = None,
    ) -> str | None:
        """
        Get session ID for Claude.
        
        Claude stores session history in ~/.claude/history.jsonl
        We parse the most recent session ID from this file.
        
        Args:
            output: Ignored (Claude doesn't output session IDs to stdout)
            since_mtime: Only consider sessions created after this timestamp
            working_directory: Ignored (Claude sessions are global)
        
        Returns:
            Session ID if found, None otherwise
        """
        return await get_latest_claude_session(since_mtime=since_mtime)
    
    def validate_session_id(self, session_id: str) -> bool:
        """Validate a Claude session ID."""
        if not session_id:
            return False
        # Allow --continue as special case
        if session_id == "--continue":
            return True
        # Reject IDs that start with dash (flag injection)
        if session_id.startswith("-"):
            return False
        # Reject IDs with shell metacharacters
        if any(c in session_id for c in [";", "|", "&", "$", "`", "(", ")", "{", "}", "<", ">", "\n", "\r"]):
            return False
        return True
