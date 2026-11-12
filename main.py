

"""音量調整アプリの起動用ファイル。"""

import json
import logging
import os
import sys
import threading
from pathlib import Path

from app.default_controll.volume_controll import VolumeController
from app.UI.boundary import App
from app.UI.desktop import DesktopWindow
from core_schema import Core
from volume import AIService, WindowsProvider


def resource_path(relative_path):
    """ソース実行時とEXE実行時の両方で画像を見つける。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative_path


class IntegratedApp(App):
    """既存の音量操作に利用状況の取得とAI提案を加える。"""

    def __init__(self):
        super().__init__()
        self.ai = AIService()
        self.provider = WindowsProvider()
        self._context = None
        self._context_lock = threading.Lock()
        self._detection_error = None
        self._storage_error = None

    def monitor_usage(self, core):
        last_saved = None

        while core.running:
            try:
                context = self.ai.inspect(self.provider.collect())

                with self._context_lock:
                    self._context = context
                    self._detection_error = None

                current = tuple(
                    context[key]
                    for key in (
                        "active_app",
                        "system_volume",
                        "window_apps",
                        "volumes",
                        "output_device_id",
                    )
                )
                if current != last_saved:
                    try:
                        self.ai.store.record_usage(self.ai.user, context)
                        last_saved = current
                        storage_error = None
                    except Exception as error:
                        storage_error = str(error)

                    with self._context_lock:
                        self._storage_error = storage_error
            except Exception as error:
                with self._context_lock:
                    self._detection_error = str(error)

            core.event.wait(2)

    def get_usage_status(self):
        with self._context_lock:
            context = (
                json.loads(json.dumps(self._context))
                if self._context is not None
                else None
            )
            return {
                "context": context,
                "error": self._detection_error,
                "storage_error": self._storage_error,
            }

    def get_ai_proposals(self):
        status = self.get_usage_status()
        if status["error"]:
            return {"proposals": [], "error": status["error"]}

        if status["context"] is None:
            return {"proposals": [], "error": "利用状況を取得中です"}

        return {
            "proposals": self.ai.propose(status["context"]),
            "error": None,
        }

    def reject_ai_proposal(self, suggestion_id):
        self.ai.feedback(suggestion_id=int(suggestion_id), result="rejected")
        return {"ok": True}


def main():
    core = Core()

    try:
        app = IntegratedApp()
        window = DesktopWindow(app, resource_path("app/UI/img"))
        controller = VolumeController(app, core)
        core.start_tasks(
            controller.start_recording,
            lambda: app.monitor_usage(core),
        )

        smoke_result = os.environ.get("VOLUMEAUTO_SMOKE_RESULT")
        window.run(Path(smoke_result) if smoke_result else None)
    finally:
        core.stop()
        core.join_tasks()


if __name__ == "__main__":
    log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "VolumeAdjust"
    log_path = log_dir / "startup.log"

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=log_path, encoding="utf-8", level=logging.INFO)
        logging.info("Starting VolumeAuto")
        main()
    except Exception:
        logging.exception("VolumeAuto startup failed")

        if sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                None,
                f"VolumeAutoを起動できませんでした。\n詳細: {log_path}",
                "VolumeAuto",
                0x10,
            )

        sys.exit(1)
