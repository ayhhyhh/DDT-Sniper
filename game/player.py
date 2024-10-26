from game.service import GameService
import win32gui, win32ui, win32con
import time
import logging
import numpy as np
from constant import *
import math

logger = logging.getLogger(__name__)


class HandleError(Exception):
    pass


class Player:
    def __init__(self, parent_handle: str) -> None:
        self.parent_handle = parent_handle
        self.handle = GameService.find_flash_player_window_by_handle(parent_handle)
        if not self.handle:
            raise HandleError("The handle is not a game window")

        w, h = (1000, 600)
        self.hwnd_dc = win32gui.GetWindowDC(self.handle)
        self.mfc_dc = win32ui.CreateDCFromHandle(self.hwnd_dc)
        self.save_dc = self.mfc_dc.CreateCompatibleDC()
        self.save_bit_map = win32ui.CreateBitmap()
        self.save_bit_map.CreateCompatibleBitmap(self.mfc_dc, w, h)

        self.manual = False
        self.drawing = False

        self.wind = 0
        self.angle = 0
        self.map_left_bound = 0
        self.box_pos = (0, 0)
        self.box_size = (0, 0)
        self.circle = (0, 0)
        self.distance = (0, 0)
        self.strength = 0.0

    def update_setting(self, manual: bool, drawing: bool):
        self.manual = manual
        self.drawing = drawing

    def update_circle_manual(self, mouse_pos):
        self.update_info()
        self.circle = (
            int(mouse_pos[0] / WINDOW_WIDTH * self.box_size[0] + self.box_pos[0]),
            int(mouse_pos[1] / WINDOW_HEIGHT * self.box_size[1] + self.box_pos[1]),
        )

    def update_info(self, target_pos: tuple[int, int] = None):
        image = GameService.capture(
            self.handle, self.mfc_dc, self.save_dc, self.save_bit_map
        )
        try:
            wind = GameService.read_wind(image)
            if wind is not None:
                self.wind = wind

            angle = GameService.read_angle(image)
            if angle is not None:
                self.angle = angle

            map_left_bound = GameService.read_small_map(image)
            if map_left_bound is not None:
                self.map_left_bound = map_left_bound

            box_pos, box_size = GameService.read_white_box(image)
            if box_pos is not None and box_size is not None:
                self.box_pos = box_pos
                self.box_size = box_size

            if self.manual:
                pass
            else:
                image1 = GameService.capture(
                    self.handle, self.mfc_dc, self.save_dc, self.save_bit_map
                )
                self.__sleep(100)
                image2 = GameService.capture(
                    self.handle, self.mfc_dc, self.save_dc, self.save_bit_map
                )
                circle = GameService.read_circle(image1, image2)
                if circle is not None:
                    self.circle = circle

            x = self.box_pos[0] + target_pos[0] / WINDOW_WIDTH * self.box_size[0]
            y = self.box_pos[1] + target_pos[1] / WINDOW_HEIGHT * self.box_size[1]

            distance = (
                (x - self.circle[0]) / self.box_size[0] * 10,
                -(y - self.circle[1]) / self.box_size[1] * 10,
            )
            self.distance = distance
            self.strength = GameService.operate_calculate_strength(
                self.angle,
                self.wind * math.copysign(1, distance[0]),
                abs(distance[0]),
                distance[1],
            )

        except Exception as e:
            logger.exception(e)

    def capture(self) -> np.ndarray:
        """Capture the game window, return RGB image."""
        return GameService.capture(
            self.handle, self.mfc_dc, self.save_dc, self.save_bit_map
        )

    @staticmethod
    def __sleep(period: int):
        time.sleep(period / 1000)

    def destroy(self):
        win32gui.DeleteObject(self.save_bit_map.GetHandle())
        self.mfc_dc.DeleteDC()
        self.save_dc.DeleteDC()
        win32gui.ReleaseDC(self.handle, self.hwnd_dc)
