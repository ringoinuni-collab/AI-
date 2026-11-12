
import tkinter as tk
from tkinter import ttk


class DesktopWindow:
    def __init__(self, app, image_dir):
        self.app = app
        self.root = tk.Tk()
        self.root.title("VolumeAuto — 音量調整アプリ")
        self.root.geometry("700x520")
        self.root.minsize(440, 380)

        body = ttk.Frame(self.root, padding=20)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="VolumeAuto", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        self.volume = tk.DoubleVar(value=app.get_volume())
        ttk.Label(body, text="音量").pack(anchor="w", pady=(12, 0))
        ttk.Scale(
            body,
            from_=0,
            to=100,
            variable=self.volume,
            command=self.set_volume,
        ).pack(fill="x")
        self.status = ttk.Label(body)
        self.status.pack(anchor="w")

        controls = ttk.Frame(body)
        controls.pack(fill="x", pady=14)
        self.buttons = []

        for event, icon, name, toggle in (
            (app.adj, "adjustments", "自動調整", app.toggle_adj),
            (app.mic, "microphone", "マイク", app.toggle_mic),
            (app.cam, "camera", "カメラ", app.toggle_cam),
        ):
            images = tuple(
                tk.PhotoImage(file=image_dir / f"{icon}{suffix}.png").subsample(7)
                for suffix in ("-off", "")
            )
            button = tk.Button(
                controls,
                text=name,
                image=images[0],
                compound="left",
                command=toggle,
                bg="#262626",
                fg="white",
                activebackground="#444444",
                activeforeground="white",
            )
            button.pack(side="left", padx=(0, 8))
            self.buttons.append((button, event, images))

        ttk.Label(
            body,
            text="利用中のアプリ",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")
        self.usage = ttk.Label(body, text="利用状況を取得中…")
        self.usage.pack(anchor="w")

        self.apps = ttk.Treeview(body, columns=("name", "volume"), show="headings")
        self.apps.heading("name", text="アプリ")
        self.apps.heading("volume", text="音量")
        self.apps.column("volume", width=140, stretch=False)
        self.apps.pack(fill="both", expand=True, pady=(8, 0))

        self.displayed_context = None

    def set_volume(self, value):
        volume = round(float(value))
        try:
            self.app.now_volume = volume
            self.app.set_volume(volume)
        except OSError as error:
            self.status.config(text=f"音量を変更できませんでした: {error}")
            return

        self.status.config(text=f"{volume}%")

    def refresh(self):
        for button, event, images in self.buttons:
            button.config(
                image=images[event.is_on],
                relief="sunken" if event.is_on else "raised",
            )

        status = self.app.get_usage_status()
        context = status["context"]

        if status["error"]:
            self.usage.config(text=f"取得エラー: {status['error']}")
        elif context:
            level = context["system_volume"]
            level_text = f"{level}%" if level is not None else "取得できません"
            self.usage.config(
                text=status["storage_error"]
                or f"前面: {context['active_app'] or '—'} ／ PC音量: {level_text}"
            )

            if context != self.displayed_context:
                self.apps.delete(*self.apps.get_children())
                volumes = context["volumes"]

                for name in sorted(set(context["window_apps"]) | volumes.keys()):
                    value = f"{volumes[name]:.0f}%" if name in volumes else "—"
                    self.apps.insert("", "end", values=(name, value))

                self.displayed_context = context

        self.root.after(200, self.refresh)

    def run(self, smoke_result=None):
        self.status.config(text=f"{self.app.get_volume()}%")
        self.refresh()

        if smoke_result:
            def verify_window():
                if self.root.winfo_viewable() and self.displayed_context is not None:
                    smoke_result.write_text("ok\n", encoding="utf-8")
                    self.root.destroy()
                else:
                    self.root.after(100, verify_window)

            self.root.after(100, verify_window)
            self.root.after(15000, self.root.destroy)

        self.root.mainloop()
