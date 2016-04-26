"""
second iteration of the ray-casting camera.
treats Minecraft block as smallest discrete unit of world, rather than a continuous 3D world
calculates set of visible blocks for a givent client position pitch and yaw (head)
"""

from math import pi, floor, sqrt
import numpy as np
import time
import logging

import utils.movement_utils as mov
from utils.constants import *

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')
# radius of vision
MAX_DIST = 10

#############################################################################
# Utility methods that don't require state variables
#############################################################################
# returns: 0 if equal, + if first greater, - if second greater
def compare_floats(f1, f2):
    if abs(f1-f2) < 0.000001:
        return 0
    else:
        return f1-f2

def distance(x1, y1, x2, y2):
    return sqrt((x2-x1)**2 + (y2-y1)**2)

def offset_origin(x, y):
    x1, y1 = (x + 0.5, y + 0.5)
    return distance(0.5, 0.5, x1, y1)

# 'run over rise' creates multiplicative factors (fewer divisions later on)
# 0.5 is important, because rays are cast from (0.5, 0.5)
def get_ray_factors(h, d):
    if h < 0.5:
        # lower left corner
        left = (h - 0.5)/(d - 0.5)
    else:
        # upper left corner
        left = (h - 0.5)/(d+1 - 0.5)
    if (h+1) < 0.5:
        # upper right corner
        right = (h+1 - 0.5)/(d+1 - 0.5)
    else:
        # lower right corner
        right = (h+1 - 0.5)/(d - 0.5)
    return (left, right)

# since origin (0.5, 0.5) is always part of the line, simply use point-slope
# form with origin to get the new x vals: minh and maxh
def is_visible(h, d, left, right):
    if h < 0.5:
        minh = ((d-0.5)*left + 0.5)
    else:
        minh = ((d+1-0.5)*left + 0.5)
    if (h+1) < 0.5:
        maxh = ((d+1-0.5)*right + 0.5)
    else:
        maxh = ((d-0.5)*right + 0.5)
    if compare_floats(h,minh) > 0 and compare_floats(h+1,maxh) < 0:
        return False
    return True

#############################################################################
# Initializes game materials, and whether or not they are solid
# Not comprehensive, but includes most common blocks
#############################################################################
class MinecraftMaterials:
    def __init__(self):
        self.block_mats = dict()
        self.init_block_mats()

    def init_block_mats(self):
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

