# Nano Claude Code

A minimal Python implementation of Claude Code (~920 lines total), covering all core features.

## Features

| Feature | Implementation |
|---|---|
| Interactive REPL | Readline with history, tab completion |
| Agent loop | Streaming API + tool use loop |
| 8 Built-in tools | Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch |
| Permission system | auto / accept-all / manual modes |
| Slash commands | 14 commands (/help, /clear, /model, etc.) |
| System context | CLAUDE.md injection, git status, cwd |
| Session save/load | JSON sessions in ~/.nano_claude/sessions/ |
| Extended thinking | Toggle on/off via /thinking or --thinking |
| Cost tracking | Token usage + estimated USD cost |
| Rich output | Markdown rendering via rich library |
| Non-interactive mode | --print flag for scripting |

## Quick Start

```bash
# Install dependencies
pip install anthropic httpx rich

# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Start interactive REPL
python nano_claude.py

# Non-interactive (run and exit)
python nano_claude.py --print "explain quicksort in 3 sentences"

# With specific model
python nano_claude.py --model claude-sonnet-4-6

# Accept all permissions automatically
python nano_claude.py --accept-all

# Show thinking process
python nano_claude.py --thinking --verbose
```

## File Structure

```
nano_claude_code/
├── nano_claude.py   # Entry point: REPL + slash commands + rendering (~300 lines)
├── agent.py         # Core agent loop: API calls + tool dispatch (~180 lines)
├── tools.py         # 8 tool implementations + schemas (~280 lines)
├── context.py       # System prompt + CLAUDE.md + git info (~90 lines)
├── config.py        # Config load/save + cost calculation (~70 lines)
├── demo.py          # Demo script showing all features
└── requirements.txt
```

## Slash Commands

| Command | Description |
|---|---|
| `/help` | Show all commands |
| `/clear` | Clear conversation history |
| `/model [name]` | Show or set model |
| `/config` | Show config; `/config key=value` to set |
| `/save [file]` | Save session to file |
| `/load [file]` | Load session; `/load` lists saved sessions |
| `/history` | Print full conversation history |
| `/context` | Show token usage estimate |
| `/cost` | Show API cost for this session |
| `/verbose` | Toggle verbose mode (thinking + tokens) |
| `/thinking` | Toggle extended thinking mode |
| `/permissions [mode]` | Get/set permission mode (auto/accept-all/manual) |
| `/cwd [path]` | Show or change working directory |
| `/exit` or `/quit` | Exit |

## Permission Modes

- **`auto`** (default): Asks before Bash commands and file writes. Safe read/list commands (ls, cat, git status, etc.) are always allowed.
- **`accept-all`**: Never asks. Use with `--accept-all` flag or `/permissions accept-all`.
- **`manual`**: Asks before everything including reads.

During a session, when asked for permission you can type `a` to switch to accept-all for the rest of the session.

## Available Tools

### Read
```
Read a file with line numbers.
Inputs: file_path, limit (optional), offset (optional)
```

### Write
```
Create or overwrite a file.
Inputs: file_path, content
```

### Edit
```
Replace exact text in a file.
Inputs: file_path, old_string, new_string, replace_all (optional)
```

### Bash
```
Execute shell command (stateless, runs in cwd).
Inputs: command, timeout (default: 30s)
```

### Glob
```
Find files by pattern.
Inputs: pattern (e.g. **/*.py), path (optional)
```

### Grep
```
Search file contents with regex (uses ripgrep if available).
Inputs: pattern, path, glob, output_mode, case_insensitive, context
```

### WebFetch
```
Fetch a URL and extract text content.
Inputs: url, prompt (hint for extraction)
```

### WebSearch
```
Search the web via DuckDuckGo.
Inputs: query
```

## Configuration

Config is stored in `~/.nano_claude/config.json`:

```json
{
  "model": "claude-opus-4-6",
  "max_tokens": 8192,
  "permission_mode": "auto",
  "verbose": false,
  "thinking": false,
  "thinking_budget": 10000
}
```

Set via `/config key=value` in REPL, or edit the file directly.

## CLAUDE.md Support

Nano Claude automatically loads:
1. `~/.claude/CLAUDE.md` (global memory)
2. `CLAUDE.md` in current directory or any parent directory (project memory)

These are injected into the system prompt for context.

## Run the Demo

```bash
ANTHROPIC_API_KEY=sk-ant-... python demo.py
```

The demo runs 5 scenarios:
1. Simple Q&A (no tools)
2. File system exploration (Glob + Read)
3. Code writing + execution (Write + Bash)
4. Multi-turn conversation
5. Web search (WebSearch)
