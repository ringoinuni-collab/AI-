
import cv2


def get_score(categories, name):
    for item in categories:
        if item.category_name == name:
            return float(item.score)

    return 0.0


def analyze_face(result):

    # 顔が検出されなかった場合
    if not result.face_landmarks:
        return None

    landmarks = result.face_landmarks[0]

    # 表情データ
    categories = []

    if result.face_blendshapes:
        blendshapes = result.face_blendshapes[0]

        if hasattr(blendshapes, "categories"):
            categories = blendshapes.categories
        else:
            categories = blendshapes

    # 笑顔
    smile = (
        get_score(categories, "mouthSmileLeft") +
        get_score(categories, "mouthSmileRight")
    ) / 2

    # 口の開き
    mouth = get_score(categories, "jawOpen")

    # まばたき
    left_blink = get_score(categories, "eyeBlinkLeft")
    right_blink = get_score(categories, "eyeBlinkRight")

    # 顔の中心位置
    nose = landmarks[1]

    x = nose.x
    y = nose.y

    # 顔の向き
    yaw = pitch = roll = 0.0

    if result.facial_transformation_matrixes:

        matrix = result.facial_transformation_matrixes[0]

        rotation = matrix[:3, :3]

        angles = cv2.RQDecomp3x3(rotation)[0]

        pitch, yaw, roll = map(float, angles)

    return {
        "face_detected": True,
        "smile_score": round(smile, 4),
        "mouth_open": round(mouth, 4),
        "left_blink": round(left_blink, 4),
        "right_blink": round(right_blink, 4),
        "face_x": round(float(x), 4),
        "face_y": round(float(y), 4),
        "face_yaw": round(yaw, 2),
        "face_pitch": round(pitch, 2),
        "face_roll": round(roll, 2)
    }