#############################################################################
# Performs ray-casting and neighbor checking for FOV calculations
#############################################################################
class FovUtils:
    def __init__(self, world, max_dist=MAX_DIST):
        self.max_dist = max_dist
        self.world = world

        self.ray_factors = dict()
        self.rel_fov = list()
        self.percept = dict()

        self.single_blocking = dict()
        self.pair_blocking = dict()

        self.init_fov()
        self.init_single_blocking()
        self.init_pair_blocking()
        self.materials = MinecraftMaterials()

    def init_fov(self):
        self.rel_fov = [(hi,di)
            for di in range(self.max_dist)
            for hi in range(-di,di+1)]

    def init_single_blocking(self):
        self.ray_factors = {(h1,d1):get_ray_factors(h1,d1)
            for h1,d1 in self.rel_fov}
        self.single_blocking = {
            (h1,d1):{(h2,d2)
                    for h2,d2 in self.rel_fov
                    if (d2>d1
                        and (not is_visible(h2,d2,*self.ray_factors[(h1,d1)]))
                        and (offset_origin(h1, d1) < offset_origin(h2, d2)))
                    }
            for h1,d1 in self.ray_factors
        }

    def init_pair_blocking(self):
        for h,d in self.rel_fov:
            neighbors = self.get_neighbors(h,d)
            for hn,dn in neighbors:
                if (((h,d),(hn,dn)) in self.pair_blocking or
                    ((hn,dn),(h,d)) in self.pair_blocking):
                    continue
                left_factors,right_factors = zip(
                    self.ray_factors[(h,d)],
                    self.ray_factors[(hn,dn)]
                )
                # ray factors (1/m) have the nice property of increasing
                # monotonically from left to right of FOV
                left_most = min(left_factors)
                right_most = max(right_factors)
                pair = ((h,d),(hn,dn))
                self.pair_blocking[pair] = set()
                for hb,db in self.rel_fov:
                    if (hb,db) == (hn,dn) or (hb,db) == (h,d):
                        continue
                    if is_visible(hb, db, left_most, right_most):
                        continue
                    if offset_origin(hb, db) < offset_origin((h+hn)/2.,(d+dn)/2.):
                        continue
                    self.pair_blocking[pair].add((hb,db))

    def get_neighbors(self, h, d):
        # diagonals first, since they block most
        neighbors = [
            (h-1,d-1), (h+1,d-1), (h-1,d+1), (h-1,d-1),
            (h,d-1), (h,d+1), (h-1,d), (h+1,d)
        ]
        neighbors = [(hn,dn) for hn,dn in neighbors if self.pos_in_range(hn,dn)]
        return neighbors

    def update_pose(self, pose):
        self.pos = mov.get_nearest_position(pose['x'], pose['y'], pose['z'])
        self.dir = mov.get_nearest_direction(pose['yaw'])

    def update_percept(self, pose):
        # always update the pose first, or camera will be in wrong place
        self.update_pose(pose)
        self.cur_blocked = set()
        self.cur_percept = {coord:None for coord in self.rel_fov}

        for h,d in self.rel_fov:
            if self.is_blocked(h,d):
                self.cur_percept[(h,d)] = None
            else:
                ax,ay,az = self.rel_to_abs(h,d)
                bid,meta = self.world.get_block(ax, ay, az)
                self.cur_percept[(h,d)] = bid
                if self.materials.is_solid(bid):
                    self.update_blocked(h, d)
        return self.cur_percept

    def pos_in_range(self, h, d):
        if d >=0 and d < self.max_dist and h >= -d and h <= d:
            return True
        return False

    def is_blocked(self, h, d):
        if (h,d) in self.cur_blocked:
            return True
        return False

    def update_blocked(self, h, d):
        cur_blocked = set()
        neighbors = self.get_neighbors(h,d)
        for hn,dn in neighbors:
            if (hn,dn) in cur_blocked or self.is_blocked(hn,dn):
                continue
            mat = self.cur_percept[(hn,dn)]
            if (mat is None) or (not self.materials.is_solid(mat)):
                continue
            if ((h,d),(hn,dn)) in self.pair_blocking:
                cur_blocked |= self.pair_blocking[((h,d),(hn,dn))]
            else:
                cur_blocked |= self.pair_blocking[((hn,dn),(h,d))]
        for hb,db in cur_blocked:
            self.cur_percept[(hb,db)] = None
        self.cur_blocked |= cur_blocked
        self.cur_blocked |= self.single_blocking[(h,d)]

    def rel_to_abs(self, h, d):
        ax,ay,az = self.pos
        # SOUTH is +z
        if self.dir == DIR_SOUTH:
            return ax-h, ay, az+d
        # NORTH is -z
        if self.dir == DIR_NORTH:
            return ax+h, ay, az-d
        # EAST is +x
        if self.dir == DIR_EAST:
            return ax+d, ay, az+h
        # WEST is -x
        if self.dir == DIR_WEST:
            return ax-d, ay, az-h

    def abs_to_rel(self, x, y, z):
        ax,ay,az = self.pos
        # SOUTH is +z
        if self.dir == DIR_SOUTH:
            return -(x-ax), z-az
        # NORTH is -z
        if self.dir == DIR_NORTH:
            return x-ax, -(z-az)
        # EAST is +x
        if self.dir == DIR_EAST:
            return z-az, x-ax
        # WEST is -x
        if self.dir == DIR_WEST:
            return -(z-az), -(x-ax)

    def draw_visual_percept(self, percept):
        coords = self.rel_fov
        max_dist = self.max_dist
        full_string = "\n" + "__"*max_dist*2 + "\n"
        for i in reversed(range(max_dist)):
            cur_list = [" "]*(max_dist*2 - 1)
            full_string += "|"
            cur_coords = [(h,d) for h,d in coords
                if (d == i)]
            cur_blocked = [(h,d) for h,d in percept
                if (d == i and percept[(h,d)] is None)]
            cur_solid = [(h,d) for h,d in percept
                if (d == i and percept[(h,d)] != 0 and percept[(h,d)] != None)]
            for h,d in cur_blocked:
                cur_list[h+(max_dist-1)] = "-"
            for h,d in cur_solid:
                cur_list[h+(max_dist-1)] = "#"
            for ch in cur_list:
                full_string += (ch + "|")
            full_string += "\n"
            #print(full_string)
        full_string += "__"*max_dist*2 + "\n"
        logger.info("current visual percept: {}".format(full_string))

if __name__ == "__main__":
    # attempt to initialize
    my_fov_utils = FovUtils(max_dist=10)
