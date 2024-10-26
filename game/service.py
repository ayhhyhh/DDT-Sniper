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

import math
import numpy as np
from scipy.optimize import fsolve

from typing import Union, Literal, Callable, Optional
from threading import Thread
from ctypes import windll
from constant import *
import logging

logger = logging.getLogger(__name__)


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
            width = shape[2] - shape[0]
            if (
                class_name == "MacromediaFlashPlayerActiveX"
                and width == WINDOW_WIDTH
                and height == WINDOW_HEIGHT
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
    def capture(
        handle, mfc_dc, save_dc, save_bit_map, x=0, y=0, w=WINDOW_WIDTH, h=WINDOW_HEIGHT
    ) -> np.ndarray:

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
    ) -> float | None:
        """get wind from image

        Args:
            image (2D-Array): The game image

        Returns:
            float: float number of wind, positive means right, negative means left
        """

        b, g, r = image[WIND_DIRECTION_POINT]
        right = 1 if b == 252 and g == r and g > 240 and r > 240 else -1

        try:
            return Wind(image) * right
        except Exception as e:
            logger.info("Wind reading failed: %s", e)
            return None

    @staticmethod
    def read_angle(image) -> int | None:
        """get angle from image

        Args:
            image (2D-Array): Game Image

        Returns:
            int: Angel, absolute value
        """
        try:
            return Angle(image)
        except Exception as e:
            logger.info("Wind reading failed: %s", e)
            return None

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
                np.argwhere(np.all(image[1, 750:] == SMALL_MAP_BAR_COLOR, axis=-1))[
                    0, 0
                ]
                + 742
            )
        except IndexError:
            logger.info("Can't Find Small Map Left Bound.")

    @staticmethod
    def read_white_box(
        image,
    ) -> tuple[tuple[int, int], tuple[int, int]] | tuple[None, None]:
        """
        Detect the position and width of the white box in the game image.

        Args:
            image (2D-Array): The game image containing the small map.

        Returns:
            tuple[tuple[int, int], tuple[int, int]] | tuple[None, None]: The (x, y) position of the white box and its scaled width,
                                    or None if no white box is detected.
        """

        # Extract the region of interest from the image
        left_bound = GameService.read_small_map(image)
        roi_image = image[
            WHITE_BOX_ROI["start_row"] : WHITE_BOX_ROI["end_row"],
            left_bound : WHITE_BOX_ROI["end_col"],
        ]

        # Create a binary mask where pixels matching WHITE_BOX_COLOR are set to 255, others to 0
        binary_image = (np.all(roi_image == WHITE_BOX_COLOR, axis=-1) * 255).astype(
            "uint8"
        )

        # Find contours in the binary image
        contours, _ = cv2.findContours(
            binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        # Iterate through the contours to find the white box
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 30:
                return (x, y), (w, h)

        # If no contours are found, log the information and return None
        if not contours:
            logging.warning("No white box detected;")
        return None, None

    @staticmethod
    def read_circle(image1, image2):

        map_left_bound = GameService.read_small_map(image1)
        capture_1 = image1[
            WHITE_BOX_ROI["start_row"] : WHITE_BOX_ROI["end_row"],
            map_left_bound : WHITE_BOX_ROI["end_col"],
        ]
        capture_1 = cv2.cvtColor(capture_1, cv2.COLOR_RGB2GRAY)
        capture_2 = image2[
            WHITE_BOX_ROI["start_row"] : WHITE_BOX_ROI["end_row"],
            map_left_bound : WHITE_BOX_ROI["end_col"],
        ]
        capture_2 = cv2.cvtColor(capture_2, cv2.COLOR_RGB2GRAY)
        image = np.where(capture_1 == capture_2, 255, 0).astype("uint8")

        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        image = cv2.medianBlur(image, 5)
        image = cv2.Canny(image, 50, 100)

        def fit_circle_to_contours(image, contours):
            detected_circles = []
            for contour in contours:
                if len(contour) >= 5:  # At least 5 points are needed to fit an ellipse
                    (x, y), radius = cv2.minEnclosingCircle(contour)
                    if 4 < radius < 15:
                        detected_circles.append((int(x), int(y), int(radius)))
            return detected_circles

        contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        detected_circles = fit_circle_to_contours(image, contours)
        for x, y, radius in detected_circles:
            logger.info(f"Detected circle at ({x}, {y}) with radius {radius}")
            return x, y

        return None, None

    def operate_calculate_strength(angel, wind, dx, dy):
        if not dx:
            return 0
        if angel > 90:
            angel = 180 - angel
        r, w, g = [0.90289815, 6.33592869, -184.11666458]
        shot_angel = angel
        position_angel = math.atan(dy / dx)
        position_angel = position_angel * 180 / math.pi
        x_angel = shot_angel - position_angel
        y_angel = 90 - shot_angel + position_angel
        x_angel = x_angel * math.pi / 180
        y_angel = y_angel * math.pi / 180
        position_angel = position_angel * math.pi / 180

        def solve(F):
            vx = math.cos(x_angel) * F
            vy = math.cos(y_angel) * F
            fx = math.cos(position_angel) * w * wind + math.sin(position_angel) * g
            fy = -math.sin(position_angel) * w * wind + math.cos(position_angel) * g

            def computePosition(v0, f, r, t):
                temp = f - r * v0
                ert = np.power(math.e, -r * t)
                right = temp * ert + f * r * t - temp
                return right / (r * r)

            def getTime(v0):
                solve_l = lambda t1: computePosition(v0, fy, r, t1)
                time = fsolve(solve_l, [2])
                assert time[0] != 0
                return time[0]

            t = getTime(vy)
            return computePosition(vx, fx, r, t) - math.sqrt(dx**2 + dy**2)

        f = fsolve(solve, [100])
        if f[0] > 100:
            return 100.0
        elif f[0] < 0:
            return 0.0
        return f[0]
