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
from ddtank.utils.stop_thread import stop_thread
from ddtank.utils.get_game import get_game

VkKeyScanA = windll.user32.VkKeyScanA

keycode_dict = {
    "back": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "pause": 0x13,
    "capital": 0x14,
    "esc": 0x1B,
    "space": 0x20,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "print": 0x2A,
    "snapshot": 0x2C,
    "insert": 0x2D,
    "delete": 0x2E,
    "lwin": 0x5B,
    "rwin": 0x5C,
    "numpad0": 0x60,
    "numpad1": 0x61,
    "numpad2": 0x62,
    "numpad3": 0x63,
    "numpad4": 0x64,
    "numpad5": 0x65,
    "numpad6": 0x66,
    "numpad7": 0x67,
    "numpad8": 0x68,
    "numpad9": 0x69,
    "multiply": 0x6A,
    "add": 0x6B,
    "separator": 0x6C,
    "subtract": 0x6D,
    "decimal": 0x6E,
    "divide": 0x6F,
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
    "numlock": 0x90,
    "scroll": 0x91,
    "lshift": 0xA0,
    "rshift": 0xA1,
    "lcontrol": 0xA2,
    "rcontrol": 0xA3,
    "lmenu": 0xA4,
    "rmenu": 0XA5
}

def get_keycode(key: str) -> int:
    """
    获取按键的键值
    :param key: 按键的名称
    :return: 按键的键值，如果没有找到该键键值，返回-1
    """
    key = key.lower()
    if len(key) == 1 and key in string.printable:
        return VkKeyScanA(ord(key)) & 0xff
    elif key in keycode_dict.keys():
        return keycode_dict[key]
    else:
        return -1


