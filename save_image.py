from game.service import GameService
from game.player import Player
import cv2
import keyboard
import os
import win32gui


def get_next_image_index(directory, prefix):

    files = os.listdir(directory)
    image_files = [f for f in files if f.startswith(prefix) and f.endswith(".png")]

    indices = []
    for image_file in image_files:
        try:
            index = int(image_file[len(prefix) : -4])
            indices.append(index)
        except ValueError:
            continue

    return max(indices, default=-1) + 1


directory = "./game_image"
prefix = "image_"
key_pressed = False
target_key = "ctrl"
while True:
    handle = win32gui.GetForegroundWindow()
    if (
        GameService.is_game(handle)
        and keyboard.is_pressed(target_key)
        and not key_pressed
    ):
        game = Player(handle)
        image = game.capture()
        next_index = get_next_image_index(directory, prefix)
        file_path = os.path.join(directory, f"{prefix}{next_index}.png")
        cv2.imwrite(file_path, image)
    elif not keyboard.is_pressed(target_key):
        key_pressed = False
