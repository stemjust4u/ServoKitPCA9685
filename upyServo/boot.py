# This file is executed on every boot (including wake-boot from deepsleep)
import esp, machine
from mytools import rtcdate
esp.osdebug(None)
#import webrepl
#webrepl.start()

# SET CPU FREQUENCY
CPUFREQ = 240000000  # Can set to 160000000 or 80000000 to save power, but loop time will be much slower
machine.freq(CPUFREQ)

# SET UP REAL TIME CLOCK. EITHER MANUALLY SET DATETIME OR USE LOCAL NETWORK
rtc = machine.RTC()
#rtc.datetime((2021, 5, 6, 0, 12, 55, 0, 0))  # If using local network time comment out rtc.datetime(xxx)
#(year, month, day, weekday, hours, minutes, seconds, subseconds)
print('RTC datetime: {0}'.format(rtcdate(rtc.datetime())))

# TURN ON/OFF SINGLE-MAIN-FILE-LOGGING OPTION
MAIN_FILE_LOGGING = False  # Enable if wanting all modules to write to a single log file. Will use safer 'with' (open/close).
MAIN_FILE_NAME = "complete.log"    # Had to enable 'sync_all_file_types' to get .log files to copy over in pymakr
MAIN_FILE_OW = "w"    # Open with 'w' to start a new log file. Can change to 'a' to keep older logs.
MAIN_FILE_MODE = "a"  # Should be either a or ab append mode (ab for binary)
logfiles = []         # Keep track of log files to monitor size and close them if too big