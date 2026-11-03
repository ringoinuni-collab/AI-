import webview
import platform
import threading

class App:
    def __init__(self, now_volume: int):
        self.window: WebViewWindow | None = None
        self._volume = now_volume
        self._camera = False
        self._microphone = False
        self._lock = threading.Lock()

    def update_volume(self, value: int) -> None: pass
    def update_camera(self, value: bool) -> None: pass
    def update_mic(self, value: bool) -> None: pass
    def create_update_funcs(self, fn: callable) -> None:
        self.update_volume = lambda value: fn("updateVolume", value)
        self.update_camera = lambda value: fn("updateCamera", value)
        self.update_mic = lambda value: fn("updateMic", value)
    def set_device_volume(self, value: int) -> None: pass

    def get_volume(self) -> int:
        """通信用・現在の音量を取得（0～100）"""
        with self._lock:
            return self._volume

    def set_volume(self, value: int) -> None:
        """通信用・音量を設定（0～100）"""
        if value < 0 or value > 100:
            raise ValueError("音量は0～100の範囲で指定してください。")
        with self._lock:
            self._volume = value
        self.update_volume(value)
        self.set_device_volume(value)

    def toggle_cam(self) -> None:
        """カメラのオン/オフを切り替え"""
        with self._lock:
            self._camera = not self._camera
        self.update_camera(self._camera)

    def toggle_mic(self) -> None:
        """マイクのオン/オフを切り替え"""
        with self._lock:
            self._microphone = not self._microphone
        self.update_mic(self._microphone)

    @property
    def volume(self) -> int:
        """(int)デバイス音量（0～100）"""
        return self.get_volume()
    @volume.setter
    def volume(self, value: int) -> None:
        self.set_volume(value)

    @property
    def camera(self) -> bool:
        """(bool)表情認識機能を使用するか"""
        with self._lock:
            return self._camera
    @camera.setter
    def camera(self, value: bool) -> None:
        if value not in [True, False]:
            raise ValueError("カメラの状態はboolで指定してください。")
        with self._lock:
            self._camera = value
        self.update_camera(self._camera)

    @property
    def mic(self) -> bool:
        """(bool)音声認識機能を使用するか"""
        with self._lock:
            return self._microphone
    @mic.setter
    def mic(self, value: bool) -> None:
        if value not in [True, False]:
            raise ValueError("マイクの状態はboolで指定してください。")
        with self._lock:
            self._microphone = value
        self.update_mic(self._microphone)

class WebViewWindow:
    def __init__(self, window: webview.Window):
        self.window = window
    def update_ui(self, func_name: str, value) -> None:
        if type(value) is bool:
            value = "true" if value else "false"
        self.window.evaluate_js(f"{func_name}({value})")