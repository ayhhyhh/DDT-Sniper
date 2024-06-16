import time
import cv2
import numpy as np
import win32api
import win32con
import win32gui
import win32ui
import os
import PySimpleGUI as sg


def get_capture(handle):
    win32api.PostMessage(handle, win32con.WM_SETFOCUS, 0, 0)
    time.sleep(0.1)
    hwnd_dc = win32gui.GetWindowDC(handle)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    save_bit_map = win32ui.CreateBitmap()
    save_bit_map.CreateCompatibleBitmap(mfc_dc, 1000, 600)
    save_dc.SelectObject(save_bit_map)
    save_dc.BitBlt((0, 0), (1000, 600), mfc_dc, (0, 0), win32con.SRCCOPY)
    signed_ints_array = save_bit_map.GetBitmapBits(True)
    img = np.frombuffer(signed_ints_array, dtype="uint8")
    img.shape = (600, 1000, 4)
    win32gui.DeleteObject(save_bit_map.GetHandle())
    mfc_dc.DeleteDC()
    save_dc.DeleteDC()
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    return img

def get_point(handle):
    def on_EVENT_LBUTTONDOWN(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f'self.click(\'rfind\', pos={(x, y)}, rgb={(img[y][x][2], img[y][x][1], img[y][x][0])})')

    img = get_capture(handle)
    cv2.namedWindow(str(handle))
    cv2.setMouseCallback(str(handle), on_EVENT_LBUTTONDOWN)
    while True:
        cv2.imshow(str(handle), img)
        if cv2.waitKey(0) & 0xFF == 27:
            break
    cv2.destroyWindow(str(handle))

def get_image(handle):
    if not os.path.exists('./image'):
        os.mkdir('./image')
    img = get_capture(handle)
    cv2.namedWindow(str(handle))
    cv2.imshow(str(handle), img)
    rect = cv2.selectROI(str(handle), img, False)
    cv2.destroyWindow(str(handle))
    cropped = img[int(rect[1]):int(rect[1] + rect[3]), int(rect[0]):int(rect[0] + rect[2])]
    if rect is not None:
        image_name = sg.popup_get_text('命名截图(不需要后缀名)')
        if image_name:
            print(f'self.click(\'rfind_image\', img=\'{image_name}\')')
            cv2.imwrite(f'./image/{image_name}.png', cropped)
            return image_name



