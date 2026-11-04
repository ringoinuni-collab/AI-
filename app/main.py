import threading
import webview
import threading
import time

from UI.boundary import App, WebViewWindow
from core_schema import Core
from default_controll.volume_controll import VolumeController

# ===============================================
# このクラスなどの想定使用方法
#
# core, app を引数として渡して使用する
# core.running：アプリが動作しているか確認
#   while(core.running): などで動作を継続する想定
# core.os：OSの種類を取得
#
# app.volume：デバイスの音量サイズ、0～100の少数
#   app.volume = 50 のように代入すればUIも更新される
# app.camera：表情認識の機能をオンにするか、bool型
# app.mic：音声認識の機能をオンにするか、bool型
# ===============================================

# メモ：音量を２つ用意する
core = Core()


def eternal_process(core: Core):
    """テスト用の永続的な処理"""
    while core.running:
        print(core.running)
        time.sleep(5)

app = App()

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

volume_controller = VolumeController(app, core)
core.start_tasks(
    lambda: eternal_process(core),
    volume_controller.start_recording,
)

webview.start()

core.stop()
core.join_tasks()