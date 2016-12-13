"""Robot methods, errors, modules all in one interface that used in our library,
include it's api and module enhancement."""

#errors
from robot.errors import ExecutionFailed

#utils
from robot.utils import get_timestamp
from robot.utils import seq2str
from robot.utils import timestr_to_secs 
from robot.utils import secs_to_timestr
from robot.utils import get_time
from robot.utils import get_error_message
from robot.utils import timestamp_to_secs
from robot.utils import secs_to_timestamp
#from robot.utils import matches
#from robot.utils.asserts import fail_if_none
#from robot.utils.asserts import assert_equals
from robot.utils import get_error_details
from robot.utils import cut_long_message

#TODO runner enhancement 
