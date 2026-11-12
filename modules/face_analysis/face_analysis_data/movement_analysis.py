
import time


class FaceMovementTracker:

    def __init__(self):
        self.previous = None
        self.previous_time = None

    def update(self, metrics):

        now = time.monotonic()

        if not metrics:
            self.previous = None
            self.previous_time = None

            return {
                "face_move_x": 0.0,
                "face_move_y": 0.0,
                "face_move_speed": 0.0,
                "yaw_change": 0.0,
                "pitch_change": 0.0,
                "roll_change": 0.0
            }

        current = {
            "x": metrics["face_x"],
            "y": metrics["face_y"],
            "yaw": metrics["face_yaw"],
            "pitch": metrics["face_pitch"],
            "roll": metrics["face_roll"]
        }

        if self.previous is None:
            self.previous = current
            self.previous_time = now

            return {
                "face_move_x": 0.0,
                "face_move_y": 0.0,
                "face_move_speed": 0.0,
                "yaw_change": 0.0,
                "pitch_change": 0.0,
                "roll_change": 0.0
            }

        dt = max(now - self.previous_time, 0.001)

        dx = current["x"] - self.previous["x"]
        dy = current["y"] - self.previous["y"]

        speed = ((dx ** 2 + dy ** 2) ** 0.5) / dt

        result = {
            "face_move_x": round(dx, 5),
            "face_move_y": round(dy, 5),
            "face_move_speed": round(speed, 5),
            "yaw_change": round(
                current["yaw"] - self.previous["yaw"], 2
            ),
            "pitch_change": round(
                current["pitch"] - self.previous["pitch"], 2
            ),
            "roll_change": round(
                current["roll"] - self.previous["roll"], 2
            )
        }

        self.previous = current
        self.previous_time = now

        return result
