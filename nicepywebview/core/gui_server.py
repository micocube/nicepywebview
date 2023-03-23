import contextlib
import multiprocessing
import os
import sys
import threading
import time
import webbrowser
from contextlib import redirect_stdout
from io import StringIO
import random
import socket
from typing import Optional, List

import uvicorn
from uvicorn.main import STARTUP_FAILURE
from nicegui import globals
import webview
import logging


logger = logging.getLogger(__name__)


class UvicornServer(uvicorn.Server):
    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


class GuiServer:
    def __init__(self, title, debug):
        self.title = title
        self.debug = debug
        self.init_gui()
        self.port = self.get_random_port()

    def init_gui(self):
        pass

    @staticmethod
    def before_thread_start(*,
                            host: str = '0.0.0.0',
                            port: int = 8080,
                            title: str = 'NiceGUI',
                            viewport: str = 'width=device-width, initial-scale=1',
                            favicon: Optional[str] = None,
                            dark: Optional[bool] = False,
                            binding_refresh_interval: float = 0.1,
                            show: bool = True,
                            reload: bool = True,
                            uvicorn_logging_level: str = 'warning',
                            uvicorn_reload_dirs: str = '.',
                            uvicorn_reload_includes: str = '*.py',
                            uvicorn_reload_excludes: str = '.*, .py[cod], .sw.*, ~*',
                            exclude: str = '',
                            tailwind: bool = True,
                            **kwargs,
                            ) -> None:
        """ui.run

        You can call `ui.run()` with optional arguments:

        :param host: start server with this host (default: `'0.0.0.0'`)
        :param port: use this port (default: `8080`)
        :param title: page title (default: `'NiceGUI'`, can be overwritten per page)
        :param viewport: page meta viewport content (default: `'width=device-width, initial-scale=1'`, can be overwritten per page)
        :param favicon: relative filepath or absolute URL to a favicon (default: `None`, NiceGUI icon will be used)
        :param dark: whether to use Quasar's dark mode (default: `False`, use `None` for "auto" mode)
        :param binding_refresh_interval: time between binding updates (default: `0.1` seconds, bigger is more CPU friendly)
        :param show: automatically open the UI in a browser tab (default: `True`)
        :param reload: automatically reload the UI on file changes (default: `True`)
        :param uvicorn_logging_level: logging level for uvicorn server (default: `'warning'`)
        :param uvicorn_reload_dirs: string with comma-separated list for directories to be monitored (default is current working directory only)
        :param uvicorn_reload_includes: string with comma-separated list of glob-patterns which trigger reload on modification (default: `'.py'`)
        :param uvicorn_reload_excludes: string with comma-separated list of glob-patterns which should be ignored for reload (default: `'.*, .py[cod], .sw.*, ~*'`)
        :param exclude: comma-separated string to exclude elements (with corresponding JavaScript libraries) to save bandwidth
          (possible entries: aggrid, audio, chart, colors, interactive_image, joystick, keyboard, log, markdown, mermaid, plotly, scene, video)
        :param tailwind: whether to use Tailwind (experimental, default: `True`)
        :param kwargs: additional keyword arguments are passed to `uvicorn.run`
        """
        globals.ui_run_has_been_called = True
        globals.host = host
        globals.port = port
        globals.reload = reload
        globals.title = title
        globals.viewport = viewport
        globals.favicon = favicon
        globals.dark = dark
        globals.binding_refresh_interval = binding_refresh_interval
        globals.excludes = [e.strip() for e in exclude.split(',')]
        globals.tailwind = tailwind

        if multiprocessing.current_process().name != 'MainProcess':
            return

        if show:
            webbrowser.open(f'http://{host if host != "0.0.0.0" else "127.0.0.1"}:{port}/')

        def split_args(args: str) -> List[str]:
            return [a.strip() for a in args.split(',')]

        # NOTE: The following lines are basically a copy of `uvicorn.run`, but keep a reference to the `server`.

        config = uvicorn.Config(
            'nicegui:app' if reload else globals.app,
            host=host,
            port=port,
            reload=reload,
            reload_includes=split_args(uvicorn_reload_includes) if reload else None,
            reload_excludes=split_args(uvicorn_reload_excludes) if reload else None,
            reload_dirs=split_args(uvicorn_reload_dirs) if reload else None,
            log_level=uvicorn_logging_level,
            **kwargs,
        )
        globals.server = UvicornServer(config=config)

        if (reload or config.workers > 1) and not isinstance(config.app, str):
            logging.warning('You must pass the application as an import string to enable "reload" or "workers".')
            sys.exit(1)

        # if config.should_reload:
        #     sock = config.bind_socket()
        #     ChangeReload(config, target=globals.server.run, sockets=[sock]).run()
        # elif config.workers > 1:
        #     sock = config.bind_socket()
        #     Multiprocess(config, target=globals.server.run, sockets=[sock]).run()
        # else:
        #     globals.server.run()
        if config.uds:
            os.remove(config.uds)  # pragma: py-win32

        if not globals.server.started and not config.should_reload and config.workers == 1:
            sys.exit(STARTUP_FAILURE)

    def start(self):
        self.before_thread_start(show=False, port=self.port)
        with globals.server.run_in_thread():
            stream = StringIO()
            with redirect_stdout(stream):
                window = webview.create_window(self.title, "http://localhost:"+str(self.port))
                window.events.closed += self.on_closed
                webview.start(debug=self.debug)

    def on_closed(self):
        pass

    @staticmethod
    def get_random_port():
        while True:
            port = random.randint(1023, 65535)

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.bind(('localhost', port))
                except OSError:
                    logger.warning('Port %s is in use' % port)
                    continue
                else:
                    return port



