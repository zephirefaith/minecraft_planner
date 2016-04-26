"""
Some constants for plugins dealing with agent (discretized) movement
The agent can move forward, and can face any cardinal compass direction
(NORTH, SOUTH, EAST, WEST). These constants define values relative to
the Minecraft world
"""

# compass directions in yaw values
DIR_SOUTH = 0.0
DIR_EAST = -90.0
DIR_NORTH = 180.0
DIR_WEST = 90.0

TURN_NONE = 0
TURN_LEFT = -90
TURN_RIGHT = 90

MOVE_NONE = 0
MOVE_FORWARD = 1

# acceptable error to test whether agent has stopped moving
EPSILON_DIST = 1./10
EPSILON_DIR  = 90./10

##############################################################################
# string labels used for printing, maybe later for ids as well
##############################################################################
compass_labels = {
    DIR_SOUTH: 'SOUTH',
    DIR_EAST:  'EAST',
    DIR_NORTH: 'NORTH',
    DIR_WEST:  'WEST',
}

motion_labels = {
    MOVE_NONE:    'NONE',
    MOVE_FORWARD: 'FORWARD',
    TURN_NONE:    'NONE',
    TURN_LEFT:    'LEFT',
    TURN_RIGHT:   'RIGHT',
}

##############################################################################
# absolute changes caused by taking the corresponding action
##############################################################################
look_left_deltas = {
    DIR_NORTH: DIR_WEST,
    DIR_SOUTH: DIR_EAST,
    DIR_WEST:  DIR_SOUTH,
    DIR_EAST:  DIR_NORTH,
}

look_right_deltas = {
    DIR_NORTH: DIR_EAST,
    DIR_SOUTH: DIR_WEST,
    DIR_WEST:  DIR_NORTH,
    DIR_EAST:  DIR_SOUTH,
}

# not exactly 'constant' but functions themselves are constant for Minecraft
# should this be moved to a utility file? (e.g. movement_utils.py)
move_deltas = {
    DIR_EAST:  (lambda x,y,z: (x+1,y,z)),
    DIR_WEST:  (lambda x,y,z: (x-1,y,z)),
    DIR_SOUTH: (lambda x,y,z: (x,y,z+1)),
    DIR_NORTH: (lambda x,y,z: (x,y,z-1)),
}

##############################################################################
# maps for linearizing percepts
##############################################################################
# a DefaultDict is probably better here
percept_types_block = {
    # unknown
    None:   '0',
    # air block. treat as 'nothing'
    0:      '1',
    # gold block. resource
    41:     '2'
}

percept_types_motion = {
    'NONE':      '0',
    'FORWARD':   '1',
    'LEFT':      '2',
    'RIGHT':     '3'
}

percept_types_direction = {
    'SOUTH': 0,
    'EAST': 1,
    'NORTH': 2,
    'WEST': 3,
}

percept_types_items = {
    'AXE':   '0',
    'PICK':  '1',
}
