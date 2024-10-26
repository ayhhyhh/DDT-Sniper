import math
import win32gui
import win32api
import pynput
import PySimpleGUI as sg
from threading import Thread
from game.service import GameService
from game.player import Player
from typing import Optional
import time
from utils import is_game
from constant import WINDOW_HEIGHT, WINDOW_WIDTH


import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

layout = [
    [sg.Text("Window: ", key="text-window")],
    [sg.Text("Angle: ", key="text-angle")],
    [sg.Text("Wind: ", key="text-wind")],
    [sg.Text("Location: ", key="text-location")],
    [sg.Text("Distance: ", key="text-distance")],
    [sg.Text("Strength: ", key="text-suggestion")],
    [sg.Checkbox("Manual Mode", key="manual", default=False)],
    [sg.Checkbox("Enable Drawing", key="drawing", default=False)],
    [sg.Button("Exit sniper", key="exit")],
]

window = sg.Window(
    "ddtankSniper",
    layout,
    keep_on_top=True,
    location=(0, 0),
    size=(320, 250),
    no_titlebar=True,
    margins=(0, 0),
    finalize=True,
)

old_handle: int = 0
game: Optional[Player] = None
compute_on: bool = False
manual_on: bool = False


def listen():
    def on_press(key):
        global compute_on, manual_on
        if key == pynput.keyboard.Key.ctrl_l:
            compute_on = True
        if key == pynput.keyboard.Key.alt_l:
            manual_on = True

    def on_release(key):
        global compute_on, manual_on
        if key == pynput.keyboard.Key.ctrl_l:
            compute_on = False
        if key == pynput.keyboard.Key.alt_l:
            manual_on = False

    with pynput.keyboard.Listener(
        on_press=on_press, on_release=on_release
    ) as key_listener:
        key_listener.join()


listen_thread = Thread(target=listen)
listen_thread.daemon = True
listen_thread.start()

while True:
    event, values = window.read(timeout=100)
    if event in (None, "exit"):
        exit()

    enable_drawing = values["drawing"]
    manual = values["manual"]

    handle = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(handle)
    window["text-window"].update(f"Window: {title}")

    if not GameService.is_game(handle):
        window["text-angle"].update("Angle: None")
        window["text-wind"].update("Wind: None")
        window["text-location"].update("Location: None")
        window["text-distance"].update("Distance: None")
        window["text-suggestion"].update("Strength: None")
        time.sleep(0)
        continue

    if handle != old_handle:
        old_handle = handle
        game = Player(handle)
        title = win32gui.GetWindowText(handle)
        window["text-window"].update(f"Window: {title}")

    game.update_setting(manual, enable_drawing)

    if manual and manual_on:
        mouse_pos, game_pos = win32api.GetCursorPos(), win32gui.GetWindowRect(
            game.handle
        )
        pos = ((mouse_pos[0] - game_pos[0]), (mouse_pos[1] - game_pos[1]))
        game.update_circle_manual(pos)

    mouse_pos, game_pos = win32api.GetCursorPos(), win32gui.GetWindowRect(game.handle)
    target_pos = ((mouse_pos[0] - game_pos[0]), (mouse_pos[1] - game_pos[1]))

    if (
        compute_on
        and 0 < target_pos[0] < WINDOW_WIDTH
        and 0 < target_pos[1] < WINDOW_HEIGHT
    ):

        game.update_info(target_pos)
        window["text-angle"].update(f"Angle: {game.angle}")
        window["text-wind"].update(f"Wind: {game.wind}")
        window["text-location"].update(f"Location: {game.circle}")
        window["text-distance"].update(
            f"Distance: {game.distance[0]:.1f}, {game.distance[1]:.1f}"
        )
        window["text-suggestion"].update(f"Suggestion: {game.strength:.1f}")
