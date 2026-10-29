import webview

class API:
    def __init__(self):
        self.volume = 50  # 初期音量を50に設定

    def set_volume(self, value):
        self.volume = value
        print(f"音量が{value}に設定されました。")

    def get_volume(self):
        return self.volume

    def toggle_camera(self):
        print("カメラのトグル操作が呼び出されました。")
        # ここにカメラのトグル操作の処理を追加できます

    def toggle_microphone(self):
        print("マイクのトグル操作が呼び出されました。")
        # ここにマイクのトグル操作の処理を追加できます

webview.create_window(
    "My Application",
    "index.html",
    width=600,
    height=500,
    resizable=False,
    js_api=API()
)

webview.start()

# git push -u origin feature/onishi