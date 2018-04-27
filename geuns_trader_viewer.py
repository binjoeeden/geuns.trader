from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtCore import *
import sys, time, os
from common_util import *
from db_handler import *
from rest_api import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import datetime as dt

settings =  getSettings()
ui_file = settings['system']['view']
main_ui = uic.loadUiType(ui_file)[0]

is_new_ui = False
if ui_file=='Main_v2.ui' or ui_file=='Main_v3.ui':
    is_new_ui = True

class Main(QtWidgets.QMainWindow, main_ui):
    idxSTATUS_CRCY          = 0
    idxSTATUS_NumSlot       = 1
    idxSTATUS_TotalKrw      = 2
    idxSTATUS_AvrPrc        = 3
    idxSTATUS_Amnt          = 4
    idxSTATUS_CurrPrc       = 5
    idxSTATUS_ProfitRt      = 6
    idxSTATUS_ProfitKrw     = 7
    idxSTATUS_EarningAsk    = 8
    lblBtnExec = ['트레이딩 시작', '트레이딩 중지']
    global settings
    global is_new_ui, ui_file
    def __init__(self, parent=None):
        super()
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.setting = settings
        self.coin_config = getCoinConfig()
        self.status={}
        self.lblSLOTS_header  = ['', '생성일자','상태', '물타기', '수량',
                            '매수금액', '평가금액', '평가손익',
                            '평균단가', '현재가격', '수익률', '다음매수가','익절 가격',
                            '매도수익']


        if self.setting['system']['manual_ask_yn']==1:
            self.m_ask_yn = True
            self.lblOption.setText('코인\n수익')
            # self.lblSLOTS_header.append("코인수익")
            self.btnManualAsk.setEnabled(True)
            self.txtManualAsk.setEnabled(True)
            self.lblSTATUS_header = ['', '슬롯', '보유수량', '총매수금액',
                                     '평가금액', '평균단가', '현재가격', '수익률',
                                     '평가손익', '매도수익', '실현수익', '총 이윤',
                                     '코인수익']
        else:
            self.m_ask_yn = False
            self.btnManualAsk.setEnabled(False)
            self.txtManualAsk.setEnabled(False)
            self.lblOption.setText('자본\n잠식')
            self.lblSTATUS_header = ['', '슬롯', '보유수량', '총매수금액',
                                     '평가금액', '평균단가', '현재가격', '수익률',
                                     '평가손익', '매도수익', #, '자본잠식',
                                     '실현수익', '총 이윤']

        self.tblStatus.setColumnCount(len(self.lblSTATUS_header))
        self.tblStatus.setHorizontalHeaderLabels(self.lblSTATUS_header)
        self.tblStatus.resizeColumnsToContents()
        self.tblSlots.setColumnCount(len(self.lblSLOTS_header))
        self.tblSlots.setHorizontalHeaderLabels(self.lblSLOTS_header)
        self.tblSlots.resizeColumnsToContents()
        self.cmbSellCrcy.clear()


        self.need_cbox_init = True
        title = self.setting['system']['window_title']
        self.setWindowTitle(title)
        icon_img = self.setting['system']['title_icon']
        self.setWindowIcon(QtGui.QIcon(icon_img))

        self.system = self.setting['system']
        self.db_name = self.system['db_file_name']
        self.crcy_list = self.coin_config['crcy_list']
        self.db = DB_Handler(self.db_name)
        self.cboxs = {'all':self.cboxAll, 'BTC':self.cboxBtc,
                      'ETH':self.cboxEth, 'XRP':self.cboxXrp,
                      'BCH':self.cboxBch, 'LTC':self.cboxLtc,
                      'EOS':self.cboxEos, 'XMR':self.cboxXmr,
                      'DASH':self.cboxDash, 'ETC':self.cboxEtc,
                      'QTUM':self.cboxQtum, 'ICX':self.cboxIcx,
                      'TRX':self.cboxTrx,  'VEN':self.cboxVen,
                      'ELF':self.cboxElf,  'MITH':self.cboxMith,
                      'BTG':self.cboxBtg,  'MCO':self.cboxMco,
                      'ZEC':self.cboxZec,  'OMG':self.cboxOmg,
                      'KNC':self.cboxKnc}
        self.initAllCombos()

        # connect signals & slots
        self.btnInquiryStatus.clicked.connect(self.inquiryStatus)
        self.cmbAskYn.currentIndexChanged.connect(self.inquirySlots)
        self.cmbSellCrcy.currentIndexChanged.connect(self.inquiryMoreInfo)
        self.btnExecTrading.clicked.connect(self.toggleExec)
        self.btnManualAsk.clicked.connect(self.updateManualAsk)
        self.btnReset.setVisible(False)
        self.btnReset.clicked.connect(self.resetAll)

        self.tblStatus.itemSelectionChanged.connect(self.selCoin)
        self.fgr = None
        self.cvs = None
        self.lblG1.hide()
        self.lblG2.hide()
        self.lblG3.hide()
        self.lblG4.hide()

        self.curr_prc = {}
        self.updateExecState()
        self.inquiryStatus()


    def initAllCombos(self):
        for e in self.cboxs.values():
            if e!=self.cboxs['all']:
                e.setEnabled(False)
                e.toggled.connect(self.toggleCbox)
            else:
                e.toggled.connect(self.toggleCboxAll)

    def updateExecState(self):
        if self.get_exec_state() is True:
            self.btnExecTrading.setText(self.lblBtnExec[1])
            self.lblExecStatus.setText('트레이딩 진행 중 ... ')
            self.btnReset.setVisible(False)
        else:
            self.btnExecTrading.setText(self.lblBtnExec[0])
            self.lblExecStatus.setText('트레이딩 중단됨 ...')
            self.btnReset.setVisible(True)


    def get_exec_state(self):
        r = self.db.req_db('s_exec', None)
        if r[0][0].upper()=='Y':
            return True
        else:
            return False

    def toggleExec(self):
        if self.get_exec_state() is True:
            self.db.req_db('u_exec', ('N',))
        else:
            self.db.req_db('u_exec', ('Y',))
        sleep(1)
        self.updateExecState()

    def setTableData(self, tbl, row, col, cell_value):
        item = QtWidgets.QTableWidgetItem(str(cell_value))
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

        # if type(cell_value) is str:
        #     item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        # else:
        #     item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        tbl.setItem(row, col, item)


    def setTableRowData(self, tbl, row, row_data):
        for idx_column in range(len(row_data)):
            self.setTableData(tbl, row, idx_column, row_data[idx_column])

    def toggleCbox(self, isChecked):
        self.inquirySlots()
    def toggleCboxAll(self, isChecked):
        print("toggled: "+str(isChecked))
        for e in self.cboxs.values():
            if e.isEnabled():
                if isChecked and e.isChecked() is False:
                    e.toggle()
                elif isChecked is False and e.isChecked():
                    e.toggle()

    def selCoin(self):
        coin = self.tblStatus.selectedItems()
        try:
            crcy = coin[0].text()
        except:
            return
        if self.cvs is not None:
            self.gLayout.removeWidget(self.cvs)
        self.fgr = plt.Figure()
        self.cvs = FigureCanvas(self.fgr)
        self.gLayout.addWidget(self.cvs)
        ax = self.fgr.add_subplot(111)

        r_db = self.db.req_db('s_prcs_g', (crcy,crcy))
        r_db_2 = self.db.req_db('s_prc_gb', (crcy, crcy))
        r_db_o = self.db.req_db('s_order_h', (crcy, ))
        if r_db is False or r_db_2 is False:
            return

        self.lblG1.show()
        self.lblG2.show()
        self.lblG3.show()
        self.lblG4.show()

        y = [z[1] for z in r_db]
        # ts = [z[0] for z in r_db]
        ts = [(dt.datetime.strptime(str(z[0]), '%Y%m%d%H%M%S').timestamp())/1000 for z in r_db]
        c_ts = ts[0]
        num_p = len(y)
        #x = list(range(c_ts, c_ts+num_p))

        print(str(r_db_2))
        min_prc = r_db_2[0][0]
        max_prc = r_db_2[0][1]
        c_ts = r_db_2[0][2]

        print('y')
        print(str(y))
        print('num_p : '+str(num_p))
        print('x')
        print(str(ts))
        print('num_x:'+str(len(ts)))
        print("min : "+str(min_prc)+", max:"+str(max_prc))
        c_date = int(c_ts/1000000)
        c_time = c_ts%1000000
        self.lblGcrcy.setText(crcy)
        self.lblCtime.setText(get_ts((c_date,c_time)))
        self.lblMinPrice.setText(format(min_prc, ','))
        self.lblMaxPrice.setText(format(max_prc, ','))

        ax.plot(ts,y,'k--')

        color = ('b', 'g', 'r', 'c', 'm', 'y')
        if r_db_o is not False:
            i_c = 0
            for order in r_db_o:
                i_c = (i_c+1)%6
                b_ts = dt.datetime.strptime(str(order[0]), '%Y%m%d%H%M%S').timestamp()/1000
                a_ts = dt.datetime.strptime(str(order[2]), '%Y%m%d%H%M%S').timestamp()/1000
                b_prc = order[1]
                a_prc = order[3]
                ax.plot(b_ts, b_prc, color[i_c]+'s')
                ax.plot(a_ts, a_prc, color[i_c]+'^')

        # 자주 사용하는 마커 패턴으로는 '--', 's', '^', '+' 등이 있습니다.
        # 색상과 마커 패턴을 조합한 'r--'는 빨간색 대시라인을 의미하고,
        # 'bs'는 파란색 사각형, 'g^'는 녹색 삼각형, 'g+'는 녹색 플러스 모양을 의미합니다.
        # 문자	색상
        # b	blue(파란색)
        # g	green(녹색)
        # r	red(빨간색)
        # c	cyan(청록색)
        # m	magenta(마젠타색)
        # y	yellow(노란색)
        # k	black(검은색)
        # w	white(흰색)

        ax.set_xlabel('time')
        # ax.set_ylabel(crcy)
        ax.xaxis.set_ticklabels([])

        ax.grid()
        self.cvs.draw()



        # for col in selectedRow:
        #     pass #print(str(col.text()))


    def updateManualAsk(self):
        m_ask_krw=0
        amnt = 0
        try:
            m_ask_krw = int(get_num_from_str(self.txtManualAsk.text()))
            txt_amnt = self.lblEarnAmnt.text()
            amnt = get_num_from_str(txt_amnt)
        except:
            pass

        crcy = self.cmbSellCrcy.currentText()
        print("m_ask_krw : "+str(m_ask_krw)+", amnt : "+str(amnt)+", crcy : "+crcy)

        if m_ask_krw==0 or crcy not in self.coin_config['crcy_list'] or amnt==0:
            return

        # r = self.db.req_db('s_exec', None)

        self.db.req_db('iu_m_ask', (crcy, m_ask_krw, amnt, m_ask_krw))

        sleep(10)
        self.inquiryStatus()

    def inquiryMoreInfo(self):
        crcy = self.cmbSellCrcy.currentText()
        if crcy not in self.coin_config['crcy_list']:
            return
        cfg = self.coin_config[crcy]

        self.lblFirstSlotKrw.setText(format(int(cfg['first_slot_krw']), ','))
        self.lblSlotKrw.setText(format(int(cfg['slot_krw']), ','))
        if ui_file=='Main_v2.ui':
            self.lblMinPrc.setText(format(int(cfg['min_prc']), ','))
        if ui_file=='Main_v3.ui':
            self.lblAdjSlotKrw.setText(format(int(cfg['add_slot_krw']), ','))
            v = round(cfg['adj_new_slot_gap']*100, 1)
            if v==int(v):
                v = int(v)
            self.lblAdjNewSlotGap.setText(str(v)+' %')
            v = round(cfg['max_new_slot_gap']*100, 1)
            if v==int(v):
                v = int(v)
            self.lblMaxNewSlotGap.setText(str(v)+' %')


        v = round(cfg['add_bid_rate']*100, 1)
        if v == int(v):
            v = int(v)
        self.lblAddBidRt.setText(str(v)+' %')
        v = round(cfg['adj_add_bid_rt']*100, 1)
        if v == int(v):
            v = int(v)
        if v>=0:
            self.lblPm1.setText("++")
        else:
            self.lblPm1.setText("--")
        self.lblAdjAddBidRt.setText(str(abs(v))+' %')

        v = round(cfg['good_ask_rt']*100, 1)
        if v == int(v):
            v = int(v)
        self.lblGoodAskRt.setText(str(v)+' %')
        v = round(cfg['adj_good_ask_rt']*100, 1)
        if v == int(v):
            v = int(v)
        if v>=0:
            self.lblPm2.setText("++")
        else:
            self.lblPm2.setText("--")
        self.lblAdjGoodAskRt.setText(str(abs(v))+' %')
        v = round(cfg['new_slot_gap']*100, 1)
        if v == int(v):
            v = int(v)
        self.lblNewSlotGap.setText(str(v)+' %')

        self.lblEarnAmnt.setText('-')
        self.lblEarnPrc.setText('-')
        self.txtManualAsk.setText('0')

        try:
            if self.setting['system']['manual_ask_yn']==1:
                coin_amnt = self.status[crcy][EARN_COIN_AMNT_M_ASK]
                coin_krw = self.status[crcy][EARN_COIN_AVR_KRW_M_ASK]
                curr_krw =  self.status[crcy][EARN_COIN_CURR_KRW_M_ASK]
            else:
                coin_amnt = self.status[crcy][EARN_COIN_AMNT]
                coin_krw = self.status[crcy][EARN_COIN_AVR_KRW]
                curr_krw =  self.status[crcy][EARN_COIN_CURR_KRW]
            if coin_amnt>0:
                avr_prc = round(coin_krw / coin_amnt, 0)
            else:
                avr_prc=0
            if coin_amnt>0 and coin_krw>0 and curr_krw>0:
                self.lblEarnAmnt.setText(format(coin_amnt, ','))
                self.lblEarnPrc.setText(format(int(avr_prc), ','))
                self.txtManualAsk.setText(format(coin_krw, ','))
            if coin_amnt==0:
                self.lblEarnAmnt.setText('-')
            if coin_krw==0:
                self.lblEarnPrc.setText('-')
        except:
            pass




    def inquirySlots(self):
        cmb = self.cmbAskYn.currentIndex()
        values = None
        if cmb == 0:
            qtype = 's_slot_a'  # 전체 (all)
        elif cmb==3:
            qtype = 's_slot_w'  # 구매 대기 (waiting)
        elif cmb==5:
            qtype = 's_slot_nw' # 보유 +익절 : 구매 대기만 제외 (not waiting)
        else:
            qtype = 's_slot_yn'
            if cmb==1 or cmb==4:    # 보유 중 + 구매 대기
                values = ('N', )
            else:
                values = ('Y', )    # 익절 슬롯


        r_db = self.db.req_db(qtype, values)
        sell_crcy_list = []
        print("slots !!!")
        print(r_db)
        if r_db is not False:
            self.tblSlots.clear()
            self.tblSlots.setSortingEnabled(False)
            sleep(0.1)
            self.tblSlots.setRowCount(len(r_db))
            self.tblSlots.setHorizontalHeaderLabels(self.lblSLOTS_header)
            crcy = ''
            idx_row = 0
            for e in r_db:
                row_data = []
                if crcy != e[1]:
                    crcy = e[1]
                    self.cboxs[crcy].setEnabled(True)
                    if crcy not in sell_crcy_list:
                        sell_crcy_list.append(crcy)

                    try:
                        curr_prc = self.curr_prc[crcy]
                    except:
                        curr_prc = 0
                if self.need_cbox_init and self.cboxs[crcy].isChecked() is False:
                    self.cboxs[crcy].toggle()

                if self.cboxs[crcy].isChecked() is False:
                    continue
                row_data.append(e[1])
                ts_str = get_ts_slot((e[2], e[3]))
                if ts_str.find('0/0/0')>=0:
                    ts_str = '-'

                # if self.m_ask_yn is True:
                #     c_date_str = ts_str.split(' ')[0]
                #     row_data.append(c_date_str)
                # else:
                row_data.append(ts_str)

                total_bid_amnt = e[5]
                avr_prc = e[9]
                bid_krw = int(avr_prc * e[5])
                # print(crcy+"] avr:"+str(avr_prc)+", amnt:"+str(e[5])+":"+str(bid_krw))
                if e[4]==0:             # num_of_bid == 0
                    if cmb==1:          # 보유 중 only
                        continue
                    ask_yn='구매대기'
                    krw = 0
                    p_rt = 0
                    profit_rt = 0
                    profit = 0
                    total_bid_amnt = e[6]                 # total_bid_amnt = bid_amnt
                    avr_prc = e[7]                 # avr_prc  = bid_prc
                    bid_krw = e[6]*e[7]            # bid krw = bid_prc*pid_amnt
                    p_rt = 0
                elif e[10]=='Y':
                    ask_yn='익절'
                    krw = 0
                    if e[14]<e[8]:
                        profit = e[14]          # ask krw
                    else:
                        profit = e[14]-e[8]     # ask krw - bid krw
                    p_rt = round(profit / bid_krw *100, 2)
                    profit_rt = str(p_rt)+' %'
                else:
                    ask_yn='보유중'
                    krw = round(e[5]*curr_prc, 0)
                    p_rt = round((curr_prc-e[9])/e[9]*100, 2)
                    profit_rt = str(p_rt)+' %'
                    profit = e[12]

                row_data.append(ask_yn)
                if ask_yn!='구매대기':
                    n_p_bid = e[4]-1
                else:
                    n_p_bid = e[4]
                if ask_yn=='구매대기':
                    row_data.append('')     # 물타기
                else:
                    row_data.append(n_p_bid)     # 물타기
                row_data.append(format(round(total_bid_amnt,4), ","))       # 보유수량
                row_data.append(format(int(bid_krw), ","))       # 총매수KRW
                row_data.append(format(int(krw), ","))        # 평가금액
                if ask_yn=='보유중':
                    row_data.append(format(int(round(krw-bid_krw, 0)), ","))   # 평가 손익
                else:
                    row_data.append('0')   # 평가 손익
                row_data.append(format(int(round(avr_prc,0)), ","))       # 평단
                row_data.append(format(curr_prc, ","))   # 현재가격
                row_data.append(profit_rt)       # 수익률
                row_data.append(format(e[15],","))      # 다음매수가
                row_data.append(format(e[19],","))      # 익절가
                row_data.append(format(int(profit), ","))    # 수익 실현
                self.setTableRowData(self.tblSlots, idx_row, row_data)
                idx_row +=1


        self.tblSlots.setSortingEnabled(True)

        if self.need_cbox_init:
            self.need_cbox_init = False

        print("sell crcy list!!! -> "+str(sell_crcy_list))
        self.cmbSellCrcy.clear()
        for sell_crcy in sell_crcy_list:
            self.cmbSellCrcy.addItem(sell_crcy)
        if len(sell_crcy_list)>0:
            self.cmbSellCrcy.setEnabled(True)
        else:
            self.cmbSellCrcy.setEnabled(False)

        self.tblSlots.setRowCount(idx_row)
        self.tblSlots.resizeColumnsToContents()
        self.tblSlots.resizeRowsToContents()

    def inquiryStatus(self):
        r_db = self.db.req_db('s_a_status')
        total_coin_krw = 0
        print(r_db)
        self.tblStatus.clear()
        self.tblStatus.setSortingEnabled(False)

        sleep(0.1)
        total_minus = 0
        total_benefit = 0
        total_benefit_krw = 0
        total_coin_ask = 0
        total_coin_profit_krw = 0
        total_slots = 0
        total_sell_profit = 0
        if r_db is not False:
            self.tblStatus.setRowCount(len(r_db))
            self.tblStatus.setHorizontalHeaderLabels(self.lblSTATUS_header)
            idx_row = 0
            for e in r_db:
                minus = 0
                crcy = e[0]
                print("config : "+str(self.coin_config[crcy]))

                r = call_api(GET_PRC, crcy)
                print(r)
                self.curr_prc[crcy] = int(r['data']['closing_price'])
                curr_prc = self.curr_prc[crcy]
                row_data = []
                row_data.append(e[0])        # 코인 (crcy)
                row_data.append(e[1])        # 총 슬롯 수(num of slots)
                total_slots += e[1]
                row_data.append(format(round(e[4], 4), ','))        # 전체 수량 (bid amnt)
                current_bid_krw = int(e[4]*e[5])
                bid_krw = self.coin_config[crcy]['first_slot_krw'] \
                          + self.coin_config[crcy]['slot_krw']*(e[1]-1)
                if e[1]>2:
                    for i in range(2, e[1]):
                        bid_krw += int(self.coin_config[crcy]['add_slot_krw'])*(i-1)
                # print(crcy+", bid*98.5%:"+str(bid_krw*0.9985)+", total_krw : "+str(current_bid_krw))
                # print("base bid (98.5%) :"+str(bid_krw)+"("+str(bid_krw*0.985)+"), curr bid krw(98.5%) : "+str(current_bid_krw))
                if bid_krw*0.9985>current_bid_krw and self.m_ask_yn is False:
                    minus = current_bid_krw-bid_krw
                    # print("minus : "+str(minus))
                    total_minus += minus
                row_data.append(format(current_bid_krw, ','))      # 총 투자금(total krw)
                row_data.append(format(int(round(e[4]*curr_prc, 0)), ','))
                row_data.append(format(int(round(e[5], 0)), ','))   # 평단 (average price)
                row_data.append(format(curr_prc, ','))    # 현재 가격
                total_coin_krw += e[4]*curr_prc
                if e[5]>0:
                    profit_rw = round((curr_prc/e[5]-1)*100, 2)
                    row_data.append(str(profit_rw)+' %') # 수익률
                    profit_krw = int(round((curr_prc/e[5]-1)*e[3], 0))
                    row_data.append(format(profit_krw, ','))  # 평가 손익금
                    total_coin_profit_krw +=profit_krw
                    sell_profit = int(e[6])
                    row_data.append(format(sell_profit, ','))        # 매도 수익
                    total_sell_profit += sell_profit
                    # if self.m_ask_yn is False:
                    #    row_data.append(format(int(round(minus, 0)), ','))       # 자본 잠식
                    benefit_krw = round(e[6]+minus, 0)
                    row_data.append(format(int(benefit_krw), ',')) # 실현 수익 = 매도 수익 - 자본 잠식
                    benefit = benefit_krw+profit_krw
                    row_data.append(format(int(benefit), ','))     # 총 이윤 = 실현 수익  + 평가 손익
                    total_benefit     += benefit
                    total_benefit_krw += benefit_krw
                else:
                    row_data.append(0)
                    row_data.append(0)
                    row_data.append(0)
                    row_data.append(0)
                    row_data.append(0)
                coin_ask_krw = int(round(e[8], 0))
                coin_ask_amnt = round(e[7], 4)
                coin_profit_krw = int(round(coin_ask_amnt*curr_prc, 0))
                total_coin_ask += coin_profit_krw

                row_data.append(format(coin_profit_krw, ','))    # 코인 수익 KRW

                self.status[crcy] = row_data
                self.setTableRowData(self.tblStatus, idx_row, row_data)
                self.status[crcy].append(coin_ask_amnt)
                self.status[crcy].append(coin_ask_krw)
                self.status[crcy].append(coin_profit_krw)

                idx_row +=1
            total_coin_krw = int(round(total_coin_krw, 0))

        # 실적 정보
        if self.m_ask_yn is True:
            total_benefit += int(round(total_coin_ask,0))

        self.lblBenefit.setText(format(int(total_benefit), ',')) # 평가 수익 = 총 이윤 - 자본잠식
        self.lblBenefitKrw.setText(format(int(total_benefit_krw), ',')) # 실현 수익 = 총 이윤 - 자본잠식
        if is_new_ui:
            self.lblCurBenefit.setText(format(total_coin_profit_krw, ',')) # 평가손익
            self.lblNumSlot.setText(str(total_slots))
            self.lblSellProfit.setText(format(total_sell_profit,','))

        if self.m_ask_yn is True:
            self.lblOptVal.setText(format(int(round(total_coin_ask,0)), ','))    # 코인 수익
        else:
            self.lblOptVal.setText(format(int(round(total_minus,0)), ','))       # 자본 잠식

        self.tblStatus.setSortingEnabled(True)
        self.tblStatus.resizeColumnsToContents()
        self.tblStatus.resizeRowsToContents()
        self.inquirySlots()

        r = call_api(GET_BAL, 'BTC')
        if r['status']=='0000':
            in_use_krw = r['data']['total_krw'] - r['data']['available_krw']
            self.lblTotalKrw.setText(format(total_coin_krw+r['data']['total_krw'], ','))
            self.lblCoinKrw.setText(format(total_coin_krw, ','))
            self.lblKrw.setText(format(r['data']['total_krw'], ','))
            self.lblInuseKrw.setText(format(in_use_krw, ','))
            self.lblAvailKrw.setText(format(r['data']['available_krw'],','))

        self.updateExecState()

    def resetAll(self):
        qm = QtWidgets.QMessageBox
        reply = qm.question(self, '전량매도 초기화',
                    '정말로 모든 거래를 취소하고 삭제할까요?', qm.Yes|qm.No)

        if reply == qm.No:
            return

        r_db = self.db.req_db('s_a_status')
        if r_db is not False:
            for e in r_db:
                print("cancel new slot bid : "+e[0])
                ccl_order(e[2], e[0], BID)
            self.db.req_db('d_status')
        r_db = self.db.req_db('s_slot_yn', ('N',))
        if r_db is not False:
            for e in r_db:
                crcy = e[1]
                next_bid_order_id = e[17]
                ask_order_id = e[18]
                if next_bid_order_id != '' and len(next_bid_order_id)>0:
                    ccl_order(next_bid_order_id, crcy, BID)
                if ask_order_id!='' and len(ask_order_id)>0:
                    ccl_order(ask_order_id, crcy, ASK)
                r = call_api(GET_BAL, crcy)
                if r['status']=='0000':
                    key_str = 'available_'+crcy.lower()
                    try:
                        amnt = ceil(float(r['data'][key_str]), 4)
                        if amnt>min_units[crcy]:
                            call_api(MKT_ASK, crcy, {'units':amnt})
                    except:
                        pass
            pass
        self.db.req_db('d_a_slot')
        self.btnReset.setVisible(False)
        self.initAllCombos()
        self.inquiryStatus()
        pass


app = QtWidgets.QApplication(sys.argv)

# if __name__ == "__main__":
myWindow = Main(None)
# app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
myWindow.show()
app.exec_()
