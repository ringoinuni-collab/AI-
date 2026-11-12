
import math


def distance(a, b):
    return math.sqrt(
        (a.x - b.x) ** 2 +
        (a.y - b.y) ** 2
    )


def eye_aspect_ratio(points, indexes):
    p = [points[i] for i in indexes]

    horizontal = distance(p[0], p[3])

    if horizontal == 0:
        return 0.0

    vertical1 = distance(p[1], p[5])
    vertical2 = distance(p[2], p[4])

    return (vertical1 + vertical2) / (2 * horizontal)


def analyze_eyes(landmarks):

    result = {
        "left_eye_open": 0.0,
        "right_eye_open": 0.0,
        "left_gaze_x": None,
        "left_gaze_y": None,
        "right_gaze_x": None,
        "right_gaze_y": None
    }

    if len(landmarks) < 468:
        return result

    # MediaPipe Face Meshの目のランドマーク
    left_indexes = [362, 385, 387, 263, 373, 380]
    right_indexes = [33, 160, 158, 133, 153, 144]

    result["left_eye_open"] = round(
        eye_aspect_ratio(landmarks, left_indexes), 4
    )

    result["right_eye_open"] = round(
        eye_aspect_ratio(landmarks, right_indexes), 4
    )

    # 虹彩ランドマークがある場合だけ視線を推定
    if len(landmarks) >= 478:

        # 左目：虹彩468～472
        left_iris = landmarks[468:473]

        # 右目：虹彩473～477
        right_iris = landmarks[473:478]

        left_center = (
            sum(p.x for p in left_iris) / len(left_iris),
            sum(p.y for p in left_iris) / len(left_iris)
        )

        right_center = (
            sum(p.x for p in right_iris) / len(right_iris),
            sum(p.y for p in right_iris) / len(right_iris)
        )

        def gaze(center, points, corner_a, corner_b, upper, lower):
            width = abs(points[corner_b].x - points[corner_a].x)
            height = abs(points[lower].y - points[upper].y)

            if width == 0 or height == 0:
                return None, None

            center_x = (
                points[corner_a].x + points[corner_b].x
            ) / 2

            center_y = (
                points[upper].y + points[lower].y
            ) / 2

            return (
                round((center[0] - center_x) / width, 4),
                round((center[1] - center_y) / height, 4)
            )

        result["left_gaze_x"], result["left_gaze_y"] = gaze(
            left_center, landmarks, 362, 263, 386, 374
        )

        result["right_gaze_x"], result["right_gaze_y"] = gaze(
            right_center, landmarks, 33, 133, 159, 145
        )

    return result
