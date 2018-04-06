import sqlite3 as db
from time import sleep
from common_util import *

# SLOT TABLE
SLT_B_ORDER_ID = 0
SLT_CRCY = 1
SLT_C_DATE = 2
SLT_C_TIME = 3
SLT_NUM_OF_BID = 4
SLT_T_BID_AMNT = 5
SLT_T_BID_KRW = 6
SLT_AVR_PRC = 7
SLT_ASK_YN = 8
SLT_PROFIT_RT = 9
SLT_PROFIT_KRW = 10
SLT_ASK_AMNT = 11
SLT_ASK_KRW = 12
SLT_NXT_B_PRC = 13



class DB_Handler:
    def __init__(self, dbname):
        self.dbname = dbname

    def req_db(self, query_type, values=None):
        sql = None
        if query_type =='i_prc':
            sql = ''' INSERT INTO crcy_prc(date, time, crcy, prc,
                                           bid_prc, ask_prc)
                             VALUES (?, ?, ?, ?, ?, ?)
                  '''
            # return True
        elif query_type=="iu_status":
            sql = ''' INSERT OR REPLACE INTO
                      status(crcy, curr_slot_num, next_slot_bid_id, total_krw,
                             total_bid_amnt,  avr_prc, total_earning_ask)
                      VALUES (?, ?, ?, ?, ?, ?, ?) '''
        elif query_type=='s_status':
            sql = ''' SELECT * FROM  status
                        WHERE crcy = ?  '''
        elif query_type=='s_a_status':
            sql = 'SELECT * FROM  status'
        elif query_type=='i_slot':
            sql = ''' INSERT INTO slot(bid_order_id, crcy, c_date, c_time,
                                       num_of_bid, total_bid_amnt, bid_amnt, bid_prc, bid_krw,
                                       avr_prc, ask_yn, profit_rt, profit_krw,
                                       ask_amnt, ask_krw, next_bid_prc,
                                       next_bid_amnt, next_bid_order_id, ask_order_id, ask_prc)
                      VALUES( ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        elif query_type=='u_slot':
            sql = ''' UPDATE slot SET  c_date=?, c_time=?,
                                       num_of_bid=?, total_bid_amnt=?, bid_amnt=?, bid_prc=?, bid_krw=?,
                                       avr_prc=?, ask_yn=?, profit_rt=?, profit_krw=?,
                                       ask_amnt=?, ask_krw=?, next_bid_prc=?,
                                       next_bid_amnt=?, next_bid_order_id=?, ask_order_id=?, ask_prc=?
                                  WHERE bid_order_id=? and crcy=? '''
        elif query_type=='d_slot':
            sql = ''' DELETE FROM slot WHERE bid_order_id=? and crcy=? '''
        elif query_type=='s_slot':
            sql = "SELECT * FROM slot where crcy=? and ask_yn='N' "
        elif query_type=='s_slot_a':
            sql = "SELECT * FROM slot order by crcy, ask_yn"
        elif query_type=='s_slot_ac':
            sql = "SELECT * FROM slot where crcy=? order by crcy, ask_yn"
        elif query_type=='s_slot_yn':
            sql = "SELECT * FROM slot where ask_yn=? order by crcy"
        elif query_type=='s_slot_w':
            sql = "SELECT * FROM slot where num_of_bid=0 order by crcy"
        elif query_type=='i_order_hist':
            sql = ''' INSERT INTO order_hist('order_id', 'slot_id', 'crcy',
                                             'cont_date', 'cont_time', 'bidask',
                                             'total_amnt', 'result_amnt', 'krw',
                                             'fee', 'err_msg')
                          VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        elif query_type=='u_order_hist':
            sql = ''' UPDATE order_hist SET result_amnt=?, krw=?, fee=?
                                  WHERE order_id=? and slot_id=? and crcy=?'''
        elif query_type=='s_order_hist': # 결과물 bid/ask 구분 필요함
            sql = "SELECT * FROM order_hist where crcy=? and slot_id=?'' "
        elif query_type=='s_exec':
            sql = "SELECT * FROM execution"
        elif query_type=='u_exec':
            sql = "UPDATE execution SET run = ?"
        elif query_type=='s_prcs':
            sql = """ SELECT * from crcy_prc
                    where crcy=? and date*1000000+time
                                    = (select max(date*1000000+time)
                                        from crcy_prc where crcy=?)
                """
        else:
            # print("ERROR:BO0003 "+table_name)
            return False

        result = True
        is_select = query_type.lower().find('s_')>=0
        if sql is not None:
            conn = db.connect(self.dbname)
            with conn:
                cur = conn.cursor()
                #try:
                if values is not None and type(values) is tuple:
                    cur.execute(sql, values)
                else:
                    cur.execute(sql)
                if is_select:
                    result=cur.fetchall()
                else:
                    conn.commit()
                    cur.close()
                #except:
                #    print("set result False 111")
                #    result=False
                #    pass
            conn.close()
            sleep(0.01)
        else:
            result=False
        if result is False:
            print("query type :"+str(query_type)+",sql:"+str(sql)+", param:"+str(values))
            raise Exception('db error....')
        return result
