# Protocol files
DAEMON_PROCESS_FILE = '/tmp/Daemon-pim{}.pid'
DAEMON_SOCKET = '/tmp/pim_uds_socket{}'
DAEMON_LOG_FOLDER = '/var/log/pimdm/'
DAEMON_LOG_STDOUT_FILE = DAEMON_LOG_FOLDER + 'stdout{}'

# PIM-DM TIMER VARIABLES
ASSERT_TIME = 180
GRAFT_RETRY_PERIOD = 3
JP_OVERRIDE_INTERVAL = 3.0
OVERRIDE_INTERVAL = 2.5
PROPAGATION_DELAY = 0.5
REFRESH_INTERVAL = 60  # State Refresh Interval
SOURCE_LIFETIME = 210
T_LIMIT = 210

# PIM-DM VARIABLES
HELLO_HOLD_TIME_NO_TIMEOUT = 0xFFFF
HELLO_HOLD_TIME = 160
HELLO_HOLD_TIME_TIMEOUT = 0

ASSERT_CANCEL_METRIC = 0xFFFFFFFF

# MULTIPLE TABLES SUPPORT
# Define which unicast routing table to be used for RPF checks and to get route metric information
# Default unicast routing table is 254
UNICAST_TABLE_ID = 254
# Define which multicast routing table to be used for setting multicast trees
# Default multicast routing table is 0
MULTICAST_TABLE_ID = 0
