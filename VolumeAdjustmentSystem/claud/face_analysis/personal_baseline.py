
import json
from pathlib import Path
from statistics import median

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "face_analysis_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class PersonalBaseline:
    """
    個人内基準を作成・保存・比較するクラス。
    顔画像そのものではなく数値特徴量を保存する。
    """

    def __init__(self, user_id="local_user"):
        self.user_id = str(user_id)
        self.file_path = DATA_DIR / f"baseline_{self.user_id}.json"

        self.samples = []
        self.baseline = {}
        self.target_samples = 1800

        self.load()

    def add_sample(self, metrics):
        """通常状態の特徴量を1件追加する。"""

        if not metrics or not metrics.get("face_detected"):
            return False

        features = self._extract_features(metrics)

        if not features:
            return False

        self.samples.append(features)

        if len(self.samples) >= self.target_samples:
            self.build_baseline()
            return True

        return False

    def _extract_features(self, metrics):
        """基準作成に使う数値だけを取り出す。"""

        keys = [
            "left_eye_open",
            "right_eye_open",
            "mouth_open_ratio",
            "mouth_width_ratio",
            "smile_score",
            "face_yaw",
            "face_pitch",
            "face_roll",
            "smile_asymmetry",
            "brow_asymmetry",
        ]

        result = {}

        for key in keys:
            value = metrics.get(key)

            if isinstance(value, (int, float)):
                result[key] = float(value)

        return result

    def build_baseline(self):
        """中央値とMAD（中央値絶対偏差）を計算する。"""

        if len(self.samples) < self.target_samples:
            return False

        keys = set()

        for sample in self.samples:
            keys.update(sample.keys())

        result = {}

        for key in keys:
            values = [
                sample[key]
                for sample in self.samples
                if key in sample
            ]

            if not values:
                continue

            center = median(values)

            deviations = [
                abs(value - center)
                for value in values
            ]

            mad = median(deviations)

            result[key] = {
                "median": center,
                "mad": mad,
                "sample_count": len(values),
            }

        self.baseline = result
        self.save()

        return True

    def compare(self, metrics):
        """通常状態からの変化を特徴量ごとに計算する。"""

        if not self.baseline:
            return {
                "baseline_ready": False,
                "changes": {},
                "change_score": 0.0,
            }

        features = self._extract_features(metrics)
        changes = {}

        for key, value in features.items():
            reference = self.baseline.get(key)

            if not reference:
                continue

            center = reference["median"]
            mad = reference["mad"]

            # MADがほぼ0の場合の過大なスコアを防止
            scale = max(mad * 1.4826, 0.01)

            z_score = (value - center) / scale

            changes[key] = {
                "current": round(value, 4),
                "baseline": round(center, 4),
                "z_score": round(z_score, 3),
                "difference": round(value - center, 4),
            }

        scores = [
            min(abs(item["z_score"]), 5.0)
            for item in changes.values()
        ]

        average = sum(scores) / len(scores) if scores else 0.0

        change_score = min(100.0, average / 5.0 * 100.0)

        return {
            "baseline_ready": True,
            "changes": changes,
            "change_score": round(change_score, 2),
        }

    def save(self):
        """基準データをJSON保存する。"""

        data = {
            "user_id": self.user_id,
            "sample_count": len(self.samples),
            "baseline": self.baseline,
        }

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def load(self):
        """保存済み基準データを読み込む。"""

        if not self.file_path.exists():
            return False

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            self.baseline = data.get("baseline", {})
            return True

        except (OSError, json.JSONDecodeError):
            self.baseline = {}
            return False

    def reset(self):
        """基準をリセットして再測定できるようにする。"""

        self.samples.clear()
        self.baseline = {}

        if self.file_path.exists():
            self.file_path.unlink()
