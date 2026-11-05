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
# app.cam、app.mic、app.adj：
#   camが顔認証、micが音声認識、adjが音量自動調整のオンオフを管理
#   app.cam.on() でオン、app.cam.off() でオフにできる
#     (cameraの部分は各機能の名前に変更)
#   app.cam.is_on でオンかオフかを取得できる
#   app.cam.wait() でオンになるまで待機できる
# ===============================================

# メモ：音量を２つ用意する
core = Core()

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
    volume_controller.start_recording,
)

webview.start()

core.stop()
core.join_tasks()