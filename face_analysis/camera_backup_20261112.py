
import cv2
import time

from .detector import create_detector, detect_face
from .analyzer import analyze_face
from .face_data import save_face_data
from .personal_baseline import PersonalBaseline
from .trend_analysis import TrendAnalyzer
from .dashboard import FaceDashboard


def run_camera(user_id="local_user"):

    # =================================
    # ① カメラ起動
    # =================================

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        raise RuntimeError(
            "Webカメラを起動できません。"
        )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # =================================
    # ② 解析機能の準備
    # =================================

    detector = None

    baseline = PersonalBaseline(user_id=user_id)

    trend_analyzer = TrendAnalyzer()

    dashboard = FaceDashboard()

    last_save_time = 0
    last_timestamp = 0
    frame_count = 0

    calibration_message = (
        "CALIBRATION"
        if not baseline.baseline
        else "BASELINE READY"
    )

    try:

        detector = create_detector()

        print("==============================")
        print("顔画像解析システム レベル6")
        print("==============================")

        if baseline.baseline:
            print("保存済みの個人内基準を読み込みました")
        else:
            print("通常状態の測定を開始します")
            print("できるだけ自然な表情で正面を向いてください")

        print("終了するには Q キーを押してください")

        # =================================
        # ③ カメラ解析ループ
        # =================================

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

            # MediaPipe用タイムスタンプ
            timestamp = time.monotonic_ns() // 1_000_000

            timestamp = max(
                timestamp,
                last_timestamp + 1
            )

            last_timestamp = timestamp

            # 顔検出
            result = detect_face(
                detector,
                rgb,
                timestamp
            )

            # 顔解析
            data = analyze_face(result)

            # =================================
            # ④ 顔が検出された場合
            # =================================

            if data is not None:

                # ランドマーク描画
                for point in result.face_landmarks[0]:

                    px = int(
                        point.x * frame.shape[1]
                    )

                    py = int(
                        point.y * frame.shape[0]
                    )

                    cv2.circle(
                        frame,
                        (px, py),
                        1,
                        (0, 255, 100),
                        -1
                    )

                # =================================
                # ⑤ 個人内基準の作成
                # =================================

                comparison = None

                if not baseline.baseline:

                    completed = baseline.add_sample(data)

                    calibration_message = (
                        f"CALIBRATION: "
                        f"{len(baseline.samples)}/"
                        f"{baseline.target_samples}"
                    )

                    cv2.putText(
                        frame,
                        calibration_message,
                        (15, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 255, 255),
                        2
                    )

                    if completed:
                        print("個人内基準の作成が完了しました")

                # =================================
                # ⑥ 通常状態との比較
                # =================================

                else:

                    comparison = baseline.compare(data)

                    data["change_score"] = (
                        comparison["change_score"]
                    )

                    # 時系列分析
                    trend = trend_analyzer.update(data)

                    # 個人内変化スコア
                    cv2.putText(
                        frame,
                        f"Change: {comparison['change_score']:.1f}",
                        (15, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 255, 0),
                        2
                    )

                    # 表情
                    cv2.putText(
                        frame,
                        f"Smile: {data.get('smile_score', 0):.2f}",
                        (15, 65),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2
                    )

                    # 頭の角度
                    cv2.putText(
                        frame,
                        f"Yaw: {data.get('face_yaw', 0):.1f}",
                        (15, 95),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2
                    )

                    # 目の開き
                    cv2.putText(
                        frame,
                        f"Eye L: {data.get('left_eye_open', 0):.2f}",
                        (15, 125),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"Eye R: {data.get('right_eye_open', 0):.2f}",
                        (15, 155),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2
                    )

                    # グラフ更新は5フレームごと
                    frame_count += 1

                    if frame_count % 5 == 0:
                        dashboard.update(
                            data,
                            comparison
                        )

                # =================================
                # ⑦ 解析結果を画面に表示
                # =================================

                lines = [
                    f"SMILE: {data.get('smile_score', 0):.2f}",
                    f"MOUTH: {data.get('mouth_open', 0):.2f}",
                    f"BLINK L: {data.get('left_blink', 0):.2f}",
                    f"BLINK R: {data.get('right_blink', 0):.2f}",
                    f"YAW: {data.get('face_yaw', 0):.1f}",
                    f"PITCH: {data.get('face_pitch', 0):.1f}",
                    f"ROLL: {data.get('face_roll', 0):.1f}",
                ]

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                thickness = 1

                # カメラ映像の幅を取得
                height, width = frame.shape[:2]

                for i, line in enumerate(lines):

                    # 文字の幅を取得
                    text_width = cv2.getTextSize(
                        line,
                        font,
                        font_scale,
                        thickness
                    )[0][0]

                    # 右端から20pxの位置に配置
                    x = width - text_width - 20
                    y = 30 + i * 27

                    cv2.putText(
                        frame,
                        line,
                        (x, y),
                        font,
                        font_scale,
                        (0, 255, 100),
                        thickness
                    )

                # =================================
                # ⑧ JSON保存（1秒に1回）
                # =================================

                now = time.monotonic()

                if now - last_save_time >= 1:

                    save_data = dict(data)

                    if comparison is not None:
                        save_data["personal_change"] = comparison

                    save_face_data(
                        user_id,
                        save_data
                    )

                    last_save_time = now

            # =================================
            # ⑨ 顔が検出されなかった場合
            # =================================

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

            # =================================
            # ⑩ 映像表示
            # =================================

            cv2.imshow(
                "Face Image Analysis - Level 6",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    finally:

        if detector is not None:
            detector.close()

        cap.release()
        dashboard.close()

        cv2.destroyAllWindows()

        print("顔画像解析を終了しました")
