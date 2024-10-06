import math
import win32gui
import win32api
import pynput
import PySimpleGUI as sg
from threading import Thread
from ddtank import Status
from ddtank.utils.aim import operate_calculate_strength
from game.service import GameService
from game.player import Player
from typing import Optional
import time
from utils import is_game

layout = [
    [sg.Text("Window: ", key="text-window")],
    [sg.Text("Angle: ", key="text-angle")],
    [sg.Text("Wind: ", key="text-wind")],
    [sg.Text("Location: ", key="text-location")],
    [sg.Text("Distance: ", key="text-distance")],
    [sg.Text("Suggestion: ", key="text-suggestion")],
    [sg.Button("Exit sniper", key="exit")],
]

window = sg.Window(
    "ddtankSniper",
    layout,
    keep_on_top=True,
    location=(0, 0),
    size=(300, 200),
    no_titlebar=True,
    margins=(0, 0),
)

old_handle: int = 0
game: Optional[Player] = None
on: bool = False


def listen():
    def on_press(key):
        global on
        if key == pynput.keyboard.Key.ctrl_l:
            on = True

    def on_release(key):
        global on
        if key == pynput.keyboard.Key.ctrl_l:
            on = False

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

    handle = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(handle)
    window["text-window"].update(f"Window: {title}")
    if not GameService.is_game(handle):
        window["text-angle"].update("Angle: None")
        window["text-wind"].update("Wind: None")
        window["text-location"].update("Location: None")
        window["text-distance"].update("Distance: None")
        window["text-suggestion"].update("Suggestion: None")
        time.sleep(0)
        continue

    if handle != old_handle:
        old_handle = handle
        game = Player(handle)

        title = win32gui.GetWindowText(handle)
        window["text-window"].update(f"Window: {title}")

    mouse_pos, game_pos = win32api.GetCursorPos(), win32gui.GetWindowRect(game.handle)
    pos = ((mouse_pos[0] - game_pos[0]) / 1000, (mouse_pos[1] - game_pos[1]) / 600)

    if on and 0 < pos[0] < 1 and 0 < pos[1] < 1:

        game.update_info()
        window["text-angle"].update(f"Angle: {game.angle}")
        window["text-wind"].update(f"Wind: {game.wind}")
        window["text-location"].update(f"Location: {game.circle}")
        x = game.box_pos[0] + pos[0] * game.box_width * 10
        y = game.box_pos[1] + pos[1] * game.box_width * 6
        if game.box_width:
            distance = (
                (x - game.circle[0]) / game.box_width,
                -(y - game.circle[1]) / game.box_width,
            )
            window["text-distance"].update(
                f"Distance: {distance[0]:.1f}, {distance[1]:.1f}"
            )

            strength = operate_calculate_strength(
                game.angle,
                game.wind * math.copysign(1, distance[0]),
                abs(distance[0]),
                distance[1],
            )
            window["text-suggestion"].update(f"Suggestion: {strength:.1f}")
