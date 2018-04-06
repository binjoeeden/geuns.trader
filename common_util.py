import datetime as dt

# constant 1. prices
DATE = 0
TIME = 1
CRCY = 2
PRC  = 3
BID_PRC = 4
ASK_PRC = 5


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
    date = ts.year*10000+ts.month*100+ts.day
    time = ts.hour*10000+ts.minute*100+ts.second
    return (date, time)

def get_ts(e):
    if type(e) is not tuple or len(e)!=2:
        return ''
    date = e[0]
    time = e[1]
    yy = int(date/10000)
    mmdd = date-yy*10000
    mm = int(mmdd/100)
    dd = mmdd-mm*100
    c_date = str(yy)+"/"+str(mm)+"/"+str(dd)
    hh = int(time/10000)
    MMss = time-hh*10000
    MM = int(MMss/100)
    ss = MMss-MM*100
    c_time = str(hh)+":"+str(MM)+":"+str(ss)
    return c_date+" "+c_time
