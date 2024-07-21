from ddtank.utils.get_game import get_game
from game.service import GameService
import win32gui, win32ui, win32con
import time


class HandleError(Exception):
    pass


class player:
    def __init__(self, info: int | str) -> None:
        games = get_game()
        if isinstance(info, str):

            for title, handle in games.items():
                if info in title:
                    self.handle = handle
                    break
            else:
                raise HandleError(f"{info} not found")
        elif isinstance(info, int):
            for title, handle in games.items():
                if info == handle:
                    self.handle = handle
                    break
            else:
                raise HandleError(f"{info} not found")
        else:
            raise HandleError(f"{info} type: {type(info)} not supported")
        w, h = (1000, 600)
        self.hwnd_dc = win32gui.GetWindowDC(self.handle)
        self.mfc_dc = win32ui.CreateDCFromHandle(self.hwnd_dc)
        self.save_dc = self.mfc_dc.CreateCompatibleDC()
        self.save_bit_map = win32ui.CreateBitmap()
        self.save_bit_map.CreateCompatibleBitmap(self.mfc_dc, w, h)

        self.wind = None
        self.angle = None
        self.map_left_bound = None
        self.box_pos = None
        self.color = None
        self.circle = None

    def update_info(self):
        image = GameService.capture(self.mfc_dc, self.save_dc, self.save_bit_map)

        self.wind = GameService.read_wind(image)
        self.angle = GameService.read_angle(image)
        self.map_left_bound = GameService.read_small_map(image)
        self.box_pos = GameService.read_white_box(image)

        image1 = GameService.capture(self.mfc_dc, self.save_dc, self.save_bit_map)
        self.__sleep(30)
        image2 = GameService.capture(self.mfc_dc, self.save_dc, self.save_bit_map)
        self.circle = GameService.read_circle(image1, image2)
        
    @staticmethod
    def __sleep(period: int):
        time.sleep(period / 1000)

    def destroy(self):
        win32gui.DeleteObject(self.save_bit_map.GetHandle())
        self.mfc_dc.DeleteDC()
        self.save_dc.DeleteDC()
        win32gui.ReleaseDC(self.handle, self.hwnd_dc)
