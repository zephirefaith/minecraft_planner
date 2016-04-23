
"""
created by Bradley Sheneman
second iteration of the ray-casting camera.
treats Minecraft block as smallest discrete unit of world, rather than a continuous 3D world
calculates set of visible blocks for a givent client position pitch and yaw (head)
"""

from math import sin, cos, radians, pi, floor
import numpy as np
import time

import utils.movement_utils as mov
from utils.constants import *

# radius of vision
MAX_DIST = 10

class FovUtils:
    def __init__(self, max_dist=MAX_DIST):
        self.max_dist = max_dist
        self.block_mats = dict()
        self.rel_fov = list()
        #self.abs_fov_coords = list()
        #self.rel_fov = dict()
        #self.abs_fov = dict()
        self.blocking = dict()

        self.init_block_mats()
        self.init_fov()
        self.init_blocking()

        #print("relative fov coords: {}\n".format(self.rel_fov_coords))
        # print("blocking:")
        # for key in self.blocking:
        #     print("this: {} blocks these: {}".format(key,self.blocking[key]))

    def init_block_mats(self):
        # not comprehensive but includes most common blocks
        blocks = [i for i in range(43+1)]
        solids = []
        for i in range(1,5+1,1):
            solids.append(i)
        solids.append(7)
        for i in range(12,17+1,1):
            solids.append(i)
        solids.append(19)
        for i in range(21,25+1,1):
            solids.append(i)
        solids.append(35)
        for i in range(41,43+1,1):
            solids.append(i)
        for blockid in blocks:
            self.block_mats[blockid] = False
        for blockid in solids:
            self.block_mats[blockid] = True


    def is_solid(self, blockid):
        if self.block_mats[blockid]:
            return True
        return False


    def init_fov(self):
        for di in range(self.max_dist):
            for hi in range(-di,di+1):
                self.rel_fov.append((hi,di))


    def init_blocking(self):
        for h1,d1 in self.rel_fov:
            left,right = self.get_ray_slopes(h1,d1)
            #print("block: {}, left: {}, right: {}".format((h1,d1),left, right ))
            self.blocking[(h1,d1)] = [
                (h2,d2) for h2,d2 in self.rel_fov
                    if d2>d1 and (not self.is_visible(h2,d2,left,right))]


    def set_cur_pos(self, x, y, z, pitch, yaw):
        self.abs_pos = mov.get_nearest_position(x, y, z)
        self.abs_dir = mov.get_nearest_direction(yaw)


    def rel_to_abs(self, h, d):
        ax,ay,az = self.abs_pos
        # SOUTH is +z
        if self.abs_dir == DIR_SOUTH:
            return ax-h, ay, az+d
        # NORTH is -z
        if self.abs_dir == DIR_NORTH:
            return ax+h, ay, az-d
        # EAST is +x
        if self.abs_dir == DIR_EAST:
            return ax+d, ay, az+h
        # WEST is -x
        if self.abs_dir == DIR_WEST:
            return ax-d, ay, az-h


    def abs_to_rel(self, x, y, z):
        ax,ay,az = self.abs_pos
        # SOUTH is +z
        if self.abs_dir == DIR_SOUTH:
            return -(x-ax), z-az
        # NORTH is -z
        if self.abs_dir == DIR_NORTH:
            return x-ax, -(z-az)
        # EAST is +x
        if self.abs_dir == DIR_EAST:
            return z-az, x-ax
        # WEST is -x
        if self.abs_dir == DIR_WEST:
            return -(z-az), -(x-ax)


    def get_ray_slopes(self, h, d):
        if h < 0.5:
            left = (d - 0.5)/(h - 0.5)
        else:
            left = (d+1 - 0.5)/(h - 0.5)

        if h+1 < 0.5:
            right = (d+1 - 0.5)/(h+1 - 0.5)
        else:
            right = (d - 0.5)/(h+1 - 0.5)

        return (left, right)


    def is_visible(self, h, d, left, right):
        minh = (d/left)
        maxh = (d/right)
        if h > minh and h+1 < maxh:
            return False
        return True


    def get_rel_fov(self):
        return self.rel_fov

    def get_blocked(self, h, d):
        return set(self.blocking[(h,d)])

if __name__ == "__main__":
    my_fov_utils = FovUtils(max_dist=10)
