class pcolor:
    ''' Add color to print statements '''
    LBLUE = '\33[36m'   # Close to CYAN
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    DBLUE = '\33[34m'
    WOLB = '\33[46m'    # White On LightBlue
    LPURPLE = '\033[95m'
    PURPLE = '\33[35m'
    WOP = '\33[45m'     # White On Purple
    GREEN = '\033[92m'
    DGREEN = '\33[32m'
    WOG = '\33[42m'     # White On Green
    YELLOW = '\033[93m'
    YELLOW2 = '\33[33m'
    RED = '\033[91m'
    DRED = '\33[31m'
    WOR = '\33[41m'     # White On Red
    BOW = '\33[7m'      # Black On White
    BOLD = '\033[1m'
    ENDC = '\033[0m'

def rtcdate(tpl):
    return "{:4}-{}-{} {:2}:{:02d}:{:02d}.{}".format(tpl[0], tpl[1], tpl[2], tpl[4], tpl[5], tpl[6], tpl[7])

def localdate(tpl):
    return "{:4}-{}-{} {:2}:{:02d}:{:02d}".format(tpl[0], tpl[1], tpl[2], tpl[3], tpl[4], tpl[5])

'''
localtime = (2021, 5, 6, 12, 55, 0, 0, 0) #(year, month, day, hour, minute, second, weekday, yearday)
print(utime.time())    # integer, seconds since 1/1/2000, returned from RTC.  Add hrs*3600 for adjustment
print((utime.localtime()))   # current time from RTC is returned. If seconds/integer is passed to it it converts to 8-tuple
print(localdate((utime.localtime())))

86400 seconds in a day, 3600 seconds in an hour

t =utime.mktime((2018,8,16,22,0,0,3,0))  # enter a 8-tuple which expresses time as per localtime. mktime returns an integer, number of seconds since 1/1/2000
t += 4*3600
utime.localtime(t)
or
utime.localtime(utime.mktime(utime.localtime()) + 3*3600)
'''