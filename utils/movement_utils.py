import logging
import math

from utils.constants import *

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')


#########################################################################
# Helper functions to determine changes in position and direction
#########################################################################

def get_abs_angle(yaw):
    if yaw >= 0: return yaw
    else: return 360 + yaw

def get_nearest_delta_pos(prev_pos, cur_pos):
    dist = math.sqrt(
        (prev_pos.x - cur_pos.x)**2 +
        (prev_pos.y - cur_pos.y)**2 +
        (prev_pos.z - cur_pos.z)**2)
    if abs(dist-1) > EPSILON_DIST:
        return MOVE_FORWARD
    return MOVE_NONE

def get_nearest_delta_dir(prev_dir, cur_dir):
    prev_angle = get_abs_angle(prev_dir)
    cur_angle = get_abs_angle(cur_dir)
    delta = cur_dir - prev_dir
    if delta - TURN_LEFT < EPSILON_DIR:
        return TURN_LEFT
    elif delta - TURN_RIGHT < EPSILON_DIR:
        return TURN_RIGHT
    return TURN_NONE

#########################################################################
# Helper functions to discretize the movement space
#########################################################################

def get_nearest_direction(yaw):
    deg_from = [(abs(DIR_NORTH - yaw),DIR_NORTH),
                (abs(DIR_SOUTH - yaw),DIR_SOUTH),
                (abs(DIR_WEST - yaw), DIR_WEST),
                (abs(DIR_EAST - yaw), DIR_EAST),]
    diff,facing = min(deg_from)
    label = compass_labels[facing]
    logger.debug("facing {} with a deviation of {}".format(label, diff))
    return facing

def get_nearest_position(x, y, z):
    pos = (math.floor(x),math.floor(y),math.floor(z))
    logger.debug("at position {} with original {}".format(pos, (x,y,z)))
    return pos

#########################################################################
# Logging functions
#########################################################################

def log_agent_motion(primitive_action):
    logger.info(
        "current action:\nmoving: {}, turning: {}>\n".format(
            primitive_action.delta_pos,
            primitive_action.delta_dir,)
    )

def log_agent_state(agent_state):
    logger.info(
        "current state:\n<x:{}, y:{}, z:{}, facing:{}, moving:{}, turning:{}>\n".format(
            agent_state.pos.x,
            agent_state.pos.y,
            agent_state.pos.z,
            agent_state.facing,
            agent_state.moving,
            agent_state.turning,)
    )
