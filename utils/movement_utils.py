import logging
import math

from utils.constants import *

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')


def get_nearest_direction(yaw):
    deg_from = [(abs(DIR_NORTH - yaw),'NORTH'),
                (abs(DIR_SOUTH - yaw),'SOUTH'),
                (abs(DIR_WEST - yaw), 'WEST'),
                (abs(DIR_EAST - yaw), 'EAST'),]
    diff,facing = min(deg_from)
    logger.debug("facing {} with a deviation of {}".format(facing, diff))
    return facing


def get_nearest_position(x, y, z):
    pos = (math.floor(x),math.floor(y),math.floor(z))
    logger.debug("at position {} with original {}".format(pos, (x,y,z)))
    return pos


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
