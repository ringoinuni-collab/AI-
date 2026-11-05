
"""担当C：利用状況判定"""

from datetime import datetime


CATEGORIES = {
    "call": {
        "discord.exe",
        "teams.exe",
        "ms-teams.exe",
        "zoom.exe",
    },
    "music": {
        "spotify.exe",
        "musicbee.exe",
        "itunes.exe",
    },
    "video": {
        "vlc.exe",
        "mpv.exe",
    },
    "game": {
        "valorant-win64-shipping.exe",
        "r5apex.exe",
        "overwatch.exe",
        "league of legends.exe",
        "fortniteclient-win64-shipping.exe",
    },
}


def normalize(name):
    """パスや大文字・小文字の違いを統一する。"""
    return (
        str(name)
        .replace("\\", "/")
        .rsplit("/", 1)[-1]
        .lower()
    )


class SituationDetector:
    def __init__(self, overrides=None):
        self.overrides = {
            normalize(name): category
            for name, category in (overrides or {}).items()
        }

        self.previous = None

    def classify(self, name):
        """アプリを分類する。"""
        name = normalize(name)

        if name in self.overrides:
            return self.overrides[name]

        for category, applications in CATEGORIES.items():
            if name in applications:
                return category

        return "other"

    def snapshot(self, raw, now=None):
        """
        担当Aの取得結果を、AIに渡せる形式へ変換する。

        rawの音量は0〜100で指定する。
        """
        now = now or datetime.now().astimezone()

        applications = sorted({
            normalize(name)
            for name in raw.get("running_apps", [])
            if name
        })

        categories = {
            name: self.classify(name)
            for name in applications
        }

        kinds = set(categories.values()) - {"other"}

        scene = "_and_".join(sorted(kinds)) or "other"

        hour = now.hour

        if hour < 6:
            period = "late_night"
        elif hour < 12:
            period = "morning"
        elif hour < 18:
            period = "afternoon"
        else:
            period = "night"

        volumes = {}

        for name, value in raw.get("volumes", {}).items():
            if value is None:
                continue

            value = float(value)

            if not 0 <= value <= 100:
                raise ValueError(
                    "音量は0〜100で渡してください"
                )

            volumes[normalize(name)] = value

        result = {
            "time": now.isoformat(),
            "hour": hour,
            "weekday": now.weekday(),
            "period": period,
            "running_apps": applications,
            "categories": categories,
            "active_app": normalize(
                raw.get("active_app") or ""
            ),
            "scene": scene,
            "output_device": raw.get(
                "output_device",
                "unknown",
            ),
            "output_device_id": raw.get(
                "output_device_id",
                "unknown",
            ),
            "volumes": volumes,
            "playing": raw.get("playing", {}),
            "call_status": raw.get(
                "call_status",
                "unknown",
            ),
            "warnings": raw.get("warnings", []),
        }

        watched_keys = (
            "running_apps",
            "active_app",
            "output_device_id",
            "call_status",
        )

        result["changes"] = [
            key
            for key in watched_keys
            if self.previous is not None
            and result[key] != self.previous[key]
        ]

        self.previous = result

        return result


class WindowsProvider:
    """
    担当Aの処理が未接続の場合に使う取得処理。

    Discordの起動と実際の通話中は区別する。
    この処理では通話状態はunknownとして返す。
    """

    def collect(self):
        import sys

        if sys.platform != "win32":
            raise RuntimeError(
                "Windows用の取得処理です"
            )

        import ctypes
        from ctypes import wintypes

        import comtypes
        import psutil
        from pycaw.pycaw import AudioUtilities

        result = {
            "running_apps": [],
            "volumes": {},
            "playing": {},
            "warnings": [],
        }

        process_names = {}

        for process in psutil.process_iter(
            ["pid", "name"]
        ):
            name = process.info.get("name")

            if name:
                process_names[
                    process.info["pid"]
                ] = normalize(name)

        result["running_apps"] = list(
            process_names.values()
        )

        user32 = ctypes.WinDLL(
            "user32",
            use_last_error=True,
        )

        user32.GetForegroundWindow.restype = (
            wintypes.HWND
        )

        user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]

        process_id = wintypes.DWORD()

        user32.GetWindowThreadProcessId(
            user32.GetForegroundWindow(),
            ctypes.byref(process_id),
        )

        result["active_app"] = process_names.get(
            process_id.value,
            "",
        )

        comtypes.CoInitialize()

        try:
            device = AudioUtilities.GetSpeakers()

            result["output_device_id"] = str(
                device.id
            )

            # 名前だけでは機器の種類を断定しない。
            result["output_device"] = "unknown"

            for session in (
                AudioUtilities.GetAllSessions()
            ):
                try:
                    if not session.Process:
                        continue

                    name = normalize(
                        session.Process.name()
                    )

                    volume = (
                        session.SimpleAudioVolume
                        .GetMasterVolume()
                        * 100
                    )

                    if (
                        name in result["volumes"]
                        and result["volumes"][name]
                        != volume
                    ):
                        result["warnings"].append(
                            f"{name}: "
                            "複数セッションの音量が"
                            "異なります"
                        )

                    result["volumes"][name] = volume

                    # Activeセッションでも、
                    # 実際に発音しているとは限らない。
                    result["playing"][name] = None

                except (
                    psutil.Error,
                    OSError,
                ) as error:
                    result["warnings"].append(
                        type(error).__name__
                    )

        except Exception as error:
            result["warnings"].append(
                f"音声取得失敗: {error}"
            )

        finally:
            comtypes.CoUninitialize()

        return result
