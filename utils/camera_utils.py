"""
created by Bradley Sheneman
calculates set of visible blocks for a givent client position pitch and yaw (head)
"""

#import roslib; roslib.load_manifest('minecraft_bot')
#import rospy
#from minecraft_bot.srv import get_block_multi_srv
#from minecraft_bot.msg import map_block_msg, vec3_msg

from math import sin, cos, radians, pi, floor
import numpy as np
#from sys import argv
import time

# radius of vision
MAX_DIST = 6

# step size
D_DIST 	 = 0.2
D_PITCH  = 15.
D_YAW 	 = 5.

# angles cover range theta - R_THETA to theta + R_THETA
# e.g. R_YAW 45 means it will cover a 90 degree range
R_PITCH = 0
R_YAW   = 45

block_mats = {}

def init_block_mats():
    # this is not a comprehensive list, but includes most common solid blocks
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
        block_mats[blockid] = False

    for blockid in solids:
        block_mats[blockid] = True


def is_solid(blockid):
    #print blockid
    if block_mats[blockid] == True:
            return True
    return False

#
# # convert to angle between 0 and 360 (include 0, not include 360)
# def get_abs_angle(yaw):
#     if yaw >= 0: return yaw
#     else: return 360 + yaw
#

def calc_ray_step(pitch, yaw, dist):
    pt = radians(pitch)
    yw = radians(yaw)

    if pt < pi/2 and pt > -pi/2:
        dx = -(dist*cos(pt))*sin(yw)
        dz = (dist*cos(pt))*cos(yw)
    else:
        dx = (dist*cos(pt))*sin(yw)
        dz = -(dist*cos(pt))*cos(yw)

    dy = -dist*sin(pt)

    return dx, dy, dz


def get_block_coords(x, y, z, step, num_steps):
    nx = floor(x + step[0]*num_steps)
    ny = floor(y + step[1]*num_steps)
    nz = floor(z + step[2]*num_steps)
    #print "x: %d, y: %d, z: %d"%(x, y, z)
    coords = {'x':nx, 'y':ny, 'z':nz}
    return coords


def get_coordinates_in_range(pos):
    x = pos['x']
    y = pos['y']
    z = pos['z']
    pitch = pos['pitch']
    yaw = pos['yaw']
    pit_range = np.arange(pitch - R_PITCH, pitch + R_PITCH + D_PITCH, D_PITCH)
    yaw_range = np.arange(yaw - R_YAW, yaw + R_YAW + D_YAW, D_YAW)
    num_steps = np.arange(0, int(MAX_DIST/D_DIST) + D_DIST)

    # ROS messages only support 1-D arrays...
    ray_steps = [calc_ray_step(pt, yw, D_DIST) for pt in pit_range for yw in yaw_range]
    block_coords = [get_block_coords(x, y, z, step, num) for step in ray_steps for num in num_steps]
    return block_coords


def get_visible_blocks(blocks):

    #start = time.time()
    vis_blocks = {}

    p_jump = int(floor((2*R_PITCH)/D_PITCH) + 1)
    y_jump = int(floor((2*R_YAW)/D_YAW) + 1)
    d_jump = int(floor((MAX_DIST)/D_DIST) + 1)
    #print("p jump: {}, y jump: {}, d jump: {}".format(p_jump, y_jump, d_jump))
    #print("length of blocks list: {}".format(len(blocks)))
    #print("array version of blocks: {}".format(np.array(blocks)))
    blocks3D = np.reshape(np.array(blocks), newshape=(p_jump, y_jump, d_jump))

    for y_list in blocks3D:
        for d_list in y_list:
            for block in d_list:
                #xyz = (block['x'], block['y'], block['z'])
                xyz = block['coords']
                #print xyz
                bid = block['id']

                if (bid == 0):
                    #print("found air, continuing...")
                    continue

                elif xyz not in vis_blocks:
                    #print("bid: {}".format(bid))
                    #print("new block. adding to list")
                    #vis_blocks[xyz] = block
                    vis_blocks[xyz] = bid

                    if is_solid(bid):
                        #print("block is solid, breaking out")
                        break

                elif is_solid(vis_blocks[xyz]):
                    #print("bid: {}".format(bid))
                    #print("found block: {} already at these coordinates".format(vis_blocks[xyz]['id']))
                    break

    #vis_blocks_list = vis_blocks.values()

    #end = time.time()
    #print "total: %f"%(end-start)

    return vis_blocks
