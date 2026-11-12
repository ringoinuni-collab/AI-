
def analyze_mouth(landmarks, blendshapes):

    if len(landmarks) <= 291:
        return {}

    # 口の上下と左右
    upper = landmarks[13]
    lower = landmarks[14]
    left = landmarks[61]
    right = landmarks[291]

    face_width = abs(
        landmarks[234].x - landmarks[454].x
    )

    if face_width == 0:
        face_width = 1.0

    mouth_open = abs(upper.y - lower.y) / face_width

    mouth_width = abs(left.x - right.x) / face_width

    corner_difference = left.y - right.y

    return {
        "mouth_open_ratio": round(mouth_open, 4),
        "mouth_width_ratio": round(mouth_width, 4),
        "mouth_corner_difference": round(
            corner_difference, 4
        ),
        "smile_left": round(
            blendshapes.get("mouthSmileLeft", 0.0), 4
        ),
        "smile_right": round(
            blendshapes.get("mouthSmileRight", 0.0), 4
        ),
        "jaw_open_score": round(
            blendshapes.get("jawOpen", 0.0), 4
        )
    }
