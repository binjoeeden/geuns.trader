import datetime as dt

# constant 1. prices
DATE = 0
TIME = 1
CRCY = 2
PRC  = 3
BID_PRC = 4
ASK_PRC = 5

# constant 2. index of earning coin info
EARN_COIN_AMNT = 13
EARN_COIN_AVR_KRW = 14
EARN_COIN_CURR_KRW = 15

EARN_COIN_AMNT_M_ASK = 13
EARN_COIN_AVR_KRW_M_ASK = 14
EARN_COIN_CURR_KRW_M_ASK = 15


def cout(*args):
    global event_type
    if event_type==RELEASE:
        pass
    else:
        print(args)

# XML indent function
def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem

def get_weekday_string(weekday):
    if weekday==0:
        return "Mon"
    elif weekday==1:
        return "Tue"
    elif weekday==2:
        return "Wed"
    elif weekday==3:
        return "Thu"
    elif weekday==4:
        return "Fri"
    elif weekday==5:
        return "Sat"
    elif weekday==6:
        return "Sun"
    return "week:"+str(weekday)

def ceil(a, b):
    d = int((a* (10**b)))/(10**b)
    return d

def ceil_krw(a,b):
    d = int(int(a/b)*b)
    print("krw : "+str(a)+", min_amnt_krw:"+str(b)+", result : "+str(d))
    return d

def get_date_time(ts=None):
    if ts is None:
        ts = dt.datetime.now()
    date = int(ts.year*10000+ts.month*100+ts.day)
    time = int(ts.hour*10000+ts.minute*100+ts.second)
    return (date, time)

def get_ts_slot(e):
    if type(e) is not tuple or len(e)!=2:
        return ''
    date = e[0]
    time = e[1]
    yy = int(date/10000)
    mmdd = date-yy*10000
    mm = int(mmdd/100)
    dd = int(mmdd-mm*100)
    c_date = str(yy%100)+"/"+str(mm)+"/"+str(dd)
    hh = int(time/10000)
    MMss = time-hh*10000
    MM = int(MMss/100)
    ss = int(MMss-MM*100)
    c_time = str(hh)+":"+str(MM)
    return c_date+" "+c_time

def get_ts(e):
    if type(e) is not tuple or len(e)!=2:
        return ''
    date = e[0]
    time = e[1]
    yy = int(date/10000)
    mmdd = date-yy*10000
    mm = int(mmdd/100)
    dd = int(mmdd-mm*100)
    c_date = str(yy)+"/"+str(mm)+"/"+str(dd)
    hh = int(time/10000)
    MMss = time-hh*10000
    MM = int(MMss/100)
    ss = int(MMss-MM*100)
    c_time = str(hh)+":"+str(MM)+":"+str(ss)
    return c_date+" "+c_time

def get_num_from_str(str_num):
    return float(str_num.strip().replace(',',''))
