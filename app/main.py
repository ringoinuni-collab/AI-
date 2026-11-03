import threading
import webview
import threading
import time

from UI.schema import App, WebViewWindow
from UI.boundary import set_device_volume, now_volume
from core_schema import Core
from default_controll.volume_controll import VolumeController

# ===============================================
# このクラスなどの想定使用方法
#
# core, app を引数として渡して使用する
# core.running でアプリが動作しているか確認できる
# while(core.running): などで動作を継続する想定
#
# appはvolume, camera, micのプロパティを持つ
# volumeはデバイスの音量サイズ、0～100の整数
# cameraは表情認識、micは音声認識の機能をオンにするか、bool型
# app.volume = 50 のように代入すればUIも更新される
# ===============================================

# メモ：音量を２つ用意する
core = Core()


def eternal_process(core: Core):
    """テスト用の永続的な処理"""
    while core.running:
        print(core.running)
        time.sleep(5)

app = App(now_volume)

window = webview.create_window(
    "My Application",
    "UI/index.html",
    width=600,
    height=400,
    resizable=False,
    js_api=app,
)
window = WebViewWindow(window)
app.create_update_funcs(window.update_ui)
app.set_device_volume = set_device_volume

volume_controller = VolumeController(app, core)
core.start_tasks(lambda: eternal_process(core), volume_controller.start_recording)

webview.start()

core.stop()
core.join_tasks()