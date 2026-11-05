
"""担当C：アプリ別の音量予測"""

import math

from .app_detect import normalize


def features(context, target):
    """状況を機械学習に渡す特徴量へ変換する。"""
    target = normalize(target)

    result = {
        "target": target,
        "category": context[
            "categories"
        ].get(target, "other"),
        "period": context["period"],
        "weekday": context["weekday"],
        "hour_sin": math.sin(
            context["hour"] * math.pi / 12
        ),
        "hour_cos": math.cos(
            context["hour"] * math.pi / 12
        ),
        "device": str(
            context["output_device_id"]
        ),
        "active": context["active_app"],
        "scene": context["scene"],
    }

    for name in context["running_apps"]:
        result[f"running:{name}"] = 1

    return result


class VolumeLearner:
    def __init__(
        self,
        store,
        user="local",
        minimum=20,
        limit=80,
        max_increase=5,
    ):
        if (
            minimum < 2
            or not 0 <= limit <= 100
            or not 0 <= max_increase <= 100
        ):
            raise ValueError(
                "学習設定が不正です"
            )

        self.store = store
        self.user = str(user)

        self.minimum = minimum
        self.limit = limit
        self.max_increase = max_increase

        self.models = {}
        self.counts = {}

    def retrain(self):
        """DBの履歴を使ってモデルを更新する。"""
        from sklearn.ensemble import (
            RandomForestRegressor,
        )
        from sklearn.feature_extraction import (
            DictVectorizer,
        )
        from sklearn.pipeline import (
            make_pipeline,
        )

        groups = {}

        for context, target, volume in (
            self.store.samples(self.user)
        ):
            groups.setdefault(
                target,
                [],
            ).append(
                (
                    features(context, target),
                    volume,
                )
            )

        models = {}

        self.counts = {
            target: len(rows)
            for target, rows in groups.items()
        }

        for target, rows in groups.items():
            if len(rows) < self.minimum:
                continue

            model = make_pipeline(
                DictVectorizer(),
                RandomForestRegressor(
                    n_estimators=60,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=1,
                ),
            )

            model.fit(
                [
                    inputs
                    for inputs, volume in rows
                ],
                [
                    volume
                    for inputs, volume in rows
                ],
            )

            models[target] = model

        self.models = models

        return dict(self.counts)

    def predict(self, context, target):
        """1つのアプリについて推奨音量を返す。"""
        target = normalize(target)

        current = context[
            "volumes"
        ].get(target)

        if current is None:
            return None

        model = self.models.get(target)

        if model:
            raw_prediction = float(
                model.predict(
                    [
                        features(
                            context,
                            target,
                        )
                    ]
                )[0]
            )

            source = "model"

        else:
            raw_prediction = current
            source = "keep_current"

        suggested = round(
            max(
                0,
                min(
                    self.limit,
                    current + self.max_increase,
                    raw_prediction,
                ),
            ),
            1,
        )

        return {
            "target": target,
            "current": current,
            "suggested": suggested,
            "source": source,
            "samples": self.counts.get(
                target,
                0,
            ),
            "change": (
                abs(suggested - current) >= 2
            ),
        }

    def evaluate(self):
        """
        時間順で前半80%を学習、
        後半20%を評価に使う。

        比較対象は学習期間の平均音量。
        """
        from sklearn.ensemble import (
            RandomForestRegressor,
        )
        from sklearn.feature_extraction import (
            DictVectorizer,
        )
        from sklearn.pipeline import (
            make_pipeline,
        )

        groups = {}
        result = {}

        for context, target, volume in (
            self.store.samples(self.user)
        ):
            groups.setdefault(
                target,
                [],
            ).append(
                (
                    features(context, target),
                    volume,
                )
            )

        for target, rows in groups.items():
            split = int(
                len(rows) * 0.8
            )

            if (
                split < self.minimum
                or split == len(rows)
            ):
                result[target] = {
                    "status": "insufficient_data",
                    "samples": len(rows),
                }

                continue

            train = rows[:split]
            test = rows[split:]

            model = make_pipeline(
                DictVectorizer(),
                RandomForestRegressor(
                    n_estimators=60,
                    min_samples_leaf=2,
                    random_state=42,
                ),
            )

            model.fit(
                [inputs for inputs, _ in train],
                [volume for _, volume in train],
            )

            predictions = model.predict(
                [inputs for inputs, _ in test]
            )

            average = (
                sum(
                    volume
                    for _, volume in train
                )
                / len(train)
            )

            model_mae = (
                sum(
                    abs(prediction - volume)
                    for prediction, (_, volume)
                    in zip(predictions, test)
                )
                / len(test)
            )

            baseline_mae = (
                sum(
                    abs(average - volume)
                    for _, volume in test
                )
                / len(test)
            )

            result[target] = {
                "test_samples": len(test),
                "model_mae": model_mae,
                "baseline_mae": baseline_mae,
            }

        return result
