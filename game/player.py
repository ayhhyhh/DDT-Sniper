from ddtank.utils.get_game import get_game
from game.service import GameService
import win32gui, win32ui, win32con
import time
import logging

logger = logging.getLogger(__name__)


class HandleError(Exception):
    pass


class Player:
    def __init__(self, parent_handle: str) -> None:
        self.parent_handle = parent_handle
        self.handle = GameService.find_flash_player_window_by_handle(parent_handle)
        if not self.handle:
            raise HandleError("The handle is not a game window")

        w, h = (1000, 600)
        self.hwnd_dc = win32gui.GetWindowDC(self.handle)
        self.mfc_dc = win32ui.CreateDCFromHandle(self.hwnd_dc)
        self.save_dc = self.mfc_dc.CreateCompatibleDC()
        self.save_bit_map = win32ui.CreateBitmap()
        self.save_bit_map.CreateCompatibleBitmap(self.mfc_dc, w, h)

        self.wind = 0
        self.angle = 0
        self.map_left_bound = 0
        self.box_pos = (0, 0)
        self.box_width = 0
        self.circle = (0, 0)

    def update_info(self):
        image = GameService.capture(self.handle, self.mfc_dc, self.save_dc, self.save_bit_map)
        try:
            self.wind = GameService.read_wind(image)
            self.angle = GameService.read_angle(image)
            self.map_left_bound = GameService.read_small_map(image)
            self.box_pos, self.box_width = GameService.read_white_box(image)

            image1 = GameService.capture(self.handle, self.mfc_dc, self.save_dc, self.save_bit_map)
            self.__sleep(100)
            image2 = GameService.capture(self.handle, self.mfc_dc, self.save_dc, self.save_bit_map)
            self.circle = GameService.read_circle(image1, image2)
        except Exception as e:
            logger.exception(e)
        


    @staticmethod
    def __sleep(period: int):
        time.sleep(period / 1000)

    def destroy(self):
        win32gui.DeleteObject(self.save_bit_map.GetHandle())
        self.mfc_dc.DeleteDC()
        self.save_dc.DeleteDC()
        win32gui.ReleaseDC(self.handle, self.hwnd_dc)
