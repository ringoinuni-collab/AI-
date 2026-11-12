
def analyze_expression(blendshapes):

    names = [
        "browDownLeft",
        "browDownRight",
        "browInnerUp",
        "browOuterUpLeft",
        "browOuterUpRight",
        "cheekSquintLeft",
        "cheekSquintRight",
        "eyeWideLeft",
        "eyeWideRight",
        "mouthFrownLeft",
        "mouthFrownRight",
        "mouthSmileLeft",
        "mouthSmileRight",
        "jawOpen"
    ]

    result = {}

    for name in names:
        result[name] = round(
            float(blendshapes.get(name, 0.0)), 4
        )

    # 左右の笑顔の差
    result["smile_asymmetry"] = round(
        abs(
            result["mouthSmileLeft"] -
            result["mouthSmileRight"]
        ), 4
    )

    # 左右の眉上げの差
    result["brow_asymmetry"] = round(
        abs(
            result["browOuterUpLeft"] -
            result["browOuterUpRight"]
        ), 4
    )

    return result
