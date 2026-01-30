# Owlex Changes for Primary Agent Agnostic Support

## Overview

These changes make Owlex work with any primary agent (Codex, Claude, Gemini, etc.) instead of being hardcoded for Claude Code as the orchestrator.

## Changes Made

### 1. Parameter Rename: `claude_opinion` → `primary_agent_opinion`

**Files Modified:**
- `owlex/server.py` (lines 764, 779, 804, 844-847, 895, 909)
- `CODEX_SETUP.md` (all examples updated)

**What Changed:**
- MCP tool parameter renamed from `claude_opinion` to `primary_agent_opinion`
- Description updated to clarify it works for any primary agent
- All documentation updated to use new parameter name

**Backwards Compatibility:** ⚠️ Breaking change for API consumers (but parameter still internally maps to same logic)

### 2. Model Rename: `ClaudeOpinion` → `PrimaryAgentOpinion`

**Files Modified:**
- `owlex/models.py` (lines 94-101, 125)
- `owlex/council.py` (lines 18, 164, 185-191, 201)
- `owlex/__init__.py` (lines 15-16, 40-41)

**What Changed:**
- Pydantic model class renamed
- Added `ClaudeOpinion = PrimaryAgentOpinion` alias for backwards compatibility
- Both names exported in `__init__.py`

**Backwards Compatibility:** ✅ Maintained via alias

### 3. Config Rename: `include_claude_opinion` → `include_primary_agent_opinion`

**Files Modified:**
- `owlex/config.py` (lines 48, 110-117)

**What Changed:**
- Config class field renamed
- Environment variable: `COUNCIL_CLAUDE_OPINION` → `COUNCIL_PRIMARY_AGENT_OPINION`
- Legacy env var still supported for backwards compatibility

**Backwards Compatibility:** ✅ Maintained - reads both env vars with new one taking precedence

### 4. Log Messages Updated

**Files Modified:**
- `owlex/council.py` (line 164)

**What Changed:**
- "Claude's opinion received" → "Primary agent's opinion received"

## Environment Variables

### New (Recommended)
- `COUNCIL_PRIMARY_AGENT_OPINION` - Whether primary agent should share its opinion by default

### Legacy (Still Supported)
- `COUNCIL_CLAUDE_OPINION` - Old name, falls back to this if new one not set

## What Wasn't Changed (Intentionally)

### 1. Internal Parameter Name: `claude_opinion` in `council.py`
**Why:** The `deliberate()` method still uses `claude_opinion` as the parameter name internally. This is just a pass-through parameter and doesn't affect the external API.

**Location:** `owlex/council.py` line 97

**Could be changed if desired, but would require:**
- Updating all internal calls (lines 179, 457, 494, etc.)
- Updating `prompts.py` references (lines 45, 64, 85, 97, 129, 146, 160)
- More extensive testing

### 2. Prompt Labels in `prompts.py`
**Current state:** Hardcoded labels like `"CLAUDE'S ANSWER:"`, `"CODEX'S ANSWER:"`

**Why not changed:** These are accurate labels for the actual agents participating in the council. The prompts show which agent provided which answer.

**Location:** `owlex/prompts.py` lines 84-97

**Note:** These labels are correct as-is since they identify the council member (Claude via OpenRouter, Codex, etc.), not the primary agent.

### 3. Agent Name `claudeor`
**Current state:** The agent identifier for "Claude via OpenRouter"

**Why not changed:** This IS Claude (via OpenRouter API), so the name is accurate.

**Location:** Throughout codebase

## Testing Recommendations

### 1. Test with Codex as Primary Agent

```bash
export COUNCIL_EXCLUDE_AGENTS="codex"
export COUNCIL_PRIMARY_AGENT_OPINION="false"

# In Codex
"Use council_ask with primary_agent_opinion='My initial analysis...' 
to get feedback from Claude, Gemini, and OpenCode"
```

### 2. Test Backwards Compatibility

```bash
# Using legacy env var should still work
export COUNCIL_CLAUDE_OPINION="true"

# Old Python code using ClaudeOpinion should still work
from owlex import ClaudeOpinion  # Should work due to alias
```

### 3. Test with Different Primary Agents

Try with:
- Codex as primary (exclude codex, include others)
- Claude as primary (original use case)
- Gemini as primary (exclude gemini, include others)

## Migration Guide for Users

### If Using Environment Variables

**Old:**
```bash
export COUNCIL_CLAUDE_OPINION="true"
```

**New:**
```bash
export COUNCIL_PRIMARY_AGENT_OPINION="true"
```

### If Using Python API Directly

**Old:**
```python
from owlex import ClaudeOpinion

opinion = ClaudeOpinion(content="...", provided_at="...")
```

**New (Recommended):**
```python
from owlex import PrimaryAgentOpinion

opinion = PrimaryAgentOpinion(content="...", provided_at="...")
```

**Or (Legacy - Still Works):**
```python
from owlex import ClaudeOpinion  # Still available as alias

opinion = ClaudeOpinion(content="...", provided_at="...")
```

### If Using MCP Tool

**Old:**
```
council_ask(
    prompt="...",
    claude_opinion="My thinking..."
)
```

**New:**
```
council_ask(
    prompt="...",
    primary_agent_opinion="My thinking..."
)
```

## Benefits

1. ✅ **Works with any primary agent** - Codex, Claude, Gemini, or any future agent
2. ✅ **Clearer semantics** - Name reflects the actual role (primary agent, not just Claude)
3. ✅ **Backwards compatible** - Legacy names still work via aliases and env var fallbacks
4. ✅ **Better for Codex users** - No confusion about why it's called "claude_opinion"

## Potential Future Changes

If you want complete consistency throughout the codebase:

1. Rename internal `claude_opinion` parameter in `council.py.deliberate()`
2. Update prompt label generation to be dynamic based on primary agent
3. Consider renaming `claudeor` to something more generic (though "claudeor" is technically accurate)

These changes are optional and would be breaking changes for internal API.
