
import json
import os
import threading

from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "local_data"
DATA_PATH = DATA_DIR / "data.json"

LOCK = threading.RLock()


# ==============================
# 初期データ
# ==============================

def create_default_data():

    return {
        "users": [],
        "user_settings": [],
        "applications": [],
        "audio_devices": [],
        "volume_history": [],
        "usage_context": [],
        "ai_suggestions": [],
        "user_corrections": []
    }


# ==============================
# JSON読み込み
# ==============================

def load_data():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with LOCK:

        if not DATA_PATH.exists():

            data = create_default_data()

            save_data(data)

            return data

        with open(
            DATA_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        defaults = create_default_data()

        for key, value in defaults.items():
            data.setdefault(key, value)

        return data


# ==============================
# JSON保存
# ==============================

def save_data(data):

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    temp_path = DATA_PATH.with_suffix(".tmp")

    with LOCK:

        try:

            with open(
                temp_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

                f.flush()
                os.fsync(f.fileno())

            os.replace(
                temp_path,
                DATA_PATH
            )

        finally:

            if temp_path.exists():
                temp_path.unlink()


# ==============================
# ID自動発行
# ==============================

def get_next_id(data, table_name, id_name):

    records = data[table_name]

    return max(
        (item[id_name] for item in records),
        default=0
    ) + 1


# ==============================
# 音量履歴保存
# ==============================

def save_volume_history(
    user_id,
    old_volume,
    new_volume,
    device_id=None,
    target_app_id=None,
    active_app_ids=None,
    change_source="user"
):

    data = load_data()

    history_id = get_next_id(
        data,
        "volume_history",
        "history_id"
    )

    record = {
        "history_id": history_id,
        "user_id": user_id,
        "device_id": device_id,
        "target_app_id": target_app_id,
        "changed_at": datetime.now().isoformat(),
        "old_volume": old_volume,
        "new_volume": new_volume,
        "change_source": change_source
    }

    data["volume_history"].append(record)

    # 同時利用アプリを保存
    for app_id in set(active_app_ids or []):

        context_id = get_next_id(
            data,
            "usage_context",
            "context_id"
        )

        data["usage_context"].append({
            "context_id": context_id,
            "history_id": history_id,
            "app_id": app_id
        })

    save_data(data)

    return history_id


# ==============================
# AI提案保存
# ==============================

def save_ai_suggestion(
    user_id,
    history_id,
    suggested_volume
):

    data = load_data()

    suggestion_id = get_next_id(
        data,
        "ai_suggestions",
        "suggestion_id"
    )

    record = {
        "suggestion_id": suggestion_id,
        "user_id": user_id,
        "history_id": history_id,
        "suggested_volume": suggested_volume,
        "suggested_at": datetime.now().isoformat(),
        "result": "pending"
    }

    data["ai_suggestions"].append(record)

    save_data(data)

    return suggestion_id

# ==============================
# ユーザーによる音量修正を保存
# ==============================

def save_user_correction(
    suggestion_id,
    user_id,
    original_volume,
    corrected_volume
):

    data = load_data()

    # AI提案が存在するか確認
    suggestion = next(
        (
            s for s in data["ai_suggestions"]
            if (
                s["suggestion_id"] == suggestion_id
                and s["user_id"] == user_id
            )
        ),
        None
    )

    if suggestion is None:
        raise ValueError("指定されたAI提案が見つかりません。")

    # 修正履歴IDを発行
    correction_id = get_next_id(
        data,
        "user_corrections",
        "correction_id"
    )

    record = {
        "correction_id": correction_id,
        "suggestion_id": suggestion_id,
        "user_id": user_id,
        "original_volume": original_volume,
        "corrected_volume": corrected_volume,
        "corrected_at": datetime.now().isoformat()
    }

    data["user_corrections"].append(record)

    # AI提案の結果を更新
    suggestion["result"] = "modified"

    save_data(data)

    return correction_id


# ==============================
# AI学習用データ取得
# ==============================

def get_ai_learning_data(user_id):

    data = load_data()

    histories = [
        h for h in data["volume_history"]
        if h["user_id"] == user_id
    ]

    results = []

    for history in histories:

        active_apps = [
            context["app_id"]
            for context in data["usage_context"]
            if context["history_id"] == history["history_id"]
        ]

        suggestions = [
            s for s in data["ai_suggestions"]
            if s["history_id"] == history["history_id"]
        ]

        corrections = []

        for suggestion in suggestions:

            for correction in data["user_corrections"]:

                if (
                    correction["suggestion_id"]
                    == suggestion["suggestion_id"]
                ):
                    corrections.append(correction)

        target_app = next(
            (
                app["app_name"]
                for app in data["applications"]
                if app["app_id"] == history.get("target_app_id")
            ),
            None
        )

        device = next(
            (
                d for d in data["audio_devices"]
                if d["device_id"] == history.get("device_id")
            ),
            None
        )

        results.append({
            "history": history,
            "target_app": target_app,
            "active_apps": active_apps,
            "device": device,
            "suggestions": suggestions,
            "corrections": corrections
        })

    return results


# ==============================
# 音量履歴削除
# ==============================

def clear_volume_history(user_id):

    data = load_data()

    history_ids = {
        h["history_id"]
        for h in data["volume_history"]
        if h["user_id"] == user_id
    }

    suggestion_ids = {
        s["suggestion_id"]
        for s in data["ai_suggestions"]
        if s["user_id"] == user_id
    }

    # 音量履歴を削除
    data["volume_history"] = [
        h for h in data["volume_history"]
        if h["user_id"] != user_id
    ]

    # 利用状況を削除
    data["usage_context"] = [
        c for c in data["usage_context"]
        if c["history_id"] not in history_ids
    ]

    # AI提案を削除
    data["ai_suggestions"] = [
        s for s in data["ai_suggestions"]
        if s["suggestion_id"] not in suggestion_ids
    ]

    # ユーザー修正履歴を削除
    data["user_corrections"] = [
        c for c in data["user_corrections"]
        if c["suggestion_id"] not in suggestion_ids
    ]

    save_data(data)
