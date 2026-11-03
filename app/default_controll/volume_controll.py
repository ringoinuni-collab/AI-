import soundcard as sc
import numpy as np
import pythoncom

from UI.schema import App
from core_schema import Core

class VolumeController:
    """
    音声の大きさを調整するクラス\n
    文書で言うところの「元々あった機能」
    """
    def __init__(self, app: App, core: Core, target_rms=0.1):
        self.target_rms = target_rms
        self.app = app
        self.core = core

    def start_recording(self):
        pythoncom.CoInitialize()

        try:
            # 現在の既定スピーカーを取得
            self.speaker = sc.default_speaker()

            # スピーカーに対応するLoopbackデバイスを取得
            self.loopback = sc.get_microphone(
                id=self.speaker.name,
                include_loopback=True
            )
            with self.loopback.recorder(
                samplerate=48000,
                channels=2,
                blocksize=4800
            ) as recorder:

                while self.core.running:
                    # 0.1秒分の音声を取得して音量を変更
                    data = recorder.record(numframes=4800)
                    self.app.volume = self.adjust_volume(data)
        finally:
            pythoncom.CoUninitialize()

    def adjust_volume(self, data, alpha=0.3):
        """変更後の音量を決定する関数"""
        # RMS値を計算
        rms = np.sqrt(np.mean(data ** 2))
        if rms < 1e-6:
            return self.app.volume

        # RMS値を基にゲインを求める
        gain = self.target_rms / rms
        gain = max(0.25, min(4, gain))

        # ゲインを適用して音量を調整
        return alpha * self.app.volume + (1 - alpha) * (self.app.volume * gain)