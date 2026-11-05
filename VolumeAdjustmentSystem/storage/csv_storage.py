import csv

from pathlib import Path

from storage.json_storage import (
    get_ai_learning_data
)

BASE_DIR = Path(__file__).resolve().parent.parent

EXPORT_DIR = BASE_DIR / "local_data" / "export"


def export_ai_csv(user_id):

    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    csv_path = EXPORT_DIR / "ai_learning_data.csv"

    records = get_ai_learning_data(user_id)

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        fieldnames = [
            "日時",
            "対象アプリ",
            "変更前音量",
            "変更後音量",
            "使用機器",
            "同時利用アプリ",
            "AI提案音量",
            "AI結果",
            "修正前音量",
            "修正後音量"
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for record in records:

            history = record["history"]

            device = record["device"]

            apps = [
                app["app_name"]
                for app in get_app_names(
                    record["active_apps"]
                )
            ]

            suggestions = record["suggestions"]

            corrections = record["corrections"]

            if not suggestions:
                suggestions = [None]

            for suggestion in suggestions:

                related_corrections = [
                    c for c in corrections
                    if suggestion is not None
                    and c["suggestion_id"] == suggestion["suggestion_id"]
                ]

                if not related_corrections:
                    related_corrections = [None]

                for correction in related_corrections:

                    writer.writerow({
                        "日時": history["changed_at"],
                        "対象アプリ": record["target_app"],
                        "変更前音量": history["old_volume"],
                        "変更後音量": history["new_volume"],
                        "使用機器": device["device_name"] if device else "",
                        "同時利用アプリ": ", ".join(apps),
                        "AI提案音量": suggestion["suggested_volume"] if suggestion else "",
                        "AI結果": suggestion["result"] if suggestion else "未提案",
                        "修正前音量": correction["original_volume"] if correction else "",
                        "修正後音量": correction["corrected_volume"] if correction else ""
                    })

    return csv_path


def get_app_names(app_ids):

    from storage.json_storage import load_data

    data = load_data()

    return [
        app for app in data["applications"]
        if app["app_id"] in app_ids
    ]