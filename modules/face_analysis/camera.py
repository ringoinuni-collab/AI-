
import cv2
import time

from .detector import create_detector, detect_face
from .analyzer import analyze_face
from .face_data import save_face_data


def run_camera(user_id="local_user"):

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        raise RuntimeError(
            "Webカメラを起動できません。"
        )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    detector = None
    last_save_time = 0
    last_timestamp = 0

    try:

        detector = create_detector()

        print("顔画像解析を開始しました")
        print("終了するには Q キーを押してください")

        while True:

            ret, frame = cap.read()

            if not ret:
                print("カメラ映像を取得できません")
                break

            # 左右反転
            frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            timestamp = time.monotonic_ns() // 1_000_000

            timestamp = max(
                timestamp,
                last_timestamp + 1
            )

            last_timestamp = timestamp

            result = detect_face(
                detector,
                rgb,
                timestamp
            )

            data = analyze_face(result)

            if data is not None:

                # 顔の特徴点を描画
                for point in result.face_landmarks[0]:

                    px = int(point.x * frame.shape[1])
                    py = int(point.y * frame.shape[0])

                    cv2.circle(
                        frame,
                        (px, py),
                        1,
                        (0, 255, 100),
                        -1
                    )

                # 解析結果を表示
                lines = [
                    "FACE: DETECTED",
                    f"SMILE: {data['smile_score']:.2f}",
                    f"MOUTH: {data['mouth_open']:.2f}",
                    f"LEFT BLINK: {data['left_blink']:.2f}",
                    f"RIGHT BLINK: {data['right_blink']:.2f}",
                    f"YAW: {data['face_yaw']:.1f}",
                    f"PITCH: {data['face_pitch']:.1f}",
                    f"ROLL: {data['face_roll']:.1f}"
                ]

                for i, line in enumerate(lines):

                    cv2.putText(
                        frame,
                        line,
                        (15, 30 + i * 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 255, 100),
                        2
                    )

                # 1秒に1回JSON保存
                now = time.monotonic()

                if now - last_save_time >= 1:

                    save_face_data(
                        user_id,
                        data
                    )

                    last_save_time = now

            else:

                cv2.putText(
                    frame,
                    "FACE: NOT DETECTED",
                    (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            cv2.imshow(
                "Face Image Analysis - No.6",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    finally:

        if detector is not None:
            detector.close()

        cap.release()
        cv2.destroyAllWindows()

        print("顔画像解析を終了しました")
