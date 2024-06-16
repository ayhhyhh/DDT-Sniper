"""
create_time: 2023/2/4 14:24
author: TsangHans
"""
from unittest import TestCase
from ddtcv.onnx import ONNXModel
import cv2 as cv


class TestONNXModel(TestCase):
    def test_predict(self):
        m_fp = "../static/model/angle_1_rec_en_number_lite/angle_1_rec_en_number_lite.onnx"
        d_fp = "../static/model/angle_1_rec_en_number_lite/angle_dict.txt"
        m = ONNXModel(m_fp, d_fp)
        img = cv.imread("image/img.png")
        res = m.predict(img)
        assert res == "-18"
