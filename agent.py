"""Core agent loop: calls Claude API, handles streaming + tool use."""
from __future__ import annotations

from typing import Callable, Optional, Generator
from dataclasses import dataclass, field

import anthropic

from tools import TOOL_SCHEMAS, execute_tool


@dataclass
class AgentState:
    """Mutable session state passed through the agent loop."""
    messages: list = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    turn_count: int = 0


# ── Event types yielded from run() ────────────────────────────────────────

@dataclass
class TextChunk:
    text: str

@dataclass
class ThinkingChunk:
    text: str

@dataclass
class ToolStart:
    name: str
    inputs: dict

@dataclass
class ToolEnd:
    name: str
    result: str
    permitted: bool = True

@dataclass
class TurnDone:
    input_tokens: int
    output_tokens: int

@dataclass
class PermissionRequest:
    """Yielded when permission is needed. Set .granted before resuming."""
    description: str
    granted: bool = False


# ── Agent loop ─────────────────────────────────────────────────────────────

def run(
    user_message: str,
    state: AgentState,
    config: dict,
    system_prompt: str,
) -> Generator:
    """
    Generator-based agent loop.
    Yields events: TextChunk, ThinkingChunk, ToolStart, ToolEnd,
                   PermissionRequest, TurnDone.
    The caller drives tool-permission prompts by setting event.granted.
    """
    client = anthropic.Anthropic(api_key=config["api_key"])

    # Append user message
    state.messages.append({"role": "user", "content": user_message})

    while True:
        state.turn_count += 1

        # ── Build API kwargs ─────────────────────────────────────────────
        kwargs: dict = {
            "model":      config["model"],
            "max_tokens": config["max_tokens"],
            "system":     system_prompt,
            "messages":   state.messages,
            "tools":      TOOL_SCHEMAS,
        }
        if config.get("thinking"):
            kwargs["thinking"] = {
                "type":         "enabled",
                "budget_tokens": config.get("thinking_budget", 10000),
            }

        # ── Stream response ──────────────────────────────────────────────
        in_tokens = out_tokens = 0
        tool_uses: list = []

        with client.messages.stream(**kwargs) as stream:
            for event in stream:
                etype = getattr(event, "type", None)

                if etype == "content_block_delta":
                    delta = event.delta
                    dtype = getattr(delta, "type", None)
                    if dtype == "text_delta":
                        yield TextChunk(delta.text)
                    elif dtype == "thinking_delta":
                        yield ThinkingChunk(delta.thinking)

            final = stream.get_final_message()
            in_tokens  = final.usage.input_tokens
            out_tokens = final.usage.output_tokens
            state.total_input_tokens  += in_tokens
            state.total_output_tokens += out_tokens

            for block in final.content:
                if block.type == "tool_use":
                    tool_uses.append(block)

        # Append assistant turn to history
        state.messages.append({
            "role":    "assistant",
            "content": final.content,
        })

        yield TurnDone(in_tokens, out_tokens)

        if final.stop_reason != "tool_use" or not tool_uses:
            break

        # ── Execute tools ────────────────────────────────────────────────
        tool_results = []
        for tu in tool_uses:
            yield ToolStart(tu.name, tu.input)

            # Permission gate
            perm_mode = config.get("permission_mode", "auto")
            permitted = True
            if perm_mode != "accept-all":
                from tools import _is_safe_bash
                needs_check = (
                    tu.name in ("Write", "Edit") or
                    (tu.name == "Bash" and not _is_safe_bash(tu.input.get("command", ""))) or
                    perm_mode == "manual"
                )
                if needs_check:
                    desc = _permission_desc(tu.name, tu.input)
                    req = PermissionRequest(description=desc)
                    yield req
                    permitted = req.granted

            if not permitted:
                result = "Denied: user rejected this operation"
            else:
                result = execute_tool(
                    tu.name, tu.input,
                    permission_mode="accept-all",  # already checked above
                )

            yield ToolEnd(tu.name, result, permitted)
            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": tu.id,
                "content":     result,
            })

        state.messages.append({"role": "user", "content": tool_results})


def _permission_desc(name: str, inputs: dict) -> str:
    if name == "Bash":
        return f"Run: {inputs.get('command', '')}"
    if name == "Write":
        return f"Write to: {inputs.get('file_path', '')}"
    if name == "Edit":
        return f"Edit: {inputs.get('file_path', '')}"
    return f"{name}: {list(inputs.values())[:1]}"
