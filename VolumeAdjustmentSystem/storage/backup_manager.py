import zipfile

from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "local_data"

BACKUP_DIR = DATA_DIR / "backup"


def create_backup():

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        BACKUP_DIR /
        f"backup_{timestamp}.zip"
    )

    with zipfile.ZipFile(
        backup_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:

        data_path = DATA_DIR / "data.json"

        if data_path.exists():

            zip_file.write(
                data_path,
                "data.json"
            )

        export_path = DATA_DIR / "export"

        if export_path.exists():

            for file in export_path.glob("*.csv"):

                zip_file.write(
                    file,
                    f"export/{file.name}"
                )

    return backup_path