# Owlex for Codex - Council Setup

This guide shows how to use Owlex as an MCP server in Codex, allowing Codex to consult with Claude, Gemini, and OpenCode for second opinions.

## Architecture

```
Codex (Primary Agent, MCP Client)
  ↓ calls council_ask via MCP
Owlex MCP Server
  ↓ orchestrates council members in parallel
  ├→ Claude Code (via OpenRouter or API)
  ├→ Gemini CLI
  └→ OpenCode CLI
  ↓ returns all responses
Codex
  ↓ synthesizes final decision
```

## Installation

1. Install Owlex:
   ```bash
   uv tool install git+https://github.com/aolin480/owlex.git
   ```

2. Add to Codex config (`~/.codex/config.toml`):
   ```toml
   [mcp_servers.owlex]
   command = "owlex-server"
   startup_timeout_sec = 60.0
   
   [mcp_servers.owlex.env]
   # Exclude Codex from council since Codex is the primary agent
   COUNCIL_EXCLUDE_AGENTS = "codex"
   
   # Optional: Exclude agents you don't have installed
   # COUNCIL_EXCLUDE_AGENTS = "codex,gemini,opencode"
   
   # Configure timeout (see Configuration section)
   OWLEX_DEFAULT_TIMEOUT = "300"
   ```

## Configuration Options

### Required: Exclude Codex
Since Codex is the primary agent calling the council, exclude it from council members:
```bash
export COUNCIL_EXCLUDE_AGENTS="codex"
```

### Optional: Claude via OpenRouter
To include Claude in the council, set up OpenRouter:
```bash
export OPENROUTER_API_KEY="your-key-here"
export CLAUDEOR_MODEL="anthropic/claude-sonnet-4"  # or deepseek/deepseek-v3.2
```

### Optional: Exclude Missing Agents
If you don't have certain CLI tools installed:
```bash
# Only use Claude (via OpenRouter)
export COUNCIL_EXCLUDE_AGENTS="codex,gemini,opencode"

# Use Claude + Gemini (no OpenCode)
export COUNCIL_EXCLUDE_AGENTS="codex,opencode"
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COUNCIL_EXCLUDE_AGENTS` | `""` | Comma-separated list: `codex,gemini,opencode,claudeor` |
| `OWLEX_DEFAULT_TIMEOUT` | `300` | Timeout per agent in seconds |
| `OPENROUTER_API_KEY` | `""` | Required for Claude via OpenRouter |
| `CLAUDEOR_MODEL` | `""` | OpenRouter model (e.g., `anthropic/claude-sonnet-4`) |
| `OPENCODE_AGENT` | `plan` | OpenCode mode: `plan` (read-only) or `build` |
| `GEMINI_YOLO_MODE` | `false` | Auto-approve Gemini actions |

## Usage in Codex

### Basic Council Query

When you need multiple perspectives on a technical decision:

```
I need to decide between using a monorepo vs multiple repos for 5 microservices.

Can you use the owlex council_ask tool to get input from Claude, Gemini, 
and OpenCode, then synthesize the best recommendation based on our specific needs?
```

Codex will:
1. Call `council_ask` with the prompt
2. Owlex queries all council members in parallel
3. Return all responses to Codex
4. Codex synthesizes and provides final recommendation

### Sharing Your Initial Thinking

The `primary_agent_opinion` parameter allows you to share your initial analysis with the council:

```
I'm leaning towards a monorepo because we need shared component libraries, 
but I'm concerned about build times.

Use council_ask with my thinking as the 'primary_agent_opinion' parameter
and get feedback from the council.
```

### Specialist Roles

Assign specialist perspectives to council members:

```
Use council_ask with roles={"claudeor": "security", "gemini": "perf", "opencode": "skeptic"}
to review this authentication flow.
```

Available roles:
- `security` - Security analyst
- `perf` - Performance optimizer  
- `skeptic` - Devil's advocate
- `architect` - System architect
- `maintainer` - Code maintainer
- `dx` - Developer experience
- `testing` - Testing specialist

### Team Presets

Use predefined role combinations:

```
Use council_ask with team="security_audit" to review this API design.
```

Available teams:
- `security_audit` - Focus on security, edge cases, architecture
- `code_review` - Maintainability, performance, testing
- `architecture_review` - Design patterns, scalability, maintainability
- `devil_advocate` - All skeptics finding flaws
- `balanced` - Mix of security, performance, maintainability

### Two-Round Deliberation

Enable critique mode for more thorough analysis:

```
Use council_ask with deliberate=true and critique=true.

Round 1: Each agent analyzes independently
Round 2: Agents see others' answers and critique/find flaws
```

## MCP Tool Reference

### council_ask

Main tool for council deliberation.

**Parameters:**
- `prompt` (required): Question or task for the council
- `primary_agent_opinion` (optional): Your initial thinking to share with council members
- `working_directory` (optional): Context directory for agents
- `deliberate` (default: true): Enable two-round deliberation
- `critique` (default: false): Round 2 uses critique mode
- `roles` (optional): Role assignments (dict or list)
- `team` (optional): Team preset name
- `timeout` (default: 300): Timeout per agent in seconds

**Returns:**
- Task ID for async execution
- Use `wait_for_task` to get results

### wait_for_task

Wait for council deliberation to complete.

**Parameters:**
- `task_id` (required): Task ID from council_ask
- `timeout` (optional): Max seconds to wait

**Returns:**
- Complete council response with all agent answers

### Individual Agent Tools

Query specific agents directly (without council):
- `start_claudeor_session` - New Claude session
- `start_gemini_session` - New Gemini session  
- `start_opencode_session` - New OpenCode session
- `resume_*_session` - Resume existing session

## Example Workflows

### Architecture Decision

```
Codex: I need to help the user choose between microservices and monolith.
       Let me consult the council for different perspectives.

       [Calls council_ask with:
        - prompt: "Should we use microservices or monolith for a 10-person team?"
        - primary_agent_opinion: "My initial analysis: monolith for simplicity"
        - team: "architecture_review"]

Owlex: [Queries Claude, Gemini, OpenCode in parallel]
       [Returns all responses]

Codex: [Analyzes all responses]
       [Synthesizes recommendation]
       "Based on council input, here's my recommendation..."
```

### Security Review

```
Codex: Let me get security perspectives on this auth flow.

       [Calls council_ask with:
        - prompt: "Review this JWT implementation"
        - roles: ["security", "skeptic", "dx"]
        - critique: true]

Owlex: Round 1: Independent security analysis
       Round 2: Critique each other's findings

Codex: [Synthesizes security concerns]
       "Critical issues found by the council:..."
```

## Troubleshooting

### "Command not found" errors

If you get errors about missing CLIs:
1. Check which agents are failing
2. Add them to `COUNCIL_EXCLUDE_AGENTS`
3. Or install the missing CLI tools

### Timeout issues

Increase timeout for slow operations:
```toml
[mcp_servers.owlex.env]
OWLEX_DEFAULT_TIMEOUT = "600"  # 10 minutes
```

### No council members available

Ensure at least one agent (besides Codex) is:
- Not in `COUNCIL_EXCLUDE_AGENTS`
- Has required CLI installed or API key configured

### OpenRouter/Claude issues

Verify OpenRouter setup:
```bash
# Check API key is set
echo $OPENROUTER_API_KEY

# Test with curl
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

## Best Practices

1. **Use council for important decisions** - Not every question needs multiple perspectives
2. **Start with your thinking** - Pass initial analysis via `primary_agent_opinion` parameter
3. **Assign roles strategically** - Match roles to the type of review needed
4. **Enable critique mode for critical code** - More thorough than simple deliberation
5. **Exclude expensive agents** - Use `COUNCIL_EXCLUDE_AGENTS` to control costs
6. **Set appropriate timeouts** - Complex queries need more time

## Cost Management

- **Claude (OpenRouter)**: Paid per token
- **Gemini**: Uses your Google AI Studio account
- **OpenCode**: Uses OpenRouter/API tokens
- **Codex**: Uses your OpenAI subscription

Control costs by:
- Excluding agents: `COUNCIL_EXCLUDE_AGENTS="gemini,opencode"`
- Using council selectively for important decisions
- Shorter prompts and focused questions

## Advanced: Custom Configurations

### Project-Specific Configs

Create `.env` files per project:

```bash
# project/.env.owlex
export COUNCIL_EXCLUDE_AGENTS="codex,opencode"
export COUNCIL_DEFAULT_TEAM="security_audit"
export OWLEX_DEFAULT_TIMEOUT="600"
```

Source before running Codex:
```bash
source .env.owlex
codex exec --cd /path/to/project
```

### Multiple Owlex Instances

Run different configurations:

```toml
[mcp_servers.owlex-fast]
command = "owlex-server"
[mcp_servers.owlex-fast.env]
COUNCIL_EXCLUDE_AGENTS = "codex,gemini,opencode"  # Claude only
OWLEX_DEFAULT_TIMEOUT = "60"

[mcp_servers.owlex-thorough]
command = "owlex-server"  
[mcp_servers.owlex-thorough.env]
COUNCIL_EXCLUDE_AGENTS = "codex"  # All others
OWLEX_DEFAULT_TIMEOUT = "600"
```

Then specify which instance in Codex queries.

## Next Steps

1. Install Owlex: `uv tool install git+https://github.com/aolin480/owlex.git`
2. Configure Codex MCP servers (add snippet above to `~/.codex/config.toml`)
3. Test with: "Use council_ask to help me decide X"
4. Fine-tune `COUNCIL_EXCLUDE_AGENTS` based on your setup

## Support

- GitHub: https://github.com/aolin480/owlex
- Issues: https://github.com/aolin480/owlex/issues
