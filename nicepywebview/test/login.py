from nicegui import ui
from nicegui.events import ValueChangeEventArguments
from starlette.responses import RedirectResponse

from nicepywebview.core.gui_server import GuiServer
import uuid
from typing import Dict

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from nicegui import app, ui

app.add_middleware(SessionMiddleware, secret_key='some_random_string')  # use your own secret key here

# in reality users and session_info would be persistent (e.g. database, file, ...) and passwords obviously hashed
users = [('user1', 'pass1'), ('user2', 'pass2')]
session_info: Dict[str, Dict] = {}


def is_authenticated(request: Request) -> bool:
    return session_info.get(request.session.get('id'), {}).get('authenticated', False)


@ui.page('/')
def main_page(request: Request) -> None:
    if not is_authenticated(request):
        return RedirectResponse('/login')
    session = session_info[request.session['id']]
    with ui.column().classes('absolute-center items-center'):
        ui.label(f'Hello {session["username"]}!').classes('text-2xl')
        # NOTE we navigate to a new page here to be able to modify the session cookie (it is only editable while a request is en-route)
        # see https://github.com/zauberzeug/nicegui/issues/527 for more details
        ui.button('', on_click=lambda: ui.open('/logout')).props('outline round icon=logout')


@ui.page('/login')
def login(request: Request) -> RedirectResponse:
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        if (username.value, password.value) in users:
            session_info[request.session['id']] = {'username': username.value, 'authenticated': True}
            ui.open('/')
        else:
            ui.notify('Wrong username or password', color='negative')

    if is_authenticated(request):
        return RedirectResponse('/')
    request.session['id'] = str(uuid.uuid4())  # NOTE this stores a new session ID in the cookie of the client
    with ui.card().classes('absolute-center'):
        username = ui.input('Username').on('keydown.enter', try_login)
        password = ui.input('Password').props('type=password').on('keydown.enter', try_login)
        ui.button('Log in', on_click=try_login)


@ui.page('/logout')
def logout(request: Request) -> RedirectResponse:
    if is_authenticated(request):
        session_info.pop(request.session['id'])
        request.session['id'] = None
        return RedirectResponse('/login')
    return RedirectResponse('/')


if __name__ == '__main__':
    server = GuiServer("FirstApplication", False)
    server.start()
