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

move_deltas = {
    DIR_EAST:  (lambda x,y,z: (x+1,y,z)),
    DIR_WEST:  (lambda x,y,z: (x-1,y,z)),
    DIR_SOUTH: (lambda x,y,z: (x,y,z+1)),
    DIR_NORTH: (lambda x,y,z: (x,y,z-1)),
}

compass_labels = {
    DIR_SOUTH:  'SOUTH',
    DIR_EAST:   'EAST',
    DIR_NORTH:  'NORTH',
    DIR_WEST:   'WEST',
}

motion_labels = {
    MOVE_NONE:      'NONE',
    MOVE_FORWARD:   'FORWARD',
    TURN_NONE:      'NONE',
    TURN_LEFT:      'LEFT',
    TURN_RIGHT:     'RIGHT',
}

# primitive actions/percepts. Note, all are egocentric
# motion_dir = {'LEFT', 'RIGHT', 'NONE'}
# motion_pos = {'FORWARD', 'NONE'}
