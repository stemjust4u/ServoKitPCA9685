from boot import MAIN_FILE_LOGGING, MAIN_FILE_MODE, MAIN_FILE_NAME, logfiles
import ulogging
import utime

logger_log_level= 10
logger_type = "custom"  # 'basic' for basicConfig or 'custom' for custom logger
FileMode = 1 # If logger_type == 'custom'  then access to modes below
            #  FileMode == 1 # no log file
            #  FileMode == 2 # write to log file
logfile = __name__ + '.log'
if logger_type == 'basic': # Use basicConfig logger
    ulogging.basicConfig(level=logger_log_level) # Change logger global settings
    logger = ulogging.getLogger(__name__)
elif logger_type == 'custom' and FileMode == 1:        # Using custom logger
    logger = ulogging.getLogger(__name__)
    logger.setLevel(logger_log_level)
elif logger_type == 'custom' and FileMode == 2 and not MAIN_FILE_LOGGING: # Using custom logger with output to log file
    logger = ulogging.getLogger(__name__, logfile, mode='w', autoclose=True, filetime=5000)  # w/wb to over-write, a/ab to append, autoclose (with method), file time in ms to keep file open
    logger.setLevel(logger_log_level)
    logfiles.append(logfile)
elif logger_type == 'custom' and FileMode == 2 and MAIN_FILE_LOGGING:            # Using custom logger with output to main log file
    logger = ulogging.getLogger(__name__, MAIN_FILE_NAME, MAIN_FILE_MODE, 0)  # over ride with MAIN_FILE settings in boot.py
    logger.setLevel(logger_log_level)

logger.info(logger)

def TimerFunc(f, *args, **kwargs):
    name = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(utime.ticks_us(), t)
        logger.debug('Function,{},time,{:6.3f},ms'.format(name, delta/1000))
        return result
    return new_func

class Timer:

    def __init__(self):
        self._start_time = None

    def start(self):
        if self._start_time is not None:
            logger.error("timer already running")
        else:
            self._start_time = utime.ticks_us()

    def stop(self):
        if self._start_time is None:
            logger.error("no timer running. use .start() to create one")
            return -1
        else:
            _end_time = utime.ticks_us()
            elapsed = utime.ticks_diff(_end_time, self._start_time)
            self._start_time = None
            return elapsed
