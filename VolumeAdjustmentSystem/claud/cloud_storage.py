import shutil
import os

from pathlib import Path


def upload_backup(backup_path):

    cloud_dir = os.getenv("CLOUD_SYNC_DIR")

    if not cloud_dir:
        raise RuntimeError(
            "クラウド保存先が設定されていません"
        )

    cloud_path = Path(cloud_dir)

    if not cloud_path.is_dir():
        raise FileNotFoundError(
            "クラウド同期フォルダが見つかりません"
        )

    backup_path = Path(backup_path)

    if not backup_path.is_file():
        raise FileNotFoundError(
            "バックアップファイルがありません"
        )

    destination = cloud_path / backup_path.name

    shutil.copy2(
        backup_path,
        destination
    )

    return destination