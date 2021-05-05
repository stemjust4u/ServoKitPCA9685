import esp, machine, utime
esp.osdebug(None)
#import webrepl
#webrepl.start()

if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    print('woke from a deep sleep')

machine.freq(240000000)
cpufreqi = machine.freq()/(10**9)
print('cpu: {0}GHz'.format(cpufreqi))

logfiles = []   # Keep track of log files to monitor size and close them if too big
MAIN_FILE_LOGGING = False  # Enable if wanting all modules to write to a single log file. Will use safer 'with' (open/close).
MAIN_FILE_NAME = "complete.log"    # Had to enable 'sync_all_file_types' to get .log files to copy over in pymakr
MAIN_FILE_MODE = "a"       # Should be either a or ab append mode
initial_open_mode = "w"    # Open with 'w' to start a new log file. Can change to 'a' to keep older logs.
if MAIN_FILE_LOGGING:
    with open(MAIN_FILE_NAME, initial_open_mode) as f:
        f.write("cpu freq: {0} GHz\n".format(cpufreqi/10**9)) 
        f.write("All module debugging will write to file: {0} with mode: {1}\n".format(MAIN_FILE_NAME, MAIN_FILE_MODE))
        if machine.reset_cause() == machine.DEEPSLEEP_RESET:
            f.write('{0}, woke from a deep sleep'.format(utime.localtime()))
    print("All module debugging will write to file: {0} with mode: {1}\n".format(MAIN_FILE_NAME, MAIN_FILE_MODE))
    logfiles.append(MAIN_FILE_NAME)