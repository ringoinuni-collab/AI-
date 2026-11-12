
import time


class BlinkAnalyzer:

    def __init__(self, threshold=0.65):
        self.threshold = threshold

        self.left_closed = False
        self.right_closed = False

        self.left_start = None
        self.right_start = None

        self.left_count = 0
        self.right_count = 0

        self.last_blink_time = None

    def update(self, left_score, right_score):

        now = time.monotonic()

        result = {}

        # 左目
        if left_score >= self.threshold:

            if not self.left_closed:
                self.left_closed = True
                self.left_start = now

        elif self.left_closed:

            duration = now - self.left_start

            self.left_closed = False
            self.left_count += 1

            self.last_blink_time = now

            result["left_blink_duration"] = round(
                duration, 3
            )

        # 右目
        if right_score >= self.threshold:

            if not self.right_closed:
                self.right_closed = True
                self.right_start = now

        elif self.right_closed:

            duration = now - self.right_start

            self.right_closed = False
            self.right_count += 1

            self.last_blink_time = now

            result["right_blink_duration"] = round(
                duration, 3
            )

        result["left_blink_count"] = self.left_count
        result["right_blink_count"] = self.right_count

        result["both_eyes_closed"] = (
            self.left_closed and self.right_closed
        )

        return result