class Status:
    def __init__(self, info: Union[int, str]):
        games = get_game()
        if isinstance(info, str):
            for title in games.keys():
                if info in title:
                    self.handle = games[title]
                    self.name = info
                    break
            else:
                raise RuntimeError(f'找不到标题中存在{info}的游戏窗口')
        elif isinstance(info, int):
            self.handle = info
            self.name = f'玩家{info}'
        else:
            raise TypeError('info类型有误')

        self.dc = win32gui.GetWindowDC(self.handle)
        self.thread = None

        self.capture_result = None
        self.image_path = './image'
        self.repeat_find_period = 1000

        self.wind = None
        self.angle = None
        self.map_pos = None
        self.box_pos = None
        self.box_width = None
        self.blues = None
        self.cur_pos = None
        self.reds = None
        self.circle = None

        self.team_task = []

    def __repr__(self) -> str:
        return self.name

    def task(self):
        pass

    def start(self, task_func: Callable = None):
        self.thread = Thread(target=self.task) if task_func is None else Thread(target=task_func)
        self.thread.setDaemon(True)
        self.thread.start()
        return self.thread.ident

    def stop(self):
        stop_thread(self.thread)
        self.thread = None

    @staticmethod
    def __sleep(period: int):
        time.sleep(period / 1000)

    @staticmethod
    def __delay(period: int):
        start = time.perf_counter()
        while (time.perf_counter() - start) * 1000 < period:
            continue

    def __click(self, pos: tuple):
        long_position = win32api.MAKELONG(*pos)
        win32api.SendMessage(self.handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, long_position)
        win32api.SendMessage(self.handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, long_position)

    def __press(self, key: str, period: int = None):
        keycode = get_keycode(key)
        win32api.SendMessage(self.handle, win32con.WM_KEYDOWN, keycode, 0)
        if period:
            self.__delay(period)
        win32api.SendMessage(self.handle, win32con.WM_KEYUP, keycode, 0)

    def capture(self, position: tuple = (0, 0, 1000, 600), return_img: bool = False):
        x, y, w, h = position
        hwnd_dc = win32gui.GetWindowDC(self.handle)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        save_bit_map = win32ui.CreateBitmap()
        save_bit_map.CreateCompatibleBitmap(mfc_dc, w, h)
        save_dc.SelectObject(save_bit_map)
        save_dc.BitBlt((0, 0), (w, h), mfc_dc, (x, y), win32con.SRCCOPY)
        signed_ints_array = save_bit_map.GetBitmapBits(True)
        img = np.frombuffer(signed_ints_array, dtype="uint8")
        img.shape = (h, w, 4)
        win32gui.DeleteObject(save_bit_map.GetHandle())
        mfc_dc.DeleteDC()
        save_dc.DeleteDC()
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        self.capture_result = img
        return img if return_img else None

    def activate(self, period: int = 0):
        win32api.PostMessage(self.handle, win32con.WM_SETFOCUS, 0, 0)
        self.__sleep(period)

    def sleep(self, period: int):
        self.__sleep(period)

    def find(self, method: Literal['find', 'rfind', 'mfind', 'find_image', 'rfind_image'] = 'find', **kwargs) -> Union[tuple, str, bool]:
        self.activate()
        if method in ('find', 'f'):
            pos, rgb = kwargs['pos'], kwargs.get('rgb', None)
            pixel = win32gui.GetPixel(self.dc, *pos)
            pixel = pixel & 0xff, (pixel >> 8) & 0xff, (pixel >> 16) & 0xff
            if rgb is None:
                return pixel
            else:
                # print(f'pixel: {pixel}')
                # print(f'rgb: {rgb}')
                return True if pixel == rgb else False
        elif method in ('rfind', 'rf', 'r'):
            pos, rgb = kwargs['pos'], kwargs['rgb']
            while not (self.find('find', pos=pos) == rgb):
                kwargs['el']() if 'el' in kwargs else self.activate()
                self.__sleep(kwargs['period'] if 'period' in kwargs else self.repeat_find_period)
        elif method in ('mfind', 'mf', 'm'):
            for condition, (pos, rgb) in kwargs.items():
                if self.find('find', pos=pos) == rgb:
                    return condition
        elif method in ('find_image', 'fi', 'image', 'i'):
            part, img = kwargs.get('part', (0, 0, 1000, 600)), kwargs['img']
            self.capture()
            if isinstance(img, np.ndarray) and len(img.shape) == 3 and img.shape[2] in [3, 4]:
                template_image = img
            elif isinstance(img, str):
                if '.' in img:
                    template_image = cv2.imread(img)
                else:
                    template_image = cv2.imread(self.image_path + '/' + img + '.png', 0)
            else:
                raise RuntimeError('找不到所要识别的图片')

            x, y, w, h = part
            image = cv2.cvtColor(self.capture_result, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(image[y:y + h, x:x + w], template_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if max_val >= 0.9:
                w, h = template_image.shape[::-1]
                return int(max_loc[0] + w / 2), int(max_loc[1] + h / 2)

    def click(self, method: Literal['normal', 'find', 'rfind', 'find_image', 'rfind_image'] = 'normal', **kwargs):
        self.activate()
        if method in ('normal', 'n', 'click'):
            pos = kwargs['pos']
            self.__click(pos=pos)
        elif method in ('find', 'f'):
            pos = kwargs['pos']
            if self.find('find', pos=pos) == kwargs['rgb']:
                self.__click(pos=pos)
                return True
            return False
        elif method in ('rfind', 'rf', 'r'):
            pos, rgb = kwargs['pos'], kwargs['rgb']
            while not (self.find('find', pos=pos) == rgb):
                kwargs['el']() if 'el' in kwargs else self.activate()
                self.__sleep(kwargs['period'] if 'period' in kwargs else self.repeat_find_period)
            self.__click(pos=pos)
        elif method in ('find_image', 'fi', 'i'):
            img, part = kwargs['img'], kwargs.get('part', (0, 0, 1000, 600))
            if pos := self.find('find_image', img=img, part=part):
                self.__click(pos)
                return True
            return False
        elif method in ('rfind_image', 'rfi', 'ri'):
            img, part = kwargs['img'], kwargs.get('part', (0, 0, 1000, 600))
            while not (pos := self.find('find_image', img=img, part=part)):
                kwargs['el']() if 'el' in kwargs else self.activate()
                self.__sleep(kwargs['period'] if 'period' in kwargs else self.repeat_find_period)
            self.__click(pos)

    def press(self, key_series: Union[tuple, str, int]):
        if isinstance(key_series, str):
            self.__press(key_series)
            return

        elements = []
        for elem in key_series:
            if isinstance(elem, str):
                elements.append(('press', elem))
            elif isinstance(elem, int):
                elements.append(('sleep', elem))
            elif isinstance(elem, tuple):
                elements.append(('press', *elem))

        for action, arg in elements:
            # getattr(self, f"__{action}")(arg)
            if action == 'press':
                self.__press(arg)
            else:
                self.__press(arg)

    def input(self, content: str):
        input_char = [ord(c) for c in content]
        for char in input_char:
            win32api.PostMessage(self.handle, win32con.WM_CHAR, char, 0)

    def read(self, is_circle: bool = False):

        def read_wind():
            image = self.capture_result
            b, g, r = image.item(21, 468, 0), image.item(21, 468, 1), image.item(21, 468, 2)
            if b == 252 and g == r and g > 240 and r > 240:
                face = 1
            else:
                face = -1
            return ddtcv.Wind(self.capture_result) * face

        def read_angle():
            return ddtcv.Angle(self.capture_result)

        def read_small_map():
            return np.argwhere(np.all(self.capture_result[1, 750:] == [160, 160, 160], axis=-1))[0, 0] + 742

        def read_white_box():
            img = np.where(np.any(self.capture_result[24:120, self.map_pos:998] != [153, 153, 153], axis=-1), 0, 255).astype('uint8')
            contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w > 30:
                    white_box_pos = (x, y)
                    white_box_width = w / 10
                    return white_box_pos, white_box_width
            return None

        def read_blue():
            blue_list = []
            blue_triangle = None
            img = np.where(np.any(self.capture_result[24:120, self.map_pos:998] != [204, 51, 0], axis=-1), 0, 255).astype('uint8')
            contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if h > 3:
                    blue = (int(x + w / 2), int(y + h / 2))
                    blue_list.append(blue)
                elif 2 <= h <= 4 and 4 <= w <= 6:
                    blue_triangle = (int(x + w / 2), int(y + h / 2))
            return blue_list, blue_triangle

        def read_red():
            red_list = []
            img = np.where(np.any(self.capture_result[24:120, self.map_pos:998] != [0, 0, 255], axis=-1), 0, 255).astype('uint8')
            contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if h > 3:
                    red = (int(x + w / 2), int(y + h / 2))
                    red_list.append(red)
            return red_list

        def read_circle():
            def get_circle():
                self.activate()
                capture_1 = self.capture(position=(self.map_pos, 24, 998 - self.map_pos, 120 - 24), return_img=True)
                capture_1 = cv2.cvtColor(capture_1, cv2.COLOR_BGR2GRAY)
                self.__sleep(30)
                capture_2 = self.capture(position=(self.map_pos, 24, 998 - self.map_pos, 120 - 24), return_img=True)
                capture_2 = cv2.cvtColor(capture_2, cv2.COLOR_BGR2GRAY)
                image = np.where(capture_1 == capture_2, 255, 0).astype('uint8')
                contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if 15 < w < 25 or 15 < h < 25 and w == h:
                        self_x = int(x + w / 2)
                        self_y = int(y + h / 2)
                        return self_x, self_y
            while True:
                circle_pos = get_circle()
                if circle_pos:
                    return circle_pos
                elif is_circle:
                    return None
                self.__sleep(100)

        self.capture()
        self.wind = read_wind()
        self.angle = read_angle()
        self.map_pos = read_small_map()
        self.box_pos, self.box_width = read_white_box()
        self.blues, self.cur_pos = read_blue()
        self.reds = read_red()
        self.circle = read_circle()

    def shot(self, shot_angle: Union[int, tuple, None], shot_strength: int, shot_item: tuple = None, wait: bool = False):
        def change_angle(current_angle: int, target_angle: int):
            diff = target_angle - current_angle
            direction = 'W' if diff > 0 else 'S'
            for i in range(abs(diff)):
                self.__press(direction)

        def press_shot(strength: int):
            self.__press('space', period=(strength + 1) * 40)

        self.find('rfind', pos=(495, 163), rgb=(255, 255, 224)) if wait else None
        self.press(shot_item) if shot_item else None
        if isinstance(shot_angle, int):
            change_angle(self.angle, shot_angle)
            press_shot(shot_strength)
        elif isinstance(shot_angle, (list, tuple)):
            change_angle(self.angle, shot_angle[0])
            press_shot(shot_strength)
            for i in range(1, len(shot_angle)):
                self.__sleep(800)
                change_angle(shot_angle[i-1], shot_angle[i])
        else:
            press_shot(shot_strength)

    def move(self, move_face: str, move_period: int, reverse_face: bool = False):
        """
        角色移动
        :param move_face: 移动朝向
        :param move_period: 移动时间(毫秒)
        :param reverse_face: 移动完后是否逆转朝向
        :return: 无返回值
        """
        if move_face in ['left', 'l', '左']:
            self.__press('A')
            self.__press('A', period=move_period)
            if reverse_face:
                self.__press('D')
        elif move_face in ['right', 'r', '右']:
            self.__press('D')
            self.__press('D', period=move_period)
            if reverse_face:
                self.__press('A')







