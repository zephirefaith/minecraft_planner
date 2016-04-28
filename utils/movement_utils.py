import logging
import math

from utils.constants import *

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')


#########################################################################
# Helper functions to determine changes in position and direction
#########################################################################

def get_nearest_delta_pos(prev_pos, cur_pos):
    dist = math.sqrt(
        (prev_pos.x - cur_pos.x)**2 +
        (prev_pos.y - cur_pos.y)**2 +
        (prev_pos.z - cur_pos.z)**2)
    if abs(dist-1) < EPSILON_DIST:
        return MOVE_FORWARD
    return MOVE_NONE

def get_nearest_delta_dir(prev_dir, cur_dir):
    nearest_prev_dir = get_nearest_direction(prev_dir)
    nearest_cur_dir = get_nearest_direction(cur_dir)
    if look_left_deltas[nearest_prev_dir] == nearest_cur_dir:
        return TURN_LEFT
    if look_right_deltas[nearest_prev_dir] == nearest_cur_dir:
        return TURN_RIGHT
    # remaining cases: angle difference is 0 or 180
    # one is lack of movement, the other is illegal;
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
    logger.debug(
        "current motion percept: <moving: {}, turning: {}>".format(
            primitive_action.delta_pos,
            primitive_action.delta_dir,)
    )

def log_agent_state(agent_state):
    logger.debug(
        "current state: <x:{}, y:{}, z:{}, facing:{}>".format(
            agent_state.pos.x,
            agent_state.pos.y,
            agent_state.pos.z,
            compass_labels[agent_state.dir],)
    )

def log_agent_vision(visible_blocks):
    logger.debug(
        "current vis blocks: <{}>".format(visible_blocks)
    )
