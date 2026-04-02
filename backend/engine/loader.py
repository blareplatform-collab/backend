"""
BLARE Strategy Loader
Reads all .txt strategy files from /strategies/ directory.
Parses them into structured dicts the pattern engine can use.
Adding a new strategy = drop a .txt file + restart. No code changes.
"""
from pathlib import Path
from typing import Dict

STRATEGIES_DIR = Path(__file__).parent.parent.parent / "strategies"

_loaded_strategies: Dict[str, dict] = {}


def parse_strategy_file(filepath: Path) -> dict:
    """Parse a BLARE strategy .txt file into a structured dict."""
    strategy = {"id": filepath.stem, "filepath": str(filepath), "raw": {}}
    current_key = None
    current_value = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("#") or not line.strip():
                continue
            if ":" in line and not line.startswith(" "):
                if current_key:
                    strategy["raw"][current_key] = "\n".join(current_value).strip()
                parts = line.split(":", 1)
                current_key = parts[0].strip()
                current_value = [parts[1].strip()] if len(parts) > 1 else []
            else:
                if current_key:
                    current_value.append(line.strip())

    if current_key:
        strategy["raw"][current_key] = "\n".join(current_value).strip()

    raw = strategy["raw"]
    strategy.update({
        "name": raw.get("STRATEGY_NAME", strategy["id"]),
        "market": [m.strip() for m in raw.get("MARKET", "all").split(",")],
        "direction": raw.get("DIRECTION", "both"),
        "htf": raw.get("HTF", "1d"),
        "mtf": raw.get("MTF", "4h"),
        "ltf": raw.get("LTF", "15m"),
        "concept": raw.get("CONCEPT", ""),
        "conditions": [v for k, v in raw.items() if k.startswith("CONDITION_") and v],
        "entry_trigger": raw.get("ENTRY_TRIGGER", ""),
        "stop_placement": raw.get("STOP_PLACEMENT", ""),
        "invalidations": [v for k, v in raw.items() if k.startswith("INVALIDATION_") and v],
        "detect_steps": [v for k, v in raw.items() if k.startswith("DETECT_STEP_") and v],
        "min_rr": float(raw.get("MINIMUM_RR", "2.0")),
    })
    return strategy


def load_all_strategies() -> Dict[str, dict]:
    """Load all strategy .txt files from the strategies directory."""
    global _loaded_strategies
    _loaded_strategies = {}

    if not STRATEGIES_DIR.exists():
        print(f"[Loader] Strategies directory not found: {STRATEGIES_DIR}")
        return {}

    files = [f for f in STRATEGIES_DIR.glob("*.txt") if not f.name.startswith("_")]

    for filepath in files:
        try:
            strategy = parse_strategy_file(filepath)
            _loaded_strategies[strategy["id"]] = strategy
            print(f"[Loader] Loaded strategy: {strategy['id']}")
        except Exception as e:
            print(f"[Loader] Error loading {filepath.name}: {e}")

    print(f"[Loader] Total strategies loaded: {len(_loaded_strategies)}")
    return _loaded_strategies


def get_strategies() -> Dict[str, dict]:
    return _loaded_strategies


def get_strategy(strategy_id: str) -> dict:
    return _loaded_strategies.get(strategy_id)
