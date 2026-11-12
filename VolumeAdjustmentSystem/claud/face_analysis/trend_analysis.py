
from collections import deque
from statistics import mean


class TrendAnalyzer:

    def __init__(self, window_size=150):
        self.history = deque(maxlen=window_size)

    def update(self, metrics):
        if not metrics or not metrics.get("face_detected"):
            return {
                "trend_ready": False,
                "smile_average": 0.0,
                "movement_average": 0.0,
                "change_average": 0.0,
            }

        sample = {
            "smile": float(metrics.get("smile_score", 0.0)),
            "movement": abs(float(metrics.get("face_move_speed", 0.0))),
            "change": float(metrics.get("change_score", 0.0)),
        }

        self.history.append(sample)

        if not self.history:
            return {"trend_ready": False}

        return {
            "trend_ready": len(self.history) >= 10,
            "sample_count": len(self.history),
            "smile_average": round(
                mean(item["smile"] for item in self.history), 4
            ),
            "movement_average": round(
                mean(item["movement"] for item in self.history), 4
            ),
            "change_average": round(
                mean(item["change"] for item in self.history), 2
            ),
        }

    def reset(self):
        self.history.clear()
