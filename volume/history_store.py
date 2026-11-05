
"""担当C：学習履歴・提案履歴の保存"""

import json
import os
import sqlite3

from contextlib import contextmanager
from pathlib import Path


def default_db():
    """ユーザーごとの保存先を取得する。"""
    root = (
        Path(
            os.environ.get(
                "LOCALAPPDATA",
                Path.home(),
            )
        )
        / "VolumeAdjust"
        / "data"
    )

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    return root / "learning.sqlite3"


class HistoryStore:
    def __init__(self, path=None):
        self.path = str(
            path or default_db()
        )

        with self.connect() as database:
            database.executescript(
                """
                CREATE TABLE IF NOT EXISTS c_samples (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    context TEXT NOT NULL,
                    target TEXT NOT NULL,
                    volume REAL NOT NULL
                        CHECK (
                            volume BETWEEN 0 AND 100
                        ),
                    source TEXT NOT NULL,
                    created_at TEXT
                        DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS c_suggestions (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    context TEXT NOT NULL,
                    target TEXT NOT NULL,
                    volume REAL NOT NULL,
                    result TEXT DEFAULT 'pending',
                    actual REAL,
                    created_at TEXT
                        DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    @contextmanager
    def connect(self):
        database = sqlite3.connect(
            self.path,
            timeout=10,
        )

        try:
            with database:
                yield database

        finally:
            database.close()

    def samples(self, user):
        """ユーザーの学習データを取得する。"""
        with self.connect() as database:
            rows = database.execute(
                """
                SELECT
                    context,
                    target,
                    volume
                FROM c_samples
                WHERE user_id = ?
                ORDER BY id
                """,
                (str(user),),
            )

            return [
                (
                    json.loads(context),
                    target,
                    volume,
                )
                for context, target, volume in rows
            ]

    def record(
        self,
        user,
        context,
        target,
        volume,
    ):
        """通常の手動変更を学習用に保存する。"""
        volume = float(volume)

        if not 0 <= volume <= 100:
            raise ValueError(
                "音量は0〜100"
            )

        with self.connect() as database:
            database.execute(
                """
                INSERT INTO c_samples (
                    user_id,
                    context,
                    target,
                    volume,
                    source
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(user),
                    json.dumps(context),
                    target,
                    volume,
                    "manual",
                ),
            )

    def suggest(
        self,
        user,
        context,
        target,
        volume,
    ):
        """AIの提案を保存してIDを返す。"""
        with self.connect() as database:
            cursor = database.execute(
                """
                INSERT INTO c_suggestions (
                    user_id,
                    context,
                    target,
                    volume
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(user),
                    json.dumps(context),
                    target,
                    volume,
                ),
            )

            return cursor.lastrowid

    def resolve(
        self,
        user,
        suggestion_id,
        result,
        actual=None,
    ):
        """
        提案への回答を保存する。

        accepted:
            提案どおり適用できた。

        modified:
            ユーザーが違う音量へ変更した。

        rejected:
            提案を拒否した。
        """
        if result not in (
            "accepted",
            "rejected",
            "modified",
        ):
            raise ValueError(
                "提案の結果が不正です"
            )

        with self.connect() as database:
            database.execute(
                "BEGIN IMMEDIATE"
            )

            row = database.execute(
                """
                SELECT
                    context,
                    target,
                    volume,
                    result
                FROM c_suggestions
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    suggestion_id,
                    str(user),
                ),
            ).fetchone()

            if (
                not row
                or row[3] != "pending"
            ):
                raise ValueError(
                    "未処理の提案がありません"
                )

            if result != "rejected":
                if actual is None:
                    raise ValueError(
                        "適用が成功した実際の音量を"
                        "渡してください"
                    )

                actual = float(actual)

                if not 0 <= actual <= 100:
                    raise ValueError(
                        "音量は0〜100"
                    )

                if (
                    result == "accepted"
                    and abs(actual - row[2]) > 0.01
                ):
                    raise ValueError(
                        "提案と異なる音量は"
                        "modifiedで保存してください"
                    )

                database.execute(
                    """
                    INSERT INTO c_samples (
                        user_id,
                        context,
                        target,
                        volume,
                        source
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(user),
                        row[0],
                        row[1],
                        actual,
                        result,
                    ),
                )

            database.execute(
                """
                UPDATE c_suggestions
                SET
                    result = ?,
                    actual = ?
                WHERE id = ?
                """,
                (
                    result,
                    actual,
                    suggestion_id,
                ),
            )
