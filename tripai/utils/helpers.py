import json
import os
from datetime import datetime
from typing import Dict, Any

def save_to_json(data: Dict[str, Any], filename: str, output_dir: str = "./outputs") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{filename}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath

def load_from_json(filepath: str) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_filename(prefix: str = "trip") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"

def format_currency(amount: float) -> str:
    return f"¥{amount:,.2f}"

def format_duration(days: int) -> str:
    if days == 1:
        return "1天"
    return f"{days}天{days-1}晚"