import webview
from nicegui import ui

from core.gui_server import GuiServer

if __name__ == '__main__':
    ui.label("Hello World")
    ui.button("click me", on_click=lambda: ui.notify("clicked button"))
    server = GuiServer("FirstApplication", False)
    server.start()
