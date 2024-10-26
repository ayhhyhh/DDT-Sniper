import cv2
import numpy as np
import keyboard
import cv2
import numpy as np
from scipy import ndimage


def kmeans_color_quantization(image, k=12):
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


# 读取图像
image = cv2.imread("game_image/image_5.png")
roi_y1, roi_y2, roi_x1, roi_x2 = 24, 160, 750, 999
image[roi_y1:roi_y2, roi_x1:roi_x2] = kmeans_color_quantization(
    image[roi_y1:roi_y2, roi_x1:roi_x2]
)

# 显示图像
cv2.imshow("Image", image)


def show_coordinates(event, x, y, flags, param):
    # 只有在按住 Ctrl 键时才输出坐标和颜色
    if event == cv2.EVENT_MOUSEMOVE and keyboard.is_pressed("ctrl"):
        bgr = image[y, x]
        print(f"Coordinates: ({x}, {y}), BGR: {bgr}")


# 设置鼠标回调
cv2.setMouseCallback("Image", show_coordinates)

# 等待按键事件
cv2.waitKey(0)

# 关闭所有窗口
cv2.destroyAllWindows()
