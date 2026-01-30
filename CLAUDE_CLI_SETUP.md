# Claude CLI Integration - Installation Guide

## What Was Added

I've added Claude CLI support to Owlex so that when Codex calls the council, it can get opinions from the actual Claude CLI binary (not just Claude via OpenRouter API).

### Files Created/Modified:

1. **NEW: `owlex/agents/claude.py`** - Claude CLI runner implementation
2. **Modified: `owlex/models.py`** - Added `Agent.CLAUDE` enum value and `claude` field to `CouncilRound`
3. **Modified: `owlex/agents/__init__.py`** - Exported `ClaudeRunner`  
4. **Modified: `owlex/engine.py`** - Registered `claude_runner` instance
5. **Modified: `owlex/council.py`** - Added Claude CLI to `all_agents` list

### ⚠️ Remaining Work

The council logic in `council.py` needs Claude added to:
- Round 1 execution (around line 273-330)
- Round 2 execution (around line 500-750)

This is repetitive code similar to the existing codex/gemini/opencode blocks.

## Installation

### Step 1: Install from Local Directory

```bash
cd /Users/aaronolin/localdev/ai/mcp/owlex
uv tool install .
```

Or for editable install (changes reflect immediately):
```bash
uv tool install --editable .
```

### Step 2: Configure Codex

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.owlex]
command = "owlex-server"
startup_timeout_sec = 60.0

[mcp_servers.owlex.env]
# Exclude Codex since it's the primary agent
COUNCIL_EXCLUDE_AGENTS = "codex"

# Optional: Also exclude agents you don't have installed
# COUNCIL_EXCLUDE_AGENTS = "codex,gemini,opencode,claudeor"

OWLEX_DEFAULT_TIMEOUT = "300"
```

### Step 3: Test Claude CLI

Verify Claude CLI works:

```bash
# Test non-interactive mode
claude --print "What is 2+2?"

# Check history file
ls -la ~/.claude/history.jsonl
```

## Usage in Codex

### Basic Council Query with Claude

```
I need architectural advice. Use council_ask to get perspectives from 
Claude, Gemini, and OpenCode on whether to use microservices or monolith.
```

### Exclude Agents You Don't Have

If you only want to use Claude:

```toml
[mcp_servers.owlex.env]
COUNCIL_EXCLUDE_AGENTS = "codex,gemini,opencode,claudeor"
```

Then only Claude CLI will be consulted.

## Complete the Integration

To finish adding Claude to Round 1 and Round 2, you need to add blocks similar to the existing agent code.

### Round 1 Addition (after line 300 in council.py):

```python
if "claude" not in excluded:
    claude_role = roles.get("claude")
    claude_prompt = inject_role_prefix(prompt, claude_role)
    
    claude_task = self._engine.create_task(
        command=f"council_{Agent.CLAUDE.value}",
        args={"prompt": claude_prompt, "working_directory": working_directory},
        context=self.context,
    )
    tasks["claude"] = claude_task
    
    _claude_prompt = claude_prompt
    
    async def run_claude():
        await self._engine.run_agent(
            claude_task, claude_runner, mode="exec",
            prompt=_claude_prompt, working_directory=working_directory
        )
        elapsed = (datetime.now() - round1_start).total_seconds()
        status = "completed" if claude_task.status == "completed" else "failed"
        self.log(f"Claude {status} ({elapsed:.1f}s)")
        await self.notify(f"Claude {status} ({elapsed:.1f}s)")
    
    claude_task.async_task = asyncio.create_task(run_claude())
    async_tasks.append(claude_task.async_task)
```

### Session ID Parsing (after line 440):

```python
async def parse_claude_session():
    if "claude" not in tasks or tasks["claude"].status != "completed":
        return None
    session = await claude_runner.parse_session_id(
        "", since_mtime=r1_start_mtime, working_directory=working_directory
    )
    if session and not claude_runner.validate_session_id(session):
        self.log(f"Claude session ID validation failed: {session}")
        return None
    if not session:
        self.log("Claude session ID not found, R2 will use exec mode")
    return session
```

### Return Statement Update (around line 446):

```python
claude_session, codex_session, gemini_session, opencode_session, claudeor_session = await asyncio.gather(
    parse_claude_session(),
    parse_codex_session(),
    parse_gemini_session(),
    parse_opencode_session(),
    parse_claudeor_session(),
)

return CouncilRound(
    codex=build_agent_response(tasks["codex"], Agent.CODEX, session_id=codex_session) if "codex" in tasks else None,
    claude=build_agent_response(tasks["claude"], Agent.CLAUDE, session_id=claude_session) if "claude" in tasks else None,
    gemini=build_agent_response(tasks["gemini"], Agent.GEMINI, session_id=gemini_session) if "gemini" in tasks else None,
    opencode=build_agent_response(tasks["opencode"], Agent.OPENCODE, session_id=opencode_session) if "opencode" in tasks else None,
    claudeor=build_agent_response(tasks["claudeor"], Agent.CLAUDEOR, session_id=claudeor_session) if "claudeor" in tasks else None,
)
```

### Round 2 Addition (around line 500):

Similar pattern - add Claude to the failed agents check, get Claude's session ID, build deliberation prompts, and execute.

### Prompts Update (prompts.py):

Add `claude_answer` parameter to `build_deliberation_prompt()` and `build_deliberation_prompt_with_role()`:

```python
def build_deliberation_prompt(
    original_prompt: str,
    codex_answer: str | None = None,
    claude_answer: str | None = None,  # ADD THIS
    gemini_answer: str | None = None,
    # ... rest
```

And add to the parts list:

```python
if claude_answer:
    parts.extend(["", "CLAUDE'S ANSWER:", claude_answer])
```

## Testing

### 1. Verify Installation

```bash
owlex-server --version
```

### 2. Test in Codex

```
Use council_ask with prompt="What's the best way to handle rate limiting in APIs?" 
and get feedback from the council.
```

### 3. Check Logs

Claude CLI should appear in the council logs:
- "Round 1: querying Codex, Claude, Gemini, Opencode..."
- "Claude completed (X.Xs)"

## Troubleshooting

### "claude command not found"

Ensure Claude CLI is installed and in PATH:
```bash
which claude
claude --version
```

### Claude Not in Council

Check excluded agents:
```bash
# In Codex
"What agents are available? Use the owlex resource owlex://agents"
```

### Session Resume Not Working

Claude session IDs are stored in `~/.claude/history.jsonl`. If this file doesn't exist or isn't being updated, session resume will fall back to exec mode (which still works, just without context).

## Benefits

✅ **Use actual Claude CLI** - Not just API, get the full Claude CLI experience  
✅ **Session continuity** - Round 2 can resume from Round 1 session
✅ **Works offline** - Claude CLI doesn't need OpenRouter API key  
✅ **Better for Codex** - Codex can genuinely consult with Claude as a peer

## Next Steps

1. Complete the Round 1 and Round 2 integration (copy/paste patterns above)
2. Test with all combinations of agents
3. Update prompts.py to include Claude's answers in deliberation
4. Consider adding config options for Claude CLI (like permission modes)
