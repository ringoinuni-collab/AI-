import webview
import platform
import threading

os = platform.system()
if os == "Linux":
    import pulsectl
    def get_device_volume() -> float:
        with pulsectl.Pulse("python-volume") as pulse:
            sink = pulse.get_sink_by_name(
                pulse.server_info().default_sink_name
            )
            now_volume = round(sink.volume.value_flat * 100)
        return now_volume

    def set_device_volume(value: float) -> None:
        value = max(0, min(100.0, value))

        with pulsectl.Pulse("python-volume") as pulse:
            sink = pulse.get_sink_by_name(
                pulse.server_info().default_sink_name
            )
            pulse.volume_set_all_chans(sink, value / 100)

elif os == "Windows":
    from pycaw.pycaw import AudioUtilities
    def get_device_volume() -> float:
        return round(AudioUtilities.GetSpeakers().volume_percent)

    def set_device_volume(value: float) -> None:
        value = max(0, min(100.0, value))

        device = AudioUtilities.GetSpeakers()
        device.volume_percent = value
else:
    raise NotImplementedError("このOSはサポートされていません。")

class App:
    def __init__(self):
        self.window: WebViewWindow | None = None
        self._now_volume = get_device_volume()
        self._volume = self._now_volume
        self._camera = False
        self._microphone = False
        self._lock = threading.Lock()

    def update_volume(self, value: float) -> None: pass
    def update_camera(self, value: bool) -> None: pass
    def update_mic(self, value: bool) -> None: pass
    def create_update_funcs(self, fn: callable) -> None:
        self.update_volume = lambda value: fn("updateVolume", value)
        self.update_camera = lambda value: fn("updateCamera", value)
        self.update_mic = lambda value: fn("updateMic", value)

    def set_now_volume(self, value: float) -> None:
        set_device_volume(value)

    def get_volume(self) -> float:
        """通信用・現在の音量を取得（0～100）"""
        with self._lock:
            return self._volume

    def set_volume(self, value: float) -> None:
        """通信用・音量を設定（0～100）"""
        if value < 0 or value > 100:
            raise ValueError("音量は0～100の範囲で指定してください。")
        with self._lock:
            self._volume = value
        self.update_volume(round(value, 2))

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
    def now_volume(self) -> float:
        """
        (float)実際に流すデバイス音量（0～100）\n
        すぐに書き換わるので使用は非推奨
        """
        return self._now_volume
    @now_volume.setter
    def now_volume(self, value: int) -> None:
        self._now_volume = value
        self.set_now_volume(value)

    @property
    def volume(self) -> float:
        """(float)デバイス音量（0～100）"""
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


if __name__ == "__main__":
    app = App()

    window = webview.create_window(
        "My Application",
        "index.html",
        width=600,
        height=500,
        resizable=False,
        js_api=app,
    )
    window = WebViewWindow(window)
    app.create_update_funcs(window.update_ui)

    webview.start()