import webview
import platform

from UI.schema import App, WebViewWindow

os = platform.system()
if os == "Linux":
    import pulsectl
    with pulsectl.Pulse("python-volume") as pulse:
        sink = pulse.get_sink_by_name(
            pulse.server_info().default_sink_name
        )
        now_volume = round(sink.volume.value_flat * 100)

    def set_device_volume(value: int) -> None:
        value = max(0, min(100, value))

        with pulsectl.Pulse("python-volume") as pulse:
            sink = pulse.get_sink_by_name(
                pulse.server_info().default_sink_name
            )
            pulse.volume_set_all_chans(sink, value / 100)

elif os == "Windows":
    from pycaw.pycaw import AudioUtilities
    now_volume = round(AudioUtilities.GetSpeakers().volume_percent)

    def set_device_volume(value: int) -> None:
        value = max(0, min(100, value))

        device = AudioUtilities.GetSpeakers()
        device.volume_percent = value

else:
    raise NotImplementedError("このOSはサポートされていません。")


if __name__ == "__main__":
    app = App(now_volume)

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
    app.set_device_volume = set_device_volume

    webview.start()
# git push -u origin feature/onishi