"""Config loading/saving. config.json is gitignored (contains the API key)."""
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
EXAMPLE_PATH = ROOT / "config.example.json"

DEFAULTS = {
    "gemini_api_key": "",
    "model": "gemini-3.5-flash",
    "thinking_budget": 0,
    "hotkey": "F9",
    "interact_key": "alt",
    "hold_threshold_ms": 350,
    "monitor": 0,
    "max_capture_width": 1366,
    "jpeg_quality": 78,
    "result_seconds": 25,
    "animations": True,
    "animation_fps": 30,
    "platform": "pc",
    "position": None,
}


def load() -> dict:
    if not CONFIG_PATH.exists() and EXAMPLE_PATH.exists():
        shutil.copyfile(EXAMPLE_PATH, CONFIG_PATH)
    data = {}
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
        except Exception:
            data = {}
    cfg = {**DEFAULTS, **data}
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_key and not cfg.get("gemini_api_key"):
        cfg["gemini_api_key"] = env_key
    return cfg


def save(cfg: dict) -> None:
    out = dict(cfg)
    CONFIG_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
