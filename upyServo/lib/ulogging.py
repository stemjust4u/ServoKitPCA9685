from boot import MAIN_FILE_LOGGING, MAIN_FILE_MODE, MAIN_FILE_NAME, logfiles
import sys, uos
from machine import Timer

CRITICAL = 50
ERROR    = 40
WARNING  = 30
INFO     = 20
DEBUG    = 10
NOTSET   = 0

_level_dict = {
    CRITICAL: "CRIT",
    ERROR: "ERROR",
    WARNING: "WARN",
    INFO: "INFO",
    DEBUG: "DEBUG",
}

_stream = sys.stderr

# To print_stream to a file pass file in basicConfig
#_stream = open('main.log', 'w')
#print(msg % args, file=_stream)
#_stream.close()

class Logger:

    level = NOTSET

    def __init__(self, name, logfile, fmode, autoclose, filetime):
        self.name = name
        self.fileopen = False
        self.logfile = logfile
        self.mode = fmode
        self.autoclose = autoclose
        if self.logfile is not None and MAIN_FILE_LOGGING: # If all modules writing to a single file use 'with' context manager
            self.logfile = MAIN_FILE_NAME 
            self.mode = MAIN_FILE_MODE
            self.fileopen = True
            self.autoclose = True   # Must use autoclose ("with" file) method with MAIN FILE LOGGING
        elif self.logfile is not None and autoclose:       # Open/close safely using 'with' context manager
            with open(self.logfile, self.mode) as f:
                f.write("Initialize file: {0} Initial mode was: {1}\n".format(self.logfile, self.mode))
            self.mode = 'a'      # Will append remaining log results
            self.fileopen = True
        elif self.logfile is not None and not autoclose:   # If this is only module writing to file then leave file open and use timer to close based on 'filetime' setting
            timer = Timer(0)
            timer.init(period=filetime, mode=Timer.ONE_SHOT, callback=self._debug_closef_exit)
            self.f = open(self.logfile, self.mode)
            self.fileopen = True
    def _level_str(self, level):
        l = _level_dict.get(level)
        if l is not None:
            return l
        return "LVL%s" % level

    def setLevel(self, level):
        self.level = level

    def isEnabledFor(self, level):
        return level >= (self.level or _level)

    def log(self, level, msg, *args):
        if level >= (self.level or _level):
            if self.fileopen and self.autoclose:
                with open(self.logfile, self.mode) as self.f:   # If multiple modules writing to file then open/close file safely
                    self.f.write("%s,%s," % (self._level_str(level), self.name))
                    if not args:
                        self.f.write("{0}\n".format(msg))
                    else:
                        self.f.write(msg % args)
            elif self.fileopen and not self.autoclose:          # If single module writing to file then leave file open for faster writes. Doesn't work with multiple files
                self.f.write("%s:%s:" % (self._level_str(level), self.name))
                if not args:
                    self.f.write("{0}\n".format(msg))
                else:
                    self.f.write(msg % args)
            else:
                _stream.write("%s:%s:" % (self._level_str(level), self.name))
                if not args:
                    print(msg, file=_stream)
                else:
                    print(msg % args, file=_stream)

    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)

    def info(self, msg, *args):
        self.log(INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(WARNING, msg, *args)

    def error(self, msg, *args):
        self.log(ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)

    def exc(self, e, msg, *args):
        self.log(ERROR, msg, *args)
        sys.print_exception(e, _stream)

    def exception(self, msg, *args):
        self.exc(sys.exc_info()[1], msg, *args)

    def _debug_closef_exit(self, timer):
        self.f.close()


_level = INFO
_loggers = {}

def getLogger(name, file=None, mode='wb', autoclose=True, filetime=2000):
    if name in _loggers:
        return _loggers[name]
    l = Logger(name, file, mode, autoclose, filetime)
    _loggers[name] = l
    #print('name:{0} dict:{1}'.format(name, _loggers))
    return l

def info(msg, *args):
    getLogger(None).info(msg, *args)

def debug(msg, *args):
    getLogger(None).debug(msg, *args)

def basicConfig(level=INFO, filename=None, stream=None, format=None):
    global _level, _stream
    _level = level
    if stream:
        _stream = stream
    if filename is not None:
        print("logging.basicConfig: filename arg is not supported")
    if format is not None:
        print("logging.basicConfig: format arg is not supported")