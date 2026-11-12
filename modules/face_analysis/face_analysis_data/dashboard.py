
from collections import deque

import matplotlib.pyplot as plt


class FaceDashboard:

    def __init__(self, max_points=150):
        self.max_points = max_points
        self.frames = deque(maxlen=max_points)
        self.smile = deque(maxlen=max_points)
        self.eye = deque(maxlen=max_points)
        self.change = deque(maxlen=max_points)

        plt.ion()

        self.fig, self.axes = plt.subplots(
            3, 1,
            figsize=(9, 7),
            sharex=True
        )

        self.fig.suptitle("Face Analysis Dashboard")

        self.axes[0].set_title("Smile")
        self.axes[0].set_ylabel("Score")

        self.axes[1].set_title("Eye openness")
        self.axes[1].set_ylabel("Ratio")

        self.axes[2].set_title("Personal change")
        self.axes[2].set_ylabel("Score")
        self.axes[2].set_xlabel("Frame")

        self.lines = [
            self.axes[0].plot([], [], label="Smile")[0],
            self.axes[1].plot([], [], label="Eye")[0],
            self.axes[2].plot([], [], label="Change")[0],
        ]

        for axis in self.axes:
            axis.grid(True)
            axis.legend(loc="upper right")

        self.fig.tight_layout()

    def update(self, metrics, comparison=None):
        if not metrics or not metrics.get("face_detected"):
            return

        frame = self.frames[-1] + 1 if self.frames else 0

        smile = float(metrics.get("smile_score", 0.0))

        left_eye = float(
            metrics.get("left_eye_open", 0.0)
        )

        right_eye = float(
            metrics.get("right_eye_open", 0.0)
        )

        eye = (left_eye + right_eye) / 2

        change = 0.0

        if comparison:
            change = float(
                comparison.get("change_score", 0.0)
            )

        self.frames.append(frame)
        self.smile.append(smile)
        self.eye.append(eye)
        self.change.append(change)

        x = list(self.frames)

        for line, values in zip(
            self.lines,
            [self.smile, self.eye, self.change]
        ):
            line.set_data(x, list(values))

        for axis in self.axes:
            axis.relim()
            axis.autoscale_view()

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

        plt.pause(0.001)

    def close(self):
        plt.close(self.fig)
