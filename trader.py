from settings import *
from rest_api import *
# from db_serv import *
from db_handler import *
import threading
import datetime as dt

# r = call_api(GET_PRC, {}, 'ZEC')
# print(r['data']['sell_price'])
# BTC,ETH,XRP,BCH,LTC,EOS,DASH,XMR,ETC,QTUM, BTG,ZEC

prcs = {}

class Main(threading.Thread):
    global prcs
    empty_slot={'bid_order_id':'', 'crcy':'', 'c_date':0, 'c_time':0,
                'num_of_bid':0, 'total_bid_amnt':0, 'bid_krw':0, 'avr_prc':0,
                'ask_yn':'N', 'profit_rt':0, 'profit_krw':0, 'ask_amnt':0,
                'ask_krw':0, 'next_bid_prc':0, 'next_bid_amnt':0,
                'next_bid_order_id':'' , 'ask_order_id':'', 'ask_prc':0}
    def __init__(self):
        threading.Thread.__init__(self)
        # update settings & config
        self.update_configs()
        # init db service
        #self.db = get_db_serv(self.db_name)
        self.db = DB_Handler(self.db_name)

        self.mutex = threading.Lock()
        print(min_units)

        self.init_status()
        self.init_slots()

        self.paused = True
        self.daemon = True
        self.state = threading.Condition()
        self.update_exec_yn()

        # get curr. prices for init.
        self.prcs = {}
        for crcy in self.crcy_list:
            r = call_api(GET_PRC, crcy)
            handle_result = self.api_result_to_db(crcy, r)
            print("crcy : "+str(self.prcs[crcy]))

        # first bid
        not_bid = self.crcy_list.copy()
        while len(not_bid)>0:
            for crcy in self.crcy_list:
                if len(self.slots[crcy])>0:
                    if crcy in not_bid:
                        not_bid.remove(crcy)
                    continue
                if len(self.slots[crcy])==0:
                    bid_krw = self.coin_config[crcy]['first_slot_krw']
                    prc = self.prcs[crcy][ASK_PRC]
                    amnt = ceil(bid_krw/prc, 4)
                    new_slot=self.make_new_bid(crcy, prc, amnt)
                    not_bid.remove(crcy)

        print(self.coin_config)
        # TODO Resume Slot & order history

        pass


    def update_configs(self):
        self.setting = getSettings()
        self.coin_config = getCoinConfig()
        self.system = self.setting['system']
        self.db_name = self.system['db_file_name']
        self.sleep_period = self.system['sleep_period']
        self.retry_delay = self.system['retry_delay']
        self.crcy_list = self.coin_config['crcy_list']
        return

    def init_status(self):
        self.status = {}
        empty_status={'next_slot_bid_id':'', 'total_krw':0,
                      'total_bid_amnt':0, 'curr_slot_num':0, 'avr_prc':0,
                      'total_earning_ask' : 0}

        for crcy in self.crcy_list:
            self.status[crcy] = empty_status.copy()
            self.status[crcy]['crcy'] = crcy

        self.resume_status()
        return

    def resume_status(self):
        for crcy in self.crcy_list:
            result = self.db.req_db('s_status', (crcy,))
            print("result of s_status : "+str(result))
            if result is False or len(result)==0:
                print("no resume status.")
            else:
                for e in result:
                    crcy = e[0]
                    target = self.status[crcy]
                    if crcy != e[0]:
                        print("resume status error : "+crcy+"<->"+e[0])
                    target['curr_slot_num'] = e[1]
                    target['next_slot_bid_id'] = e[2]
                    target['total_krw'] = e[3]
                    target['total_bid_amnt'] = e[4]
                    target['avr_prc'] = e[5]
                    target['total_earning_ask'] = e[6]
                    self.status[crcy] = target
        print("resume status : "+str(self.status))

    def init_slots(self):
        self.slots={}

        for crcy in self.crcy_list:
            self.slots[crcy] = []
        #        self.slots[crcy].append(empty_slot.copy())
            slots = self.db.req_db('s_slot', (crcy, ))
            # validation check
            for slot in slots:
                print("resume slot : "+str(slot))
                token = {}
                token['bid_order_id'] = slot[0]
                token['crcy'] = slot[1]
                token['c_date'] = slot[2]
                token['c_time'] = slot[3]
                token['num_of_bid'] = slot[4]
                if token['num_of_bid']==0:
                    token['bid_order_id'] = self.status[crcy]['next_slot_bid_id']
                token['total_bid_amnt'] = slot[5]
                token['bid_amnt'] = slot[6]
                token['bid_prc'] = slot[7]
                token['bid_krw'] = slot[8]
                token['avr_prc'] = slot[9]
                token['ask_yn'] = slot[10]
                token['profit_rt'] = slot[11]
                token['profit_krw'] = slot[12]
                token['ask_amnt'] = slot[13]
                token['ask_krw'] = slot[14]
                token['next_bid_prc'] = slot[15]
                token['next_bid_amnt'] = slot[16]
                token['next_bid_order_id'] = slot[17]
                token['ask_order_id'] = slot[18]
                token['ask_prc'] = slot[19]
                self.slots[crcy].append(token)

            print("resume slots of "+crcy)
            print(self.slots[crcy])

    def run(self):
        is_continue=True
        self.db.req_db('u_exec', ('Y',))
        self.update_exec_yn()
        print_yn = False
        while is_continue:
            if self.paused is False:
                self.go()
                if print_yn is True:
                    print("execution!")
                    print_yn=False
            else:
                if print_yn==False:
                    print("not execution!")
                    print_yn=True
            self.update_status()
            sleep(self.sleep_period)
            self.update_exec_yn()

        input("End of trading...press any key to exit..\n")

    def update_exec_yn(self):
        r = self.db.req_db('s_exec', None)
        if r[0][0].upper()=='Y':
            self.paused=False
        else:
            self.paused=True

    # def resume(self):
    #     with self.state:
    #         self.db.req_db('u_exec', ('Y',))
    #         self.paused = False
    #         self.state.notify()
    #
    # def pause(self):
    #     with self.state:
    #         self.db.req_db('u_exec', ('N',))
    #         self.paused = True

    def go(self):
        print(self.crcy_list)
        self.update_configs()

        # get price
        not_prc_crcys = self.crcy_list.copy()
        # prcs_ts = {}
        while len(not_prc_crcys)>0:
            for crcy in self.crcy_list:
                # get prc
                r = call_api(GET_PRC, crcy, {}, self.retry_delay)
                handle_result = self.api_result_to_db(crcy, r)
                if handle_result is False:
                    print("get prc / insert db error : "+crcy)
                    print("sleep:"+str(self.retry_delay))
                    sleep(self.retry_delay)
                    continue
                else:
                    prcs = self.prcs[crcy]
                    print("["+get_ts((prcs[DATE], prcs[TIME]))+":"+crcy+"] "+ str(prcs[PRC]))
                    # prcs_ts[crcy] = (self.prcs[crcy][DATE], self.prcs[crcy][TIME])
                    not_prc_crcys.remove(crcy)

        # check each slot
        for crcy in self.crcy_list:
            first_bid_yn = False
            self.is_continue_update_slots = True
            print("check each slot. num of slots : "+str(len(self.slots[crcy])))
            for s in self.slots[crcy]:
                if self.is_continue_update_slots is False:
                    break
                if s['ask_yn']=='Y':
                    continue

                # check previous ask order
                if s['ask_order_id']!='' and s['ask_yn']!='Y':
                    ts = get_ts((s['c_date'], s['c_time']))
                    print(get_ts(get_date_time())+"] "+"[c_ts-"+ts+":"+crcy+"] chk ASK : "+str(s))
                    rpa = chk_order(s['ask_order_id'], crcy, ASK, s['ask_amnt'])
                    if rpa['result'] is True:
                        print("ask complete!")
                        self.handle_ask_completed(s, rpa)
                        ## goto update slots of next crcy
                        continue

                # check bid order
                bid_amnt = 0
                if s['bid_order_id']!='' and s['next_bid_order_id']=='':
                    bid_order_id = s['bid_order_id']
                    bid_amnt = s['bid_amnt']
                    if s['num_of_bid'] !=0 or s['c_date']!=0 or s['c_time']!=0:
                        print("[DEBUG] new slot case. but error :: "+str(s))

                else:
                    bid_order_id = s['next_bid_order_id']
                    bid_amnt = s['next_bid_amnt']

                if bid_order_id!='':
                    ts = get_ts((s['c_date'], s['c_time']))
                    print(get_ts(get_date_time())+"] "+"[c_ts-"+ts+":"+crcy+"] chk BID : "+str(s))
                    r = chk_order(bid_order_id, crcy, BID, bid_amnt)
                    if r['result'] is True:
                        bid_prc = r['prcs']
                        print("bid complete!")
                        self.handle_bid_completed(s, r, bid_prc)

            is_continue_del=True
            while is_continue_del:
                for s in self.slots[crcy]:
                    if s['ask_yn']=='Y':
                        self.slots[crcy].remove(s)
                        break
                else:
                    is_continue_del = False


    def update_status(self):

        for crcy in self.crcy_list:
            total_krw = 0
            total_bid_amnt = 0
            avr_prc = 0
            total_earning_ask = 0
            total_loss = 0
            for s in self.slots[crcy]:
                # status 갱신
                if s['ask_yn']=='N':
                    total_krw += (s['avr_prc']*s['total_bid_amnt'])
                    total_bid_amnt += s['total_bid_amnt']
                    if total_bid_amnt==0:
                        avr_prc = 0
                    else:
                        avr_prc = total_krw / total_bid_amnt
                    curr_krw = self.prcs[crcy][PRC] * total_bid_amnt
                    total_loss += curr_krw - s['bid_krw']


            r_db = self.db.req_db('s_slot_ac', (crcy,))
            for e in r_db:
                total_earning_ask += e[12]

            self.status[crcy]['total_earning_ask'] = total_earning_ask
            if total_bid_amnt !=0:
                self.status[crcy]['total_krw'] = total_krw
                self.status[crcy]['total_bid_amnt'] = total_bid_amnt
                self.status[crcy]['avr_prc'] = total_krw / total_bid_amnt
            else:
                self.status[crcy]['total_krw'] = 0
                self.status[crcy]['total_bid_amnt'] = 0
                self.status[crcy]['avr_prc'] = 0
            db_token = self.get_db_token('iu_status', self.status[crcy])
            self.db.req_db('iu_status', db_token)
            sleep(0.05)

    def get_db_token(self, p_type, p):
        token = ()
        if p_type=='u_slot':
            token = (p['c_date'], p['c_time'],
                     p['num_of_bid'], p['total_bid_amnt'], p['bid_amnt'], p['bid_prc'], p['bid_krw'],
                     p['avr_prc'], p['ask_yn'], p['profit_rt'],
                     p['profit_krw'], p['ask_amnt'], p['ask_krw'],
                     p['next_bid_prc'], p['next_bid_amnt'],
                     p['next_bid_order_id'], p['ask_order_id'],
                     p['ask_prc'], p['bid_order_id'], p['crcy'])
        elif p_type=='d_slot':
            token = (p['bid_order_id'], p['crcy'])
        elif p_type=='i_slot':
            token = (p['bid_order_id'], p['crcy'], p['c_date'], p['c_time'],
                     p['num_of_bid'], p['total_bid_amnt'], p['bid_amnt'], p['bid_prc'], p['bid_krw'],
                     p['avr_prc'], p['ask_yn'], p['profit_rt'], p['profit_krw'],
                     p['ask_amnt'], p['ask_krw'], p['next_bid_prc'],
                     p['next_bid_amnt'], p['next_bid_order_id'],
                     p['ask_order_id'], p['ask_prc'])
        elif p_type=='iu_status':
            token = (p['crcy'], p['curr_slot_num'], p['next_slot_bid_id'],
                     p['total_krw'], p['total_bid_amnt'], p['avr_prc'],
                     p['total_earning_ask'])
        return token

    # 빗썸으로부터 읽어온 rest api 시세 결과를 self.prcs[crcy]에 저장하고
    # crcy_prc DB 테이블에 insert 한다.
    def api_result_to_db(self, crcy, r):
        # insert to DB
        (date, time) = get_date_time()

        rd = r['data']
        self.prcs[crcy] = (date, time, crcy, int(rd['closing_price']),
                 int(rd['buy_price']), int(rd['sell_price']))

        return (self.db.req_db('i_prc', self.prcs[crcy]))

    def make_new_slot_bid(self, crcy, prc):
        if len(self.slots[crcy])==0:
            bid_krw = self.coin_config[crcy]['first_slot_krw']
        else:
            bid_krw = self.coin_config[crcy]['slot_krw']
        if prc==0:
            print("1.prc : 0")
            return None
        amnt = ceil(bid_krw/prc, 4)
        # request bid of new slot
        r = call_api(REQ_ORD, crcy, {'units':amnt,
                                     'price':prc,
                                     'type':'bid'}, self.retry_delay)

        self.status[crcy]['next_slot_bid_id'] = r['order_id']
        slot = self.empty_slot.copy()
        slot['bid_order_id'] = r['order_id']
        slot['crcy'] = crcy
        slot['bid_amnt'] = amnt
        slot['bid_prc'] = prc
        print("set bid_amnt :"+str(amnt)+", slot:"+str(slot)+"\n")
        self.slots[crcy].append(slot)
        db_token = self.get_db_token('i_slot', slot)
        self.db.req_db('i_slot', db_token)
        return slot

    def update_new_slot_bid(self, crcy, prc):
        if len(self.slots[crcy])==0:
            bid_krw = self.coin_config[crcy]['first_slot_krw']
        else:
            bid_krw = self.coin_config[crcy]['slot_krw']

        if prc==0:
            print("1.prc : 0")
            return None
        amnt = ceil(bid_krw/prc, 4)
        return self.make_new_bid(crcy, prc, amnt)

    def make_new_bid(self, crcy, prc, amnt, slot=None):
        # cancel previous bid of new slot
        order_id = self.status[crcy]['next_slot_bid_id']
        prev_new_slot = None
        if slot is None and order_id!='':
            print(crcy+"] cancel order to delete bid of new slot ")
            ccl_order(order_id, crcy, BID)
            print("erase the slot ")
            for s in self.slots[crcy]:
                if s['bid_order_id'] == order_id:
                    prev_new_slot = s
                    break

        # request bid of new slot
        r = call_api(REQ_ORD, crcy, {'units':amnt,
                                     'price':prc,
                                     'type':'bid'}, self.retry_delay)
        if slot is None:
            self.status[crcy]['next_slot_bid_id'] = r['order_id']
            if order_id=='':
                slot = self.empty_slot.copy()
                slot['bid_order_id'] = r['order_id']
                slot['crcy'] = crcy
                slot['bid_amnt'] = amnt
                slot['bid_prc'] = prc
                print("set bid_amnt :"+str(amnt)+", slot:"+str(slot)+"\n")
                self.slots[crcy].append(slot)
                db_token = self.get_db_token('i_slot', slot)
                self.db.req_db('i_slot', db_token)
            elif prev_new_slot is not None:

                # delete previous slot
                self.db.req_db('d_slot', (prev_new_slot['bid_order_id'], crcy,))
                print("update bid of prev. new slot ")
                prev_new_slot['bid_order_id'] = r['order_id']
                prev_new_slot['bid_amnt'] = amnt
                prev_new_slot['bid_prc'] = prc
                db_token = self.get_db_token('i_slot', prev_new_slot)
                self.db.req_db('u_slot', db_token)
                slot = prev_new_slot
            else:
                pass
        else:
            slot['next_bid_order_id'] = r['order_id']
        return slot


    def handle_ask_completed(self, s, r):
        if s['ask_yn'] == 'Y':
            return
        crcy = s['crcy']
        s['ask_krw'] = r['krw'] - r['fee']

        if s['next_bid_order_id']=='':
            print("error : s['next_bid_order_id']==null?? "+str(s))
        else:
            ccl_order(s['next_bid_order_id'], crcy, BID)

        if s['ask_amnt']!=min_units[crcy] and s['ask_amnt']>s['total_bid_amnt']*0.9:
            s['ask_yn'] = 'Y'
            s['profit_krw'] = s['ask_krw'] - s['bid_krw']
            s['profit_rt'] = s['profit_krw'] / s['bid_krw']
            # s['next_bid_prc'] = 0   # necessary ?
            # s['next_bid_amnt'] = 0  # necessary ?
            s['ask_order_id'] = ''
            self.status[crcy]['curr_slot_num'] = self.status[crcy]['curr_slot_num']-1
        else:
            print("ask is last one")
            # s['ask_yn'] = 'N'
            s['bid_prc'] = s['ask_prc']
            s['avr_prc'] = s['bid_prc']
            s['total_bid_amnt'] -= s['ask_amnt']
            s['bid_krw'] = s['total_bid_amnt']*s['bid_prc']
            s['next_bid_prc'] =  ceil_krw(int(s['ask_prc'] * (1-self.coin_config[crcy]['add_bid_rate'])), self.coin_config[crcy]['min_amnt_krw'])
            s['next_bid_amnt'] = ceil(s['bid_krw'] / s['next_bid_prc'], 4)  # necessary ?
            s['profit_krw'] += s['ask_krw']
            # s['profit_rt'] = (s['bid_krw']+s['profit_krw']) / s['bid_krw']
            s['profit_rt'] = s['profit_krw'] / self.coin_config[crcy]['first_slot_krw']

            print(crcy+"] make next bid of current slot : "+str(s))
            self.make_new_bid(crcy, s['next_bid_prc'], s['next_bid_amnt'], s)

            # ask next one
            next_ask_prc = s['bid_prc']*(1+self.coin_config[crcy]['good_ask_rt'])+self.coin_config[crcy]['min_amnt_krw']
            s['ask_prc'] = ceil_krw(next_ask_prc, self.coin_config[crcy]['min_amnt_krw'])
            ask_krw = s['ask_prc'] * s['total_bid_amnt']
            profit_krw = ask_krw - s['bid_krw']
            ask_amnt = ceil(profit_krw / s['ask_prc'], 4)
            # check minimum amount
            if ask_amnt<min_units[crcy]:
                ask_amnt = min_units[crcy]
            s['ask_krw']  = ask_amnt * s['ask_prc']
            s['ask_amnt'] = ask_amnt
            rgParam =  {'units':s['ask_amnt'], 'price':s['ask_prc'], 'type':'ask'}
            print(crcy+"] set next good ask order : "+str(rgParam))
            ra = call_api(REQ_ORD, crcy, rgParam, self.retry_delay)
            s['ask_order_id'] = ra['order_id']

        # update earnings by ask
        # self.status[crcy]['total_earning_ask'] += s['profit_krw']

        db_token = self.get_db_token('u_slot', s)
        # update db
        self.db.req_db('u_slot', db_token)

        ## update bid of new slot
        next_slot_bid_prc = ceil_krw(int(s['bid_prc'] * (1-self.coin_config[crcy]['new_slot_gap'])), self.coin_config[crcy]['min_amnt_krw'])
        slot = self.update_new_slot_bid(crcy, next_slot_bid_prc)
        if slot is None:
            print("not bid !!! ask prc : "+str(s['ask_prc'])+", "+int(s['ask_prc'] * (1-self.coin_config[crcy]['new_slot_gap'])))
            raise Exception('error')

        if s['ask_yn'] == 'Y':
            print("NOT last ask complete condition! ask_yn:Y")
        else:   # if last slot of this crcy
            print("Last ask complete condition! ask_yn:N")
            next_bid_prc =  s['ask_prc'] * (1-self.coin_config[crcy]['new_slot_gap'])
            self.status[crcy]['next_bid_prc'] = next_bid_prc

        if self.status[crcy]['curr_slot_num']==1:
            # 마지막 slot 매도를 분할 매도로 변경
            for ss in self.slots[crcy]:
                if ss['ask_yn']=='N' and ss['ask_order_id']!='' and ss['ask_amnt']>ss['total_bid_amnt']*0.9:
                    print("change ask of last slot. cancel amnt,prc:"+str(ss['ask_amnt'])+", "+str(ss['ask_prc']))
                    ccl_order(ss['ask_order_id'], crcy, ASK)
                    profit_krw = ss['ask_krw']-ss['bid_krw']
                    ss['ask_amnt'] = ceil(profit_krw / ss['ask_prc'], 4)
                    if ss['ask_amnt']<min_units[crcy]:
                        ss['ask_amnt'] = min_units[crcy]
                    rgParam =  {'units':ss['ask_amnt'], 'price':ss['ask_prc'], 'type':'ask'}
                    print("new ask - amnt,prc:"+str(ss['ask_amnt'])+", "+str(ss['ask_prc']))
                    rr = call_api(REQ_ORD, crcy, rgParam, self.retry_delay)
                    ss['ask_order_id'] = rr['order_id']
                    ss['ask_krw']  = ss['ask_amnt'] * ss['ask_prc']
                    # update to slot DB
                    db_token = self.get_db_token('u_slot', ss)
                    # update db
                    self.db.req_db('u_slot', db_token)
                    break
            else:
                print("ERROR : not found last one. need to change last ask order !!!")


    def handle_bid_completed(self, s, r, bid_prc):
        print('bid complete. 가격:'+str(bid_prc)+", 주문수량:"+str(s['bid_amnt'])+', 체결수량:'+str(r['amnt'])+', 체결금액:'+str(r['krw'])+', 수수료 수량:'+str(r['fee']))
        (date, time) = get_date_time()
        crcy = s['crcy']
        if s['num_of_bid']==0:
            s['c_date'] = r['date']
            s['c_time'] = r['time']
            self.status[crcy]['curr_slot_num'] = self.status[crcy]['curr_slot_num']+1
            self.status[crcy]['next_slot_bid_id'] = ''

        s['num_of_bid'] = s['num_of_bid']+1
        if s['num_of_bid']>2:
            adj_good_ask_rt = (s['num_of_bid']-2)*self.coin_config[crcy]['adj_good_ask_rt']
            adj_bid_rt = (s['num_of_bid']-2)*self.coin_config[crcy]['adj_add_bid_rt']
        else:
            adj_good_ask_rt = 0
            adj_bid_rt = 0

        s['total_bid_amnt'] = s['total_bid_amnt'] + r['amnt'] - r['fee']
        s['bid_krw'] = s['bid_krw']+r['krw']
        s['avr_prc'] = s['bid_krw'] / s['total_bid_amnt']
        s['next_bid_prc'] = ceil_krw(int(bid_prc * (1-self.coin_config[crcy]['add_bid_rate']-adj_bid_rt)), self.coin_config[crcy]['min_amnt_krw'])
        print(crcy+"] next_bid_prc : "+ str(s['next_bid_prc']))
        s['next_bid_order_id'] = ''
        s['next_bid_amnt'] = ceil(s['bid_krw'] / s['next_bid_prc'], 4)
        s['ask_amnt'] = ceil(s['total_bid_amnt'], 4)
        ask_prc = s['avr_prc']*(1+self.coin_config[crcy]['good_ask_rt']+adj_good_ask_rt)
        s['ask_prc'] = ceil_krw(round(ask_prc,0), self.coin_config[crcy]['min_amnt_krw'])
        s['ask_krw'] = s['ask_prc'] * s['ask_amnt']

        # cancel prvious ask order
        if s['ask_order_id']!='':
            print("cancel previous ask order (id:"+s['ask_order_id']+")")
            ccl_order(s['ask_order_id'], s['crcy'], ASK)
            s['ask_order_id']=''

        # request good ask order
        if self.status[crcy]['curr_slot_num']==1:
            # 일부만 익절: update s[update ask_amnt], s[ask_krw]
            min_amnt = min_units[crcy]
            ask_krw = s['ask_prc'] * s['ask_amnt']
            profit_krw = ask_krw - s['bid_krw']
            ask_amnt = ceil(profit_krw / s['ask_prc'], 4)
            # check minimum amount
            if ask_amnt<min_amnt:
                ask_amnt = min_amnt
            s['ask_krw']  = ask_amnt * ask_prc
            s['ask_amnt'] = ask_amnt
        rgParam =  {'units':s['ask_amnt'], 'price':s['ask_prc'], 'type':'ask'}
        print(crcy+"] set next good ask order : "+str(rgParam))
        ra = call_api(REQ_ORD, crcy, rgParam, self.retry_delay)
        s['ask_order_id'] = ra['order_id']

        # update next bid order
        print("make new bid of this slot (prc, amnt) : "+str(s['next_bid_prc'])+", "+str(s['next_bid_amnt']))
        if self.coin_config[crcy]['min_prc']>0 and s['next_bid_prc']>self.coin_config[crcy]['min_prc']:
            self.make_new_bid(crcy, s['next_bid_prc'], s['next_bid_amnt'], s)

        # update to slot DB
        db_token = self.get_db_token('u_slot', s)
        # update db
        self.db.req_db('u_slot', db_token)

        # make & update bid of new slot
        next_slot_bid_prc = ceil_krw(int(bid_prc * (1-self.coin_config[crcy]['new_slot_gap'])), self.coin_config[crcy]['min_amnt_krw'])
        if self.coin_config[crcy]['min_prc']>0 and next_slot_bid_prc>self.coin_config[crcy]['min_prc']:
            if s['num_of_bid']==1:
                self.make_new_slot_bid(crcy, next_slot_bid_prc)
            else:
                self.update_new_slot_bid(crcy, next_slot_bid_prc)
        else:
            print("can't next bid prc :"+str(next_slot_bid_prc)+", min prc : "+str(self.coin_config[crcy]['min_prc']))
        return

if __name__ == "__main__":
    a = Main()
    a.daemon = True
    a.start()
    a.join()
