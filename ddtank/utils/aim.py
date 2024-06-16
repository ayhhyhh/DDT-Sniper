import math
import numpy as np
from scipy.optimize import fsolve
"""
-----计算力度操作-----
-参数说明：
    angel: 角度
    wind: 风力，逆风为负数
    dx: 横向距离，大地图每100像素为1个距离，即“1距”
    dy: 纵向距离，同上
-返回值说明：
    返回计算后的力度值，为0-100的浮点数
-备注：
    存在拟合误差
"""
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
        return computePosition(vx, fx, r, t) - math.sqrt(dx ** 2 + dy ** 2)

    f = fsolve(solve, [100])
    if f[0] > 100:
        return 100.0
    elif f[0] < 0:
        return 0.0
    return f[0]

