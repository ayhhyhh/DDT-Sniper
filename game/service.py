from ddtcv import Wind, Angle
import numpy as np
import cv2
import win32gui
import win32api
import win32con
import win32ui
import cv2
import numpy as np
import string
import time
import ddtcv

from typing import Union, Literal, Callable, Optional
from threading import Thread
from ctypes import windll


class ReadException(Exception):
    pass


class GameService:

    @staticmethod
    def find_flash_player_window_by_handle(handle) -> int:
        """
        根据给定的窗口句柄，查找符合条件的MacromediaFlashPlayerActiveX子窗口句柄。
        """
        child_hwnd_list = []
        win32gui.EnumChildWindows(
            handle, lambda hwnd, param: param.append(hwnd), child_hwnd_list
        )
        for child_hwnd in child_hwnd_list:
            class_name, shape = win32gui.GetClassName(
                child_hwnd
            ), win32gui.GetWindowRect(child_hwnd)
            height = shape[3] - shape[1]
            weight = shape[2] - shape[0]
            if (
                class_name == "MacromediaFlashPlayerActiveX"
                and weight == 1000
                and height == 600
            ):
                return child_hwnd
        return 0

    @staticmethod
    def is_game(handle) -> bool:
        return GameService.find_flash_player_window_by_handle(handle) != 0

    @staticmethod
    def activate(handle):
        win32api.PostMessage(handle, win32con.WM_SETFOCUS, 0, 0)

    @staticmethod
    def capture(handle, mfc_dc, save_dc, save_bit_map, x=0, y=0, w=1000, h=600):
        GameService.activate(handle)

        save_dc.SelectObject(save_bit_map)
        save_dc.BitBlt((0, 0), (w, h), mfc_dc, (x, y), win32con.SRCCOPY)
        signed_ints_array = save_bit_map.GetBitmapBits(True)
        img = np.frombuffer(signed_ints_array, dtype="uint8")
        img.shape = (h, w, 4)
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

        return img

    @staticmethod
    def read_wind(
        image,
    ):
        """get wind from image

        Args:
            image (2D-Array): The game image

        Returns:
            float: float number of wind, positive means right, negative means left
        """
        b, g, r = image.item(21, 468, 0), image.item(21, 468, 1), image.item(21, 468, 2)
        if b == 252 and g == r and g > 240 and r > 240:
            right = 1
        else:
            right = -1
        try:
            return Wind(image) * right
        except:
            raise ReadException("Can't read wind")

    @staticmethod
    def read_angle(image):
        """get angle from image

        Args:
            image (2D-Array): Game Image

        Returns:
            int: Angel, absolute value
        """
        try:
            return Angle(image)
        except:
            raise ReadException("Can't read angle")

    @staticmethod
    def read_small_map(image):
        """Get the left pos from image

        Args:
            image (2D-Array): Game Image

        Returns:
            int: The left position of the small map
        """
        try:
            return (
                np.argwhere(np.all(image[1, 750:] == [160, 160, 160], axis=-1))[0, 0]
                + 742
            )
        except IndexError:
            raise ReadException("Can't read small map")

    @staticmethod
    def read_white_box(image):
        try:
            map_left_bound = GameService.read_small_map(image)
        except ReadException:
            raise ReadException("Can't read white box")

        img = np.where(
            np.any(image[24:120, map_left_bound:998] != [153, 153, 153], axis=-1),
            0,
            255,
        ).astype("uint8")
        contours, hierarchy = cv2.findContours(
            img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        if len(contours) == 0:
            raise ReadException("Can't read white box, because small map is moving")
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 30:
                white_box_pos = (x, y)
                white_box_width = w / 10
                return white_box_pos, white_box_width

    @staticmethod
    def read_circle(image1, image2):

        map_left_bound = GameService.read_small_map(image1)
        capture_1 = image1[24:120, map_left_bound:998]
        capture_1 = cv2.cvtColor(capture_1, cv2.COLOR_BGR2GRAY)
        capture_2 = image2[24:120, map_left_bound:998]
        capture_2 = cv2.cvtColor(capture_2, cv2.COLOR_BGR2GRAY)
        image = np.where(capture_1 == capture_2, 255, 0).astype("uint8")
        cv2.imshow("1", image)
        contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if 5 < w < 25 or 5 < h < 25:
                self_x = int(x + w / 2)
                self_y = int(y + h / 2)
                return self_x, self_y
        raise ReadException("Can't read circle")