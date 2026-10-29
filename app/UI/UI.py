import webview

webview.create_window(
    "My Application",
    "index.html",
    width=600,
    height=500,
    resizable=False
)

webview.start()