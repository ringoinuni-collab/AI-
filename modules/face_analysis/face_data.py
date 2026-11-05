
import json
from pathlib import Path
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "face_analysis_data"
DATA_FILE = DATA_DIR / "history.json"


def save_face_data(user_id, face_data):

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            history = []
    else:
        history = []

    record = {
        "user_id": user_id,
        "app_id": "VolumeAdjustmentSystem",
        "device_id": "local_pc",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        **face_data
    }

    history.append(record)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=4
        )
