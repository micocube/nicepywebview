import webview
from nicegui import ui
from multiprocessing import Process
from time import sleep

def start_webview():
    sleep(1)
    window = webview.create_window('Hello', url='http://127.0.0.1:8080')
    webview.start(debug=True, private_mode=False)

if __name__ in '__main__':
    t = Process(target=start_webview)
    t.start()

ui.label("Hello World")
ui.button("click me", on_click=lambda: ui.notify("clicked button"))
ui.run(port=8080, show=False)