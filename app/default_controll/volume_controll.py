import soundcard as sc
import numpy as np
import pythoncom
from time import sleep

from UI.boundary import App
from core_schema import Core

class VolumeController:
    """
    音声の大きさを調整するクラス\n
    文書で言うところの「元々あった機能」
    """
    def __init__(self, app: App, core: Core, target_rms=0.1):
        self.target_rms = target_rms
        self.smoothed_rms = target_rms
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
                    while self.app.mic.is_on and self.core.running:
                        sleep(0.1)

                    # 0.1秒分の音声を取得して音量を変更
                    data = recorder.record(numframes=4800)
                    self.app.now_volume = self.adjust_volume(data)
        finally:
            pythoncom.CoUninitialize()

    def adjust_volume(self, data, smoothness=0.9, stability=0.5) -> float:
        """変更後の音量を決定する関数"""
        # RMS値を計算
        rms = np.sqrt(np.mean(data ** 2))
        if rms < 1e-6:
            return self.app.volume

        self.smoothed_rms = smoothness * self.smoothed_rms + (1 - smoothness) * rms

        # RMS値を基にゲインを求める
        gain = self.target_rms / self.smoothed_rms
        gain = max(0.25, min(4, gain))

        # ゲインを適用して音量を調整
        new_volume = stability * self.app.now_volume + (1 - stability) * (self.app.volume * gain)
        if abs(new_volume - self.app.now_volume) < 1.0:
            return self.app.now_volume
        return max(0, min(100, new_volume))