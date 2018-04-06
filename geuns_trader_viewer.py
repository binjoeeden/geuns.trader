from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, pyqtSignal
import sys, time, os
from common_util import *
from db_handler import *
from rest_api import *

main_ui = uic.loadUiType('Main.ui')[0]


class Main(QtWidgets.QMainWindow, main_ui):
    lblSTATUS_header = ['', '슬롯 수', '보유수량', '총매수KRW','평가금액',
                        '평단', '현재가격', '수익률', '평가손익(A)',
                        '수익 실현(B)', '총 이윤(A+B)']
    lblSLOTS_header  = ['', '생성일자','상태', '물타기', '보유수량',
                        '총매수KRW', '평가금액', '평가손익(A)',
                        '평단', '현재가격', '수익률', '다음매수가','익절 가격',
                        '수익 실현']

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

    def __init__(self, parent=None):
        super()
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.tblStatus.setColumnCount(len(Main.lblSTATUS_header))
        self.tblStatus.setHorizontalHeaderLabels(Main.lblSTATUS_header)
        self.tblStatus.resizeColumnsToContents()
        self.tblSlots.setColumnCount(len(Main.lblSLOTS_header))
        self.tblSlots.setHorizontalHeaderLabels(Main.lblSLOTS_header)
        self.tblSlots.resizeColumnsToContents()

        # self.trader = Main()
        # self.trader.daemon = True
        # self.setting = self.trader.setting
        # self.coin_config = self.trader.coin_config

        # self.trader.start()
        self.setBtnExecLabel()
        self.setting = getSettings()
        self.coin_config = getCoinConfig()
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
                      'QTUM':self.cboxQtum, 'ICON':self.cboxIcon}
        self.initAllCombos()

        # connect signals & slots
        self.btnInquiryStatus.clicked.connect(self.inquiryStatus)
        self.cmbAskYn.currentIndexChanged.connect(self.inquirySlots)
        self.btnExecTrading.clicked.connect(self.toggleExec)
        self.curr_prc = {}
        self.updateExecState()
        self.inquiryStatus()
        self.lblRefStatusEnd.hide()
        self.lblRefStatusIng.hide()


    def initAllCombos(self):
        for e in self.cboxs.values():
            if e!=self.cboxs['all']:
                e.setEnabled(False)
                e.toggled.connect(self.toggleCbox)
            else:
                e.toggled.connect(self.toggleCboxAll)

    def updateExecState(self):
        if self.get_exec_state() is True:
            self.btnExecTrading.setText(Main.lblBtnExec[1])
            self.lblExecStatus.setText('트레이딩 진행 중 ... ')
        else:
            self.btnExecTrading.setText(Main.lblBtnExec[0])
            self.lblExecStatus.setText('트레이딩 중단됨 ...')


    def get_exec_state(self):
        r = self.db.req_db('s_exec', None)
        if r[0][0].upper()=='Y':
            return True
        else:
            return False

    def setBtnExecLabel(self):
        pass

    def toggleExec(self):
        if self.get_exec_state() is True:
            self.db.req_db('u_exec', ('N',))
        else:
            self.db.req_db('u_exec', ('Y',))
        sleep(1)
        self.updateExecState()

    def setTableData(self, tbl, row, col, txt):
        tbl.setItem(row, col, QtWidgets.QTableWidgetItem(str(txt)))

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

    def inquirySlots(self):
        cmb = self.cmbAskYn.currentIndex()
        values = None
        if cmb == 0:
            qtype = 's_slot_a'
        elif cmb==3:
            qtype = 's_slot_w'
        else:
            qtype = 's_slot_yn'
            qtype = 's_slot_yn'
            if cmb==1:
                values = ('N', )
            else:
                values = ('Y', )

        r_db = self.db.req_db(qtype, values)
        print("slots !!!")
        print(r_db)
        if r_db is not False:
            self.tblSlots.clear()
            sleep(0.1)
            self.tblSlots.setRowCount(len(r_db))
            self.tblSlots.setHorizontalHeaderLabels(Main.lblSLOTS_header)
            crcy = ''
            idx_row = 0
            for e in r_db:
                row_data = []
                if crcy != e[1]:
                    crcy = e[1]
                    self.cboxs[crcy].setEnabled(True)
                    curr_prc = self.curr_prc[crcy]
                if self.need_cbox_init and self.cboxs[crcy].isChecked() is False:
                    self.cboxs[crcy].toggle()

                if self.cboxs[crcy].isChecked() is False:
                    continue
                row_data.append(e[1])
                ts_str = get_ts((e[2], e[3]))
                row_data.append(ts_str)
                total_bid_amnt = e[5]
                avr_prc = e[9]
                bid_krw = int(avr_prc * e[5])
                print(crcy+"] avr:"+str(avr_prc)+", amnt:"+str(e[5])+":"+str(bid_krw))
                if e[4]==0:
                    if cmb==1:
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
                row_data.append(format(profit, ","))     # 수익 실현
                self.setTableRowData(self.tblSlots, idx_row, row_data)
                idx_row +=1

        if self.need_cbox_init:
            self.need_cbox_init = False
        self.tblSlots.setRowCount(idx_row)
        self.tblSlots.resizeColumnsToContents()

    def inquiryStatus(self):
        #self.lblRefStatusEnd.hide()
        #self.lblRefStatusIng.show()

        r_db = self.db.req_db('s_a_status')
        total_coin_krw = 0
        print(r_db)
        self.tblStatus.clear()
        sleep(0.1)
        if r_db is not False:
            self.tblStatus.setRowCount(len(r_db))
            self.tblStatus.setHorizontalHeaderLabels(Main.lblSTATUS_header)

            idx_row = 0

            for e in r_db:
                crcy = e[0]
                r = call_api(GET_PRC, crcy)
                print(r)
                self.curr_prc[crcy] = int(r['data']['closing_price'])
                curr_prc = self.curr_prc[crcy]
                row_data = []
                row_data.append(e[0])        # 코인 (crcy)
                row_data.append(e[1])        # 총 슬롯 수(num of slots)
                row_data.append(format(round(e[4], 4), ','))        # 전체 수량 (bid amnt)
                row_data.append(format(int(e[4]*e[5]), ','))      # 총 투자금(total krw)
                row_data.append(format(int(round(e[4]*curr_prc, 0)), ','))
                row_data.append(format(int(round(e[5], 0)), ','))   # 평단 (average price)
                row_data.append(format(curr_prc, ','))    # 현재 가격
                total_coin_krw += e[4]*curr_prc
                if e[5]>0:
                    profit_rw = round((curr_prc/e[5]-1)*100, 2)
                    row_data.append(str(profit_rw)+' %') # 수익률
                    profit_krw = int(round((curr_prc/e[5]-1)*e[3], 0))
                    row_data.append(format(profit_krw, ','))  # 손익금
                    row_data.append(format(e[6], ','))        # 수익 실현금
                    row_data.append(e[6]+profit_krw)
                else:
                    row_data.append(0)
                    row_data.append(0)
                    row_data.append(0)
                    row_data.append(0)
                self.setTableRowData(self.tblStatus, idx_row, row_data)
                idx_row +=1
            total_coin_krw = int(round(total_coin_krw, 0))
        self.tblStatus.resizeColumnsToContents()
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
        #self.lblRefStatusEnd.show()
        #self.lblRefStatusIng.hide()

app = QtWidgets.QApplication(sys.argv)

if __name__ == "__main__":
    myWindow = Main(None)
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    myWindow.show()
    app.exec_()