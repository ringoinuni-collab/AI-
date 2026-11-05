
"""担当C：既存アプリとの接続窓口"""

from threading import RLock

from .app_detect import (
    SituationDetector,
    normalize,
)
from .history_store import HistoryStore
from .ai_learning import VolumeLearner


class AIService:
    """
    利用状況判定・予測・履歴保存をまとめる。

    実際の音量変更は担当Aの処理で行う。
    """

    def __init__(
        self,
        db_path=None,
        user="local",
        overrides=None,
    ):
        self.user = str(user)

        self.store = HistoryStore(
            db_path
        )

        self.detector = SituationDetector(
            overrides
        )

        self.learner = VolumeLearner(
            self.store,
            self.user,
        )

        self.lock = RLock()

        self.learner.retrain()

    def inspect(self, raw):
        """取得結果を整理して利用状況を返す。"""
        with self.lock:
            return self.detector.snapshot(
                raw
            )

    def propose(self, context):
        """変更が必要なアプリの提案を返す。"""
        with self.lock:
            proposals = []

            for target in context["volumes"]:
                item = self.learner.predict(
                    context,
                    target,
                )

                if (
                    item
                    and item["change"]
                ):
                    item["id"] = (
                        self.store.suggest(
                            self.user,
                            context,
                            target,
                            item["suggested"],
                        )
                    )

                    proposals.append(item)

            return proposals

    def feedback(
        self,
        suggestion_id,
        result,
        actual=None,
    ):
        """
        提案への回答を保存する。

        承認・修正の場合は、実際に適用して
        読み戻した音量をactualへ渡す。
        """
        with self.lock:
            self.store.resolve(
                self.user,
                suggestion_id,
                result,
                actual,
            )

            self.learner.retrain()

    def record_manual(
        self,
        context,
        target,
        actual,
    ):
        """通常の手動変更を学習へ反映する。"""
        with self.lock:
            target = normalize(target)

            if target not in context["volumes"]:
                raise ValueError(
                    "取得した状況に"
                    "対象アプリがありません"
                )

            self.store.record(
                self.user,
                context,
                target,
                actual,
            )

            self.learner.retrain()
