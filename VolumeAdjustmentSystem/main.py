
from storage.json_storage import (
    save_volume_history,
    save_ai_suggestion,
    save_user_correction,
    get_ai_learning_data,
    clear_volume_history
)

from storage.csv_storage import export_ai_csv
from storage.backup_manager import create_backup


def main():

    # ① 音量変更履歴
    history_id = save_volume_history(
        user_id=1,
        old_volume=50,
        new_volume=80,
        device_id=1,
        target_app_id=1,
        active_app_ids=[1, 2, 3],
        change_source="user"
    )

    # ② AI提案
    suggestion_id = save_ai_suggestion(
        user_id=1,
        history_id=history_id,
        suggested_volume=70
    )

    # ③ ユーザー修正
    save_user_correction(
        suggestion_id=suggestion_id,
        user_id=1,
        original_volume=70,
        corrected_volume=80
    )

    # ④ AI学習用データ取得
    learning_data = get_ai_learning_data(1)

    print("AI学習データ:", learning_data)

    # ⑤ CSV出力
    csv_path = export_ai_csv(1)

    print("CSV保存先:", csv_path)

    # ⑥ バックアップ
    backup_path = create_backup()

    print("バックアップ:", backup_path)


if __name__ == "__main__":
    main()
