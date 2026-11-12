
import json
import os

from pathlib import Path
from datetime import datetime, timezone


# =================================
# 保存先
# =================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "face_analysis_data"

DATA_FILE = DATA_DIR / "history.json"

# 履歴の最大保存件数
MAX_HISTORY_RECORDS = 20000


# =================================
# JSON読み込み
# =================================

def load_face_history():

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            history = json.load(f)

        if isinstance(history, list):
            return history

        raise ValueError("履歴JSONの形式が不正です")

    except json.JSONDecodeError as e:
        raise ValueError(
            f"履歴JSONが破損しています: {DATA_FILE}"
        ) from e


# =================================
# JSON安全保存
# =================================

def write_face_history(history):

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    temp_file = DATA_FILE.with_suffix(".tmp")

    try:
        with temp_file.open("w", encoding="utf-8") as f:

            json.dump(
                history,
                f,
                ensure_ascii=False,
                indent=4,
                allow_nan=False
            )

            f.flush()
            os.fsync(f.fileno())

        # 書き込み完了後に置き換える
        os.replace(temp_file, DATA_FILE)

    finally:
        if temp_file.exists():
            temp_file.unlink()


# =================================
# 顔解析データ保存
# =================================

def save_face_data(user_id, face_data):

    if not isinstance(face_data, dict):
        raise TypeError("face_dataは辞書形式で指定してください")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    history = load_face_history()

    # 保存レコード
    record = {
        **face_data,
        "user_id": str(user_id),
        "app_id": "VolumeAdjustmentSystem",
        "device_id": "local_pc",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat()
    }

    # 履歴追加
    history.append(record)

    # 古い履歴を整理
    if len(history) > MAX_HISTORY_RECORDS:
        history = history[-MAX_HISTORY_RECORDS:]

    # JSON保存
    write_face_history(history)

    return True


# =================================
# 履歴取得
# =================================

def get_face_history(user_id=None, limit=100):

    history = load_face_history()

    if user_id is not None:

        history = [
            item
            for item in history
            if item.get("user_id") == str(user_id)
        ]

    if limit is not None:
        history = history[-max(0, int(limit)):]

    return history


# =================================
# 履歴件数取得
# =================================

def get_history_count(user_id=None):

    history = get_face_history(
        user_id=user_id,
        limit=None
    )

    return len(history)
