import threading
import webview
import threading
import time

from UI.boundary import App, WebViewWindow

# ===============================================
# このクラスなどの想定使用方法
#
# from main import core, app としてインポート
# core.running でアプリが動作しているか確認できる
# while(core.running): などで動作を継続する想定
#
# appはvolume, camera, micのプロパティを持つ
# volumeはデバイスの音量サイズ、0～100の整数
# cameraは表情認識、micは音声認識の機能をオンにするか、bool型
# app.volume = 50 のように代入すればUIも更新される
# ===============================================


class Core:
    def __init__(self):
        # 同期関連
        self.event = threading.Event()

        # スレッド管理
        self._threads: list[threading.Thread] = []

    # バックグラウンド処理の開始
    def start_tasks(self):
        """バックグラウンド処理を開始する"""
        tasks = [eternal_process]

        for task in tasks:
            thread = threading.Thread(
                target=task,
                args=(),
                daemon=False
            )
            thread.start()
            self._threads.append(thread)

    # 停止通知
    def stop(self):
        """バックグラウンド処理に停止を通知する"""
        self.event.set()

    # スレッド終了待ち
    def join_tasks(self):
        """バックグラウンド処理の終了を待つ"""
        for thread in self._threads:
            thread.join()

    @property
    def running(self) -> bool:
        """(bool)アプリが動作しているか"""
        return not self.event.is_set()

core = Core()


def eternal_process():
    """テスト用の永続的な処理"""
    while core.running:
        print(core.running)
        time.sleep(5)


app = App()

window = webview.create_window(
    "My Application",
    "UI/index.html",
    width=600,
    height=500,
    resizable=False,
    js_api=app,
)
window = WebViewWindow(window)
app.create_update_funcs(window.update_ui)

core.start_tasks()

webview.start()

core.stop()
core.join_tasks()