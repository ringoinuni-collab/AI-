
import sounddevice as sd
import numpy as np
import queue
import threading
import torch

from collections import deque

from talk_control.NLP import recognize_command
from core_schema import Core
from UI.boundary import App
from time import sleep

# ==================================
# 音声認識クラス
# ==================================

class VoiceRecognition:

    def __init__(self, core: Core, app: App):

        self.core = core
        self.app = app

        self.audio_queue = queue.Queue(maxsize=200)
        self.recognition_queue = queue.Queue()

        self.running = False

        self.threads = []
        # ==================================
        # 設定
        # ==================================

        self.SAMPLE_RATE = 16000
        self.FRAME_SIZE = 512

        self.SILENCE_DURATION = 0.7
        self.PRE_ROLL_DURATION = 0.32
        self.MAX_COMMAND_DURATION = 10.0
        self.MIN_COMMAND_DURATION = 0.25

        self.VAD_THRESHOLD = 0.5

        self.vad_model = None
        self.whisper_model = None

    # ==================================
    # キュー操作
    # ==================================

    def clear_queue(self, target_queue):

        while True:
            try:
                target_queue.get_nowait()
            except queue.Empty:
                break

    # ==================================
    # 音声取得
    # ==================================

    def audio_callback(self, indata, frames, time, status):

        if status:
            print("Audio status:", status)

        # アプリ停止・マイクOFFなら取得しない
        if not self.core.running or not self.app.mic.is_on:
            return

        try:
            self.audio_queue.put_nowait(
                indata[:, 0].copy()
            )

        except queue.Full:
            print("Audio queue is full")

    def recording_worker(self):

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=self.FRAME_SIZE,
            callback=self.audio_callback
        ):

            while self.core.running:

                sd.sleep(50)

        print("[録音スレッド終了]")

    # ==================================
    # VAD・発話区間検出
    # ==================================

    def vad_worker(self):

        frame_duration = self.FRAME_SIZE / self.SAMPLE_RATE

        silence_frames_required = int(
            self.SILENCE_DURATION / frame_duration
        )

        pre_roll_frames = int(
            self.PRE_ROLL_DURATION / frame_duration
        )

        max_frames = int(
            self.MAX_COMMAND_DURATION / frame_duration
        )

        min_frames = int(
            self.MIN_COMMAND_DURATION / frame_duration
        )

        pre_buffer = deque(maxlen=pre_roll_frames)

        speech_frames = []

        speaking = False
        silence_count = 0

        while self.core.running:

            # ----------------------------------
            # マイクOFF
            # ----------------------------------

            if not self.app.mic.is_on:

                # 発話状態をリセット
                speaking = False
                silence_count = 0
                speech_frames = []
                pre_buffer.clear()

                # 古い音声を破棄
                self.clear_queue(self.audio_queue)

                # VADの内部状態もリセット
                if hasattr(self.vad_model, "reset_states"):
                    self.vad_model.reset_states()

                threading.Event().wait(0.05)
                continue

            # ----------------------------------
            # 音声取得
            # ----------------------------------

            try:
                frame = self.audio_queue.get(timeout=0.1)

            except queue.Empty:
                continue

            # 取得中にマイクOFFになった場合
            if not self.core.running or not self.app.mic.is_on:
                continue

            # ----------------------------------
            # VAD
            # ----------------------------------

            audio_tensor = torch.from_numpy(
                frame.astype(np.float32)
            )

            with torch.inference_mode():

                probability = self.vad_model(
                    audio_tensor,
                    self.SAMPLE_RATE
                ).item()

            is_speech = probability >= self.VAD_THRESHOLD

            # ----------------------------------
            # 発話開始前
            # ----------------------------------

            if not speaking:

                pre_buffer.append(frame)

                if is_speech:

                    speaking = True
                    silence_count = 0

                    speech_frames = list(pre_buffer)

                    print("\n[発話開始]")

            # ----------------------------------
            # 発話中
            # ----------------------------------

            else:

                speech_frames.append(frame)

                if is_speech:
                    silence_count = 0

                else:
                    silence_count += 1

                ended = (
                    silence_count >= silence_frames_required
                )

                too_long = (
                    len(speech_frames) >= max_frames
                )

                # ----------------------------------
                # 発話終了
                # ----------------------------------

                if ended or too_long:

                    if len(speech_frames) >= min_frames:

                        audio = np.concatenate(speech_frames)

                        if (
                            self.core.running
                            and self.app.mic.is_on
                        ):
                            self.recognition_queue.put(audio)

                    else:
                        print("[短すぎる発話を破棄]")

                    speaking = False
                    silence_count = 0
                    speech_frames = []
                    pre_buffer.clear()

                    print("[発話終了]")

        # ----------------------------------
        # スレッド終了
        # ----------------------------------

        # 停止時に残った発話は破棄する
        self.recognition_queue.put(None)

        print("[VADスレッド終了]")

    # ==================================
    # 文字起こし
    # ==================================

    def recognition_worker(self):

        while self.core.running:

            # ----------------------------------
            # マイクOFF
            # ----------------------------------

            if not self.app.mic.is_on:

                # 一時停止中の未処理音声を破棄
                self.clear_queue(self.recognition_queue)

                threading.Event().wait(0.05)
                continue

            # ----------------------------------
            # 音声取得
            # ----------------------------------

            try:
                audio = self.recognition_queue.get(
                    timeout=0.1
                )

            except queue.Empty:
                continue

            if audio is None:
                break

            if not self.core.running:
                break

            if not self.app.mic.is_on:
                continue

            # ----------------------------------
            # Whisper
            # ----------------------------------

            print("[文字起こし中]")

            try:

                segments, info = self.whisper_model.transcribe(
                    audio,
                    language="ja",
                    beam_size=1,
                    vad_filter=False
                )

                text = "".join(
                    segment.text for segment in segments
                ).strip()

                # 文字起こし中に停止・一時停止された場合
                if not self.core.running:
                    break

                if not self.app.mic.is_on:
                    continue

                if text:

                    print("認識結果:", text)

                    self.language_processing(text)

            except Exception as e:

                print("Recognition error:", e)

        print("[認識スレッド終了]")

    # ==================================
    # 言語処理
    # ==================================

    def language_processing(self, text):

        print("[言語処理]", text)

        change_volume = recognize_command(text)
        self.app.volume += change_volume

    # ==================================
    # 開始
    # ==================================

    def start(self):

        if self.running:
            return

        if not self.core.running:
            print("[アプリが停止しているため開始できません]")
            return

        self.running = True

        self.clear_queue(self.audio_queue)
        self.clear_queue(self.recognition_queue)

        self.threads = [

            threading.Thread(
                target=self.recording_worker,
                name="VoiceRecording"
            ),

            threading.Thread(
                target=self.vad_worker,
                name="VoiceVAD"
            ),

            threading.Thread(
                target=self.recognition_worker,
                name="VoiceRecognition"
            )

        ]

        for thread in self.threads:
            thread.start()

        print("[音声認識開始]")

    # ==================================
    # 終了待ち
    # ==================================

    def join(self):

        for thread in self.threads:
            thread.join()
        self.running = False

        print("[音声認識終了]")

    # ==================================
    # 一時停止・再開
    # ==================================

    def pause(self):

        self.app.mic.off()

        print("[音声認識一時停止]")

    def resume(self):

        if not self.core.running:
            return

        self.app.mic.on()

        print("[音声認識再開]")


# ==================================
# メイン
# ==================================

    def main(self):
        # ==================================
        # モデル読み込み
        # ==================================

        print("モデルを読み込んでいます...")

        from faster_whisper import WhisperModel
        from silero_vad import load_silero_vad
        self.vad_model = load_silero_vad()

        if not self.core.running:
            print("[Core停止によりモデル読み込みを中断]")
            return

        self.whisper_model = WhisperModel(
            "medium",
            device="cpu",
            compute_type="int8"
        )

        if not self.core.running:
            print("[Core停止により音声認識を開始しません]")
            return

        print("モデル読み込み完了")

        self.start()

        try:
            while self.core.running:

                if self.app.mic.is_on:
                    self.resume()
                    # マイクがONなら状態を監視
                    while self.app.mic.is_on and self.core.running:
                        sleep(0.1)
                    self.pause()

                else:
                    # マイクがOFFなら一時停止
                    self.pause()

                    # マイクがONになるまで待機
                    while not self.app.mic.is_on and self.core.running:
                        sleep(0.1)

                    self.resume()

                sleep(0.1)

        finally:
            # Core停止時に音声処理スレッドの終了を待つ
            self.join()


if __name__ == "__main__":
    import threading
    core = Core()
    app = App()
    app.mic.on()
    recognizer = VoiceRecognition(core, app)
    core.start_tasks(recognizer.main)
    from time import sleep
    sleep(10)
    core.stop()
    core.join_tasks()

"""
cd AI-/app
python -m talk_control.recognition
"""