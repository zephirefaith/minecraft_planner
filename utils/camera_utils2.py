
"""
created by Bradley Sheneman
second iteration of the ray-casting camera.
treats Minecraft block as smallest discrete unit of world, rather than a continuous 3D world
calculates set of visible blocks for a givent client position pitch and yaw (head)
"""

from math import pi, floor, sqrt
import numpy as np
import time

import utils.movement_utils as mov
from utils.constants import *

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

# 'run over rise' creates multiplicative factors (fewer divisions later on)
def get_ray_factors(h, d):
    if h < 0.5:
        # lower left corner
        left = (h - 0.5)/(d - 0.5)
    else:
        # upper left corner
        left = (h - 0.5)/(d+1 - 0.5)
    if (h+1) < 0.5:
        right = (h+1 - 0.5)/(d+1 - 0.5)
    else:
        right = (h+1 - 0.5)/(d - 0.5)
    return (left, right)

def is_visible(h, d, left, right):
    if h < 0.5:
        #print("h less than 0.5")
        minh = ((d-0.5)*left + 0.5)
    else:
        #print("h greater than 0.5")
        minh = ((d+1-0.5)*left + 0.5)
    if (h+1) < 0.5:
        #print("h+1 less than 0.5")
        maxh = ((d+1-0.5)*right + 0.5)
    else:
        #print("h+1 greater than 0.5")
        maxh = ((d-0.5)*right + 0.5)
    #print("minh: {}, maxh: {}".format(minh, maxh))
    if compare_floats(h,minh) > 0 and compare_floats(h+1,maxh) < 0:
        return False
    return True

#############################################################################
# Initializes game materials, and whether or not they are solid
#############################################################################
class MinecraftMaterials:
    def __init__(self):
        self.block_mats = dict()
        self.init_block_mats()

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

#############################################################################
# Performs ray-casting and neighbor checking for FOV calculations
#############################################################################
class FovUtils:
    def __init__(self, world, max_dist=MAX_DIST):
        self.max_dist = max_dist
        self.world = world
        ray_factors = get_ray_factors(1,4)
        print("ray factors for 1,4: {}".format(ray_factors))
        print(is_visible(1,5,*ray_factors))

        self.ray_factors = dict()
        self.rel_fov = list()
        self.percept = dict()
        self.single_blocking = dict()
        self.pair_blocking = dict()

        self.init_fov()
        self.init_single_blocking()
        self.init_pair_blocking()
        self.materials = MinecraftMaterials()

        print("single blocking for (1,4): {}".format(self.single_blocking[(1,4)]))
        #print("relative fov coords: {}\n".format(self.rel_fov))
        # print("blocked by a single position:")
        # for key in self.single_blocking:
        #     print("this: {} blocks these: {}".format(key,self.single_blocking[key]))

    def init_fov(self):
        self.rel_fov = [(hi,di) for di in range(self.max_dist) for hi in range(-di,di+1)]

    def init_single_blocking(self):
        self.ray_factors = {(h1,d1):get_ray_factors(h1,d1) for h1,d1 in self.rel_fov}
        self.single_blocking = {
            (h1,d1):{(h2,d2)
                    for h2,d2 in self.rel_fov
                    if (d2>d1
                        and (not is_visible(h2,d2,*self.ray_factors[(h1,d1)]))
                        and (distance(0.5, 0.5, h1+0.5, d1+0.5) < distance(0.5, 0.5, h2+0.5, d2+0.5)))
                    }
            for h1,d1 in self.ray_factors
        }

    def init_pair_blocking(self):
        for h,d in self.rel_fov:
            neighbors = self.get_neighbors(h,d)
            for hn,dn in neighbors:
                if ((h,d),(hn,dn)) in self.pair_blocking or ((hn,dn),(h,d)) in self.pair_blocking:
                    continue
                left_factors,right_factors = zip(self.ray_factors[(h,d)], self.ray_factors[(hn,dn)])
                left_most = min(left_factors)
                right_most = max(right_factors)

                self.pair_blocking[((h,d),(hn,dn))] = set()
                for hb,db in self.rel_fov:
                    if (hb,db) == (hn,dn) or (hb,db) == (h,d):
                        continue
                    if is_visible(hb, db, left_most, right_most):
                        continue
                    if distance(0.5,0.5,hb+0.5,db+0.5) < (distance(0.5,0.5,(h+hn+1)/2.,(d+dn+1)/2.)):
                        continue
                    self.pair_blocking[((h,d),(hn,dn))].add((hb,db))

    def get_neighbors(self, h, d):
        neighbors = [
            # diagonals first, since they block most
            (h-1,d-1), (h+1,d-1), (h-1,d+1), (h-1,d-1),
            # perpendiculars
            (h,d-1), (h,d+1), (h-1,d), (h+1,d)]
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
            #print("coordinate: {} is single blocked".format((h,d)))
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

if __name__ == "__main__":
    my_fov_utils = FovUtils(max_dist=10)
