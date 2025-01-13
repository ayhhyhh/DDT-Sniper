import sys
import math
import win32gui
import win32api
import pynput
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox
from PyQt5.QtCore import Qt, QTimer
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

class DDTankSniper(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        self.old_handle: int = 0
        self.game: Optional[Player] = None
        self.compute_on: bool = False
        self.manual_on: bool = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_window)
        self.timer.start(100)

        self.listen_thread = Thread(target=self.listen)
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def init_ui(self):
        self.setWindowTitle("ddtankSniper")
        self.setGeometry(100, 100, 320, 250)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.layout = QVBoxLayout()

        self.label_window = QLabel("Window: ")
        self.label_angle = QLabel("Angle: ")
        self.label_wind = QLabel("Wind: ")
        self.label_location = QLabel("Location: ")
        self.label_distance = QLabel("Distance: ")
        self.label_suggestion = QLabel("Strength: ")

        self.checkbox_manual = QCheckBox("Manual Mode")
        self.checkbox_drawing = QCheckBox("Enable Drawing")

        self.exit_button = QPushButton("Exit Sniper")
        self.exit_button.clicked.connect(self.close)

        self.layout.addWidget(self.label_window)
        self.layout.addWidget(self.label_angle)
        self.layout.addWidget(self.label_wind)
        self.layout.addWidget(self.label_location)
        self.layout.addWidget(self.label_distance)
        self.layout.addWidget(self.label_suggestion)
        self.layout.addWidget(self.checkbox_manual)
        self.layout.addWidget(self.checkbox_drawing)
        self.layout.addWidget(self.exit_button)

        self.setLayout(self.layout)

    def listen(self):
        def on_press(key):
            if key == pynput.keyboard.Key.ctrl_l:
                self.compute_on = True
            if key == pynput.keyboard.Key.alt_l:
                self.manual_on = True

        def on_release(key):
            if key == pynput.keyboard.Key.ctrl_l:
                self.compute_on = False
            if key == pynput.keyboard.Key.alt_l:
                self.manual_on = False

        with pynput.keyboard.Listener(on_press=on_press, on_release=on_release) as key_listener:
            key_listener.join()

    def update_window(self):
        enable_drawing = self.checkbox_drawing.isChecked()
        manual = self.checkbox_manual.isChecked()

        handle = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(handle)
        self.label_window.setText(f"Window: {title}")

        if not GameService.is_game(handle):
            self.label_angle.setText("Angle: None")
            self.label_wind.setText("Wind: None")
            self.label_location.setText("Location: None")
            self.label_distance.setText("Distance: None")
            self.label_suggestion.setText("Strength: None")
            return

        if handle != self.old_handle:
            self.old_handle = handle
            self.game = Player(handle)
            self.label_window.setText(f"Window: {title}")

        self.game.update_setting(manual, enable_drawing)

        if manual and self.manual_on:
            mouse_pos, game_pos = win32api.GetCursorPos(), win32gui.GetWindowRect(self.game.handle)
            pos = ((mouse_pos[0] - game_pos[0]), (mouse_pos[1] - game_pos[1]))
            self.game.update_circle_manual(pos)

        mouse_pos, game_pos = win32api.GetCursorPos(), win32gui.GetWindowRect(self.game.handle)
        target_pos = ((mouse_pos[0] - game_pos[0]), (mouse_pos[1] - game_pos[1]))

        if self.compute_on and 0 < target_pos[0] < WINDOW_WIDTH and 0 < target_pos[1] < WINDOW_HEIGHT:
            self.game.update_info(target_pos)
            self.label_angle.setText(f"Angle: {self.game.angle}")
            self.label_wind.setText(f"Wind: {self.game.wind}")
            self.label_location.setText(f"Location: {self.game.circlePosition}")
            self.label_distance.setText(f"Distance: {self.game.distance[0]:.1f}, {self.game.distance[1]:.1f}")
            self.label_suggestion.setText(f"Suggestion: {self.game.strength:.1f}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    sniper = DDTankSniper()
    sniper.show()
    sys.exit(app.exec_())
