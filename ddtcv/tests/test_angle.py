"""
create_time: 2023/2/4 14:54
author: TsangHans
"""
from unittest import TestCase
from ddtcv import Angle, save_angle_image
import cv2 as cv


class Test(TestCase):
    def test_angle(self):
        x = cv.imread("image/img2.png")
        res = Angle(x)
        assert res == 49

    def test_save_angle_image(self):
        x = cv.imread("image/img2.png")
        save_angle_image("image/img2_angle.png", x)
