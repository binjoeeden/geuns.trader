from xcoin_api_client import *
import datetime as dt
from settings import *
import threading

post_fix = ["/public/ticker/",
            "/trade/market_buy",
            "/trade/market_sell",
            "/trade/place",
            "/trade/cancel",
            "/info/order_detail",
            "/info/balance"]

GET_PRC = 0
MKT_BID = 1
MKT_ASK = 2
REQ_ORD = 3
CCL_ORD = 4
CHK_ORD = 5
GET_BAL = 6

MAX_TYPE = CHK_ORD
STR_API_TYPE =['GET_PRC', 'MKT_BID', 'MKT_ASK', 'REQ_ORD', 'CCL_ORD',
               'CHK_ORD', 'GET_BAL']

BID=0
ASK=1

api = XCoinAPI()

LOCK = threading.Lock()
settings = getSettings()
retry_delay = settings['system']['retry_delay']
print("default retry sleep time : "+str(retry_delay))

min_units = {"BTC": 0.001, "ETH": 0.001, "DASH": 0.001, "LTC": 0.01,
        "ETC": 0.1, "XRP": 10, "BCH": 0.001, "XMR": 0.01, "ZEC": 0.01,
        "QTUM": 0.1, "BTG": 0.01, "EOS": 0.1, "ICX":1}

def get_initParam():
    ret = {"payment_currency" : "KRW"}
    return ret

# api_type should be in (GET_PRC, MKT_BID, MKT_ASK, REQ_ORD, CCL_ORD)
def call_api(api_type, crcy, rgParam={}, t_sleep=retry_delay):
    LOCK.acquire()
    if api_type<GET_PRC and api_type>MAX_TYPE:
        print("api_type error")
        return

    rgParam['Payment_currency'] = 'KRW'
    rgParam['order_currency'] = crcy
    if api_type!=REQ_ORD:
        rgParam['currency'] = crcy
    if api_type==GET_PRC:
        if crcy is not None:
            url = post_fix[api_type]+crcy
        else:
            url = post_fix[api_type]+rgParam['crcy']
    else:
        url = post_fix[api_type]

    result={'status':'9999', 'msg':'Unknown'}
    while result['status']!='0000':
        result = api.xcoinApiCall(url,rgParam);
        if result['status']!='0000':
            if api_type==CHK_ORD:
                break
            if api_type==CCL_ORD:
                if 'message' in result.keys():
                    if result['message'].find('진행중이 아닙니다.')>0:
                        break
            print("call_api failed! "+STR_API_TYPE[api_type]+", param:"+str(rgParam))
            print(" result:"+str(result)+"\n - sleep : "+str(t_sleep))
            sleep(t_sleep)

    ret_map = {}
    try:
        ret_map['status'] = result['status']
    except:
        ret_map['status'] = '6666'

    if result['status']=='0000':
        # check order completed
        del ret_map
        ret_map= result
    elif result['status']=='9999':
        ret_map['status']='9999'
    elif result['status']=='5600':
        ret_map['status']= result['status']
    else:
        ret_map['status']= result['status']

    if 'message' in result.keys():
        ret_map['message'] = result['message']
    elif 'msg' in result.keys():
        ret_map['msg'] = result['msg']
    LOCK.release()
    return ret_map

def chk_order(order_id, crcy, bidask, amnt):
    if amnt==0:
        print("chk_order error. amnt is zero.")
        ret = {'result':False, 'status':'divide by zero'}
        return ret
    if bidask == BID:
        bs_type = "bid"
    else:
        bs_type = "ask"
    rgParams = {"order_id":order_id, "type":bs_type,
                "currency":crcy}
    r = call_api(CHK_ORD, crcy, rgParams)
    ret = {'result':False, 'status':r['status']}
    if r['status']=='0000':
        conts = r['data']
        c_amnt=0
        c_krw=0
        c_fee=0
        tr_ts_max = 0
        prc = 0
        for e_cont in conts:
            c_amnt += float(e_cont['units_traded'])
            c_fee += float(e_cont['fee'])
            c_krw += int(e_cont['total'])
            tr_ts = int(e_cont['transaction_date'])/1000000
            if tr_ts_max<tr_ts:
                tr_ts_max = tr_ts
            if prc==0:
                prc = int(e_cont['price'])
        diff = abs(amnt-c_amnt)

        if diff/amnt < 0.02:
            ret['result']=True
            ret['amnt'] = c_amnt
            ret['krw'] = c_krw
            ret['fee'] = c_fee
            ret['prcs'] = prc
            ts = dt.datetime.fromtimestamp(tr_ts_max)
            (ret['date'], ret['time']) = get_date_time(ts)
    elif r['status']=='9999':
        ret['msg'] = r['msg']
    elif r['status']=='5600':
        ret['msg'] = r['message']
    else:
        ret['msg'] = 'Unknown'
    return ret

def ccl_order(order_id, crcy, bidask):
    if bidask == BID:
        bs_type = "bid"
    else:
        bs_type = "ask"
    rgParams = {"order_id":order_id, "type":bs_type, "currency":crcy}
    r = call_api(CCL_ORD, crcy, rgParams)
    return r
