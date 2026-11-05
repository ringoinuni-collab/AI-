import threading
import platform

class Core:
    def __init__(self):
        # 同期関連
        self.event = threading.Event()

        # スレッド管理
        self._threads: list[threading.Thread] = []

        self.os = platform.system()

    # バックグラウンド処理の開始
    def start_tasks(self, *tasks: tuple[callable]):
        """バックグラウンド処理を開始する"""

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