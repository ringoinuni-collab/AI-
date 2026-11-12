


"""音量調整アプリの起動用ファイル"""

import json
import sys
import threading
from pathlib import Path

import webview

from core_schema import Core
from app.UI.boundary import App, WebViewWindow

from app.UI.default_controll.volume_controll import (
    VolumeController,
)

from volume import (
    AIService,
    WindowsProvider,
)


def resource_path(relative_path):
    """通常起動・exe化の両方に対応したパス。"""
    base = Path(
        getattr(
            sys,
            "_MEIPASS",
            Path(__file__).resolve().parent,
        )
    )

    return base / relative_path


class IntegratedApp(App):
    """既存の画面APIに担当Cの機能を追加する。"""

    def __init__(self):
        super().__init__()

        self.ai = AIService()
        self.provider = WindowsProvider()

        self._context = None
        self._context_lock = threading.Lock()
        self._detection_error = None

    def monitor_usage(self, core):
        """利用状況を2秒ごとに更新する。"""
        while core.running:
            try:
                raw = self.provider.collect()

                context = self.ai.inspect(raw)

                with self._context_lock:
                    self._context = context
                    self._detection_error = None

            except Exception as error:
                with self._context_lock:
                    self._detection_error = str(error)

            # アプリ終了時は待機を途中で解除できる。
            core.event.wait(2)

    def get_usage_status(self):
        """画面から現在の利用状況を取得する。"""
        with self._context_lock:
            # 画面へ渡す値をコピーする。
            context = (
                json.loads(
                    json.dumps(self._context)
                )
                if self._context is not None
                else None
            )

            return {
                "context": context,
                "error": self._detection_error,
            }

    def get_ai_proposals(self):
        """画面の提案取得ボタンなどから呼ぶ。"""
        status = self.get_usage_status()

        if status["error"]:
            return {
                "proposals": [],
                "error": status["error"],
            }

        if status["context"] is None:
            return {
                "proposals": [],
                "error": "利用状況を取得中です",
            }

        return {
            "proposals": self.ai.propose(
                status["context"]
            ),
            "error": None,
        }

    def reject_ai_proposal(self, suggestion_id):
        """画面からAI提案を拒否する。"""
        self.ai.feedback(
            suggestion_id=int(suggestion_id),
            result="rejected",
        )

        return {"ok": True}


def main():
    core = Core()

    try:
        app = IntegratedApp()

        html_path = resource_path(
            "UI/index.html"
        )

        if not html_path.is_file():
            raise FileNotFoundError(
                f"画面ファイルがありません: {html_path}"
            )

        window = webview.create_window(
            title="音量調整アプリ",
            url=str(html_path),
            width=600,
            height=400,
            resizable=False,
            js_api=app,
        )

        ui = WebViewWindow(window)

        app.create_update_funcs(
            ui.update_ui
        )

        volume_controller = VolumeController(
            app,
            core,
        )

        def start_background_tasks():
            core.start_tasks(
                volume_controller.start_recording,
                lambda: app.monitor_usage(core),
            )

        # 画面の準備ができてから処理を開始する。
        window.events.loaded += (
            start_background_tasks
        )

        # ウィンドウ終了時に停止を通知する。
        window.events.closed += core.stop

        webview.start()

    finally:
        core.stop()
        core.join_tasks()


if __name__ == "__main__":
    main()
