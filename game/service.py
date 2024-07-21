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
    def get_game() -> dict:
        """
        注意，我们会获取所有1000*600的MacromediaFlashPlayerActiveX类子窗口句柄
        对于这些窗口是否能够成功截图或模拟操作，应该由您自己来确认
        因此，我们建议您使用流行的登陆器来执行游戏脚本

        Args:
            None

        Returns:
            dict: {窗口名: 游戏子窗口句柄(int)}

        """
        parent_hwnd_list, games = [], {}
        win32gui.EnumWindows(lambda hwnd, param: param.append(hwnd), parent_hwnd_list)
        for parent_hwnd in parent_hwnd_list:
            if win32gui.IsWindowVisible(parent_hwnd):
                child_hwnd_list = []
                win32gui.EnumChildWindows(
                    parent_hwnd, lambda hwnd, param: param.append(hwnd), child_hwnd_list
                )
                for child_hwnd in child_hwnd_list:
                    class_name = win32gui.GetClassName(child_hwnd)
                    if class_name == "MacromediaFlashPlayerActiveX":
                        shape = win32gui.GetWindowRect(child_hwnd)
                        height = shape[3] - shape[1]
                        weight = shape[2] - shape[0]
                        if weight == 1000 and height == 600:
                            games[win32gui.GetWindowText(parent_hwnd)] = child_hwnd
        return games

    def get_game_by_title(title_substring: str) -> int:
        """
        通过窗口标题的部分字符串来获取游戏窗口句柄

        Args:
            str: substring in window title

        Returns:
            int: specific window handle, if not exist, return 0

        """
        hwnd_dict = GameService.get_game()
        print(hwnd_dict)
        for k, v in hwnd_dict.items():
            if title_substring in k:
                return v
        return 0

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
        cv2.imshow("Image", img)
        contours, hierarchy = cv2.findContours(
            img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        print(contours)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 30:
                white_box_pos = (x, y)
                white_box_width = w / 10
                return white_box_pos, white_box_width
        return None

    @staticmethod
    def read_circle(image1, image2):

        map_left_bound = GameService.read_small_map(image)
        capture_1 = image1[map_left_bound, 24, 998 - map_left_bound, 120 - 24]
        capture_1 = cv2.cvtColor(capture_1, cv2.COLOR_BGR2GRAY)

        capture_2 = image2[map_left_bound, 24, 998 - map_left_bound, 120 - 24]
        capture_2 = cv2.cvtColor(capture_2, cv2.COLOR_BGR2GRAY)
        image = np.where(capture_1 == capture_2, 255, 0).astype("uint8")
        contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # 这里可能self_x, self_y没有定义
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if 15 < w < 25 or 15 < h < 25 and w == h:
                self_x = int(x + w / 2)
                self_y = int(y + h / 2)
                return self_x, self_y

        return (self_x, self_y)
