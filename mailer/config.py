import json
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    config.setdefault("sender_name", "")
    config.setdefault("delay_seconds", 4)
    config.setdefault("default_csv", "University_of_Delaware_Contacts.csv")
    config.setdefault("default_template", "templates/default_template.txt")
    config.setdefault("smtp_host", "smtp.gmail.com")
    config.setdefault("smtp_port", 587)
    return config
