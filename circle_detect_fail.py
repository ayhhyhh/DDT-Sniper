import cv2
import numpy as np
from collections import defaultdict


def kmeans_color_quantization(image, k=50):
    # 将图像转换为二维数组
    data = image.reshape((-1, 3)).astype(np.float32)

    # 设置 K-means 聚类的终止条件
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)

    # 使用 K-means 聚类
    _, labels, centers = cv2.kmeans(
        data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
    )

    # 将中心值转换回 uint8
    centers = np.uint8(centers)

    # 重构图像，像素值替换为其聚类中心的值
    quantized_image = centers[labels.flatten()]
    quantized_image = quantized_image.reshape(image.shape)

    return quantized_image


def detect_candidates(image):
    """检测单帧中的所有候选圆点，并返回它们的中心坐标和颜色"""
    candidates = []
    # 定义感兴趣的区域（ROI）
    roi_y1, roi_y2, roi_x1, roi_x2 = 24, 160, 750, 999
    roi_full = image[roi_y1:roi_y2, roi_x1:roi_x2]

    # 统计所有颜色及其频率
    color_counts = defaultdict(int)
    for i in range(roi_full.shape[0]):
        for j in range(roi_full.shape[1]):
            color = tuple(roi_full[i, j])
            color_counts[color] += 1

    # 过滤掉那些出现频率过低或过高的颜色
    min_frequency = 20
    max_frequency = 100
    filtered_colors = [
        color
        for color, count in color_counts.items()
        if min_frequency < count < max_frequency
    ]

    # 对每种颜色分别进行检测
    for color in filtered_colors:
        lower_bound = np.array([color[0] - 5, color[1] - 5, color[2] - 5])
        upper_bound = np.array([color[0] + 5, color[1] + 5, color[2] + 5])
        mask = cv2.inRange(roi_full, lower_bound, upper_bound)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)

            # 过滤掉半径过小的轮廓
            if radius <= 1:
                continue

            contour_area = cv2.contourArea(contour)
            circle_area = np.pi * (radius**2)
            # print(f"Contour area: {contour_area}, Circle area: {circle_area}, (x, y): ({x}, {y}), radius: {radius}")
            # 确保轮廓接近圆形且半径在范围内
            if 0.2 < contour_area / circle_area < 5 and 3 <= radius <= 15:
                # 使用 NumPy 索引直接获取圆内像素的颜色
                y_indices, x_indices = np.ogrid[: mask.shape[0], : mask.shape[1]]
                mask_circle = (x_indices - center[0]) ** 2 + (
                    y_indices - center[1]
                ) ** 2 <= radius**2
                masked_pixels = roi_full[mask_circle]

                color_variance = np.var(masked_pixels, axis=0)
                variance_threshold = 300
                # if np.mean(color_variance) < variance_threshold:
                overall_center = (center[0] + roi_x1, center[1] + roi_y1)
                print(
                    f"Contour area: {contour_area}, Circle area: {circle_area}, (x, y): ({x}, {y}), radius: {radius}"
                )
                candidates.append((overall_center, color))

    print("=" * 20)
    for candidate in candidates:
        print(f"Center: {candidate[0]}, Color: {candidate[1]}")
    print("=" * 20)
    return candidates


def detect_ring_around_point(frame, point, radius_range=(4, 15)):
    """检测某个点周围是否存在符合要求的圆环"""
    x, y = point
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 定义一个10x10的感兴趣区域（ROI），确保ROI不超出图像边界
    roi_size = 10
    roi_x1 = max(x - roi_size, 0)
    roi_x2 = min(x + roi_size, gray.shape[1])
    roi_y1 = max(y - roi_size, 0)
    roi_y2 = min(y + roi_size, gray.shape[0])

    roi = gray[roi_y1:roi_y2, roi_x1:roi_x2]

    # 使用霍夫圆变换检测圆环
    circles = cv2.HoughCircles(
        roi,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=5,
        param1=50,
        param2=10,  # 参数2越小，检测更敏感，可以根据需要调整
        minRadius=radius_range[0],
        maxRadius=radius_range[1],
    )

    # 如果检测到圆环
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            center = (circle[0] + roi_x1, circle[1] + roi_y1)
            radius = circle[2]
            # 判断检测到的圆环是否符合要求
            if radius >= 5:
                print(f"Detected ring at {center} with radius {radius}")
                return True

    return False


from game.service import GameService
from game.player import Player
import cv2
import keyboard
import os
import win32gui

key_pressed = False
target_key = "ctrl"
while True:
    handle = win32gui.GetForegroundWindow()
    if GameService.is_game(handle) and keyboard.is_pressed(target_key):
        if True or not key_pressed:
            key_pressed = True  # 标志位设置为 True，避免重复触发

            game = Player(handle)
            frame = game.capture()
            roi_y1, roi_y2, roi_x1, roi_x2 = 24, 160, 750, 999
            frame[roi_y1:roi_y2, roi_x1:roi_x2] = kmeans_color_quantization(
                frame[roi_y1:roi_y2, roi_x1:roi_x2]
            )
            # 检测当前帧中的所有候选圆点
            candidates = detect_candidates(frame)

            # 检测每个候选圆点周围是否有圆环
            for candidate in candidates:
                center, color = candidate
                if detect_ring_around_point(frame, center):
                    cv2.circle(frame, center, 5, (0, 255, 0), -1)
                    print(f"Detected character at {center} with primary color {color}")

            # 显示当前帧
            cv2.imshow("Frame", frame)

            # 如果按下 'q' 键，则退出循环
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # 重置按键状态，当按键松开后允许下一次触发
    elif not keyboard.is_pressed(target_key):
        key_pressed = False

# 释放所有窗口
cv2.destroyAllWindows()
