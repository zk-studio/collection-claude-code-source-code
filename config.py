"""Configuration management for nano claude."""
import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".nano_claude"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "input_history.txt"
SESSIONS_DIR = CONFIG_DIR / "sessions"

DEFAULTS = {
    "model": "claude-opus-4-6",
    "max_tokens": 8192,
    "permission_mode": "auto",   # auto | accept-all | manual
    "verbose": False,
    "thinking": False,
    "thinking_budget": 10000,
}

# Models available
MODELS = [
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
]

# Input token costs per million (approximate)
INPUT_COST = {
    "claude-opus-4-6":   15.0,
    "claude-sonnet-4-6":  3.0,
    "claude-haiku-4-5-20251001": 0.8,
    "claude-opus-4-5":   15.0,
    "claude-sonnet-4-5":  3.0,
    "claude-3-5-sonnet-20241022": 3.0,
    "claude-3-5-haiku-20241022":  0.8,
}
OUTPUT_COST = {
    "claude-opus-4-6":   75.0,
    "claude-sonnet-4-6": 15.0,
    "claude-haiku-4-5-20251001": 4.0,
    "claude-opus-4-5":   75.0,
    "claude-sonnet-4-5": 15.0,
    "claude-3-5-sonnet-20241022": 15.0,
    "claude-3-5-haiku-20241022":  4.0,
}


def load_config() -> dict:
    CONFIG_DIR.mkdir(exist_ok=True)
    SESSIONS_DIR.mkdir(exist_ok=True)
    cfg = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text()))
        except Exception:
            pass
    # Resolve API key: config file > env var
    cfg["api_key"] = (cfg.get("api_key") or
                      os.environ.get("ANTHROPIC_API_KEY") or "")
    return cfg


def save_config(cfg: dict):
    CONFIG_DIR.mkdir(exist_ok=True)
    data = {k: v for k, v in cfg.items() if k != "api_key"}
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def calc_cost(model: str, in_tokens: int, out_tokens: int) -> float:
    ic = INPUT_COST.get(model, 3.0)
    oc = OUTPUT_COST.get(model, 15.0)
    return (in_tokens * ic + out_tokens * oc) / 1_000_000
