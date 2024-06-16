import PySimpleGUI as sg

from ddtank import Status


class MapStatus(Status):
    def read_map(self):
        self.activate(100)
        if self.find(pos=(956, 12)) == (62, 107, 47):
            self.read()

def get_map(handle):
    map_status = MapStatus(handle)
    map_status.read_map()
    info = f"""
    风力:    {map_status.wind}
    角度:    {map_status.angle}
    小地图界限:    {map_status.map_pos}
    白框位置:    {map_status.box_pos}
    白框宽度:    {map_status.box_width}
    蓝点:    {map_status.blues}
    三角:    {map_status.cur_pos}
    红点:    {map_status.reds}
    光圈:    {map_status.circle}
    """
    sg.popup(info)










