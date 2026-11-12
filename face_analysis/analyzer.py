
import cv2
import numpy as np

from .eye_analysis import analyze_eyes
from .mouth_analysis import analyze_mouth
from .expression_analysis import analyze_expression
from .movement_analysis import FaceMovementTracker


movement_tracker = FaceMovementTracker()


def get_blendshape_dict(result):
    """MediaPipeのBlendshapeを辞書に変換する。"""

    if not result.face_blendshapes:
        return {}

    data = result.face_blendshapes[0]

    if hasattr(data, "categories"):
        categories = data.categories
    else:
        categories = data

    return {
        item.category_name: float(item.score)
        for item in categories
    }


def get_face_angle(result):
    """顔の向き・傾きを取得する。"""

    if not result.facial_transformation_matrixes:
        return 0.0, 0.0, 0.0

    try:
        matrix = np.asarray(
            result.facial_transformation_matrixes[0],
            dtype=np.float64
        )

        if matrix.size != 16:
            return 0.0, 0.0, 0.0

        matrix = matrix.reshape(4, 4)

        rotation = matrix[:3, :3]

        if not np.isfinite(rotation).all():
            return 0.0, 0.0, 0.0

        angles = cv2.RQDecomp3x3(rotation)[0]

        pitch, yaw, roll = map(float, angles)

        return yaw, pitch, roll

    except (ValueError, TypeError, cv2.error):
        return 0.0, 0.0, 0.0


def calculate_face_quality(landmarks):
    """顔のランドマークから解析品質を段階的に評価する。"""

    landmark_count = len(landmarks)

    if landmark_count < 468:
        return {
            "landmark_count": landmark_count,
            "face_quality": 0.0,
            "analysis_valid": False,
            "landmark_in_frame_ratio": 0.0,
            "landmark_out_of_frame_count": 0
        }

    xs = np.array([p.x for p in landmarks], dtype=float)
    ys = np.array([p.y for p in landmarks], dtype=float)

    # NaNや無限大などの異常値を確認
    finite_mask = np.isfinite(xs) & np.isfinite(ys)

    if not finite_mask.all():
        return {
            "landmark_count": landmark_count,
            "face_quality": 0.0,
            "analysis_valid": False,
            "landmark_in_frame_ratio": 0.0,
            "landmark_out_of_frame_count": landmark_count
        }

    # 画面内にあるランドマークの割合
    in_frame_mask = (
        (xs >= 0.0) &
        (xs <= 1.0) &
        (ys >= 0.0) &
        (ys <= 1.0)
    )

    in_frame_count = int(np.count_nonzero(in_frame_mask))
    out_of_frame_count = landmark_count - in_frame_count

    in_frame_ratio = in_frame_count / landmark_count

    # 顔の大きさ
    width = float(xs.max() - xs.min())
    height = float(ys.max() - ys.min())

    size_valid = width >= 0.10 and height >= 0.10

    # 画面外の点が5%以内なら解析を有効とする
    position_valid = in_frame_ratio >= 0.95

    analysis_valid = bool(size_valid and position_valid)

    # 品質を0～100点で評価
    quality = round(in_frame_ratio * 100, 1)

    if not size_valid:
        quality = 0.0

    return {
        "landmark_count": landmark_count,
        "face_quality": quality,
        "analysis_valid": analysis_valid,
        "landmark_in_frame_ratio": round(in_frame_ratio, 4),
        "landmark_out_of_frame_count": out_of_frame_count
    }



def analyze_face(result):

    if not result.face_landmarks:
        movement_tracker.update(None)
        return None

    landmarks = result.face_landmarks[0]

    blendshapes = get_blendshape_dict(result)

    # =================================
    # ① 顔の範囲
    # =================================

    xs = [p.x for p in landmarks]
    ys = [p.y for p in landmarks]

    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    nose = landmarks[1]

    yaw, pitch, roll = get_face_angle(result)

    # =================================
    # ② 基本解析
    # =================================

    metrics = {
        "face_detected": True,

        "face_x": round(float(nose.x), 4),
        "face_y": round(float(nose.y), 4),

        "face_width": round(max_x - min_x, 4),
        "face_height": round(max_y - min_y, 4),

        "face_left": round(min_x, 4),
        "face_right": round(max_x, 4),
        "face_top": round(min_y, 4),
        "face_bottom": round(max_y, 4),

        "face_yaw": round(yaw, 2),
        "face_pitch": round(pitch, 2),
        "face_roll": round(roll, 2),

        "smile_score": round(
            (
                blendshapes.get("mouthSmileLeft", 0.0)
                + blendshapes.get("mouthSmileRight", 0.0)
            ) / 2,
            4
        ),

        "mouth_open": round(
            blendshapes.get("jawOpen", 0.0), 4
        ),

        "left_blink": round(
            blendshapes.get("eyeBlinkLeft", 0.0), 4
        ),

        "right_blink": round(
            blendshapes.get("eyeBlinkRight", 0.0), 4
        )
    }

    # =================================
    # ③ 目・視線
    # =================================

    eye_data = analyze_eyes(landmarks)

    metrics.update(eye_data)

    # =================================
    # ④ 口の動き
    # =================================

    mouth_data = analyze_mouth(
        landmarks,
        blendshapes
    )

    metrics.update(mouth_data)

    # =================================
    # ⑤ 表情特徴量
    # =================================

    expression_data = analyze_expression(
        blendshapes
    )

    metrics.update(expression_data)

    # =================================
    # ⑥ 顔の移動
    # =================================

    movement_data = movement_tracker.update(
        metrics
    )

    metrics.update(movement_data)

    # =================================
    # ⑦ 解析品質
    # =================================

    quality_data = calculate_face_quality(
        landmarks
    )

    metrics.update(quality_data)

    return metrics
