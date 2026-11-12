
import mediapipe as mp
from pathlib import Path


MODEL_PATH = Path(
    r"C:\face_models\face_landmarker.task"
)

def create_detector():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"顔認識モデルがありません: {MODEL_PATH}"
        )

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True
    )

    return mp.tasks.vision.FaceLandmarker.create_from_options(
        options
    )


def detect_face(detector, frame, timestamp_ms):

    rgb = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=frame
    )

    return detector.detect_for_video(
        rgb,
        timestamp_ms
    )
