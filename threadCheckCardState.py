
# เอกสาร pyscard
# https://pyscard.sourceforge.io/user-guide.html#pyscard-user-guide

"""
    ส่วนประกอบ โปรแกรมอ่านข้อมูลบัตรประชาชน Python + PyQT6
    วรเพชร  เรืองพรวิสุทธิ์
    14/01/2567
    # update : 14/01/2567 20:00 น
    # latest : 04/02/2567 11:00 น
"""    

import time
from smartcard.scard import *
from PyQt6 import QtCore
from PyQt6.QtCore import QThread

# ENUM
class CardState():
    ATRMATCH = ['ATRMATCH','ATR Match']
    CHANGED = ['CHANGED','อัพเดตสถานะ']
    UNKNOWN = ['UNKNOWN','ไม่รู้สถานะ']

    EMPTY = ['EMPTY','ช่องเสียบ-ว่าง']
    PRESENT = ['PRESENT','ช่องเสียบ-พบบัตร']

    EXCLUSIVE= ['EXCLUSIVE','บัตรถูกอ่านอยู่ [Exclusive]']    
    INUSE = ['INUSE','บัตรถูกอ่านอยู่ [Share]']

    MUTE = ['MUTE','อ่านแล้ว-บัตรเสีย']    
    IGNORE = ['IGNORE','อ่านแล้ว-ค้าง/เอ๋อ']
    UNAVAILABLE = ['UNAVAILABLE','อ่านแล้ว-ไม่พบบัตร']
    UNAWARE = ['UNAWARE','อ่านแล้ว-บัตรมีปัญหา']





class ThreadCheckCardState(QThread):
    
    # New Signal
    stateChange = QtCore.pyqtSignal(list)

    def __init__(self,selectedReaderIndex=0,timesleep=0.700):
        super().__init__()
        self.selectedIndex = selectedReaderIndex
        self.timesleep = timesleep
        self.cardState = CardState.UNKNOWN
        self.readerList = []
        self.hContext = -1
        #self.hCard = -1


    def run(self):
        # อ่าน PC ต่อเครื่องอ่านบัตรไว้กี่เครื่อง
        self.getReaders()

        if self.readerList != []:
            # init
            self.cardState = CardState.UNKNOWN
            loop = True
            
            while loop == True: 

                # Check CardState
                self.cardState = self.checkCardState()
                        
                # emit Signal (Event เกิดแล้ว)
                self.stateChange.emit(self.cardState)

                # Sleep
                time.sleep(self.timesleep)
                
                # ถ้าเจอบัตรประชาชน หยุดทำงาน
                if self.cardState == CardState.PRESENT:
                    loop = False
                    #self.disconnect()
                    self.releaseContext()
                    
                

    ### - ---------------------------------------------------------------
    
    # def connect(self):
    #     # Connect
    #     hresult, hcard, dwActiveProtocol = SCardConnect(
    #         self.hContext, self.readerList[self.selectedIndex], 
    #         SCARD_SHARE_SHARED, SCARD_PROTOCOL_T0)
        
    #     if hresult != SCARD_S_SUCCESS:
    #         raise error('Thread: Connect Device ... Fail !!: '+ SCardGetErrorMessage(hresult))
        
    #     self.hCard = hcard
    #     print('Thread: Device... Connected')


#    def disconnect(self):
        
        # # Disconnect
        # hresult = SCardDisconnect(self.hCard, SCARD_UNPOWER_CARD)
        # if hresult != SCARD_S_SUCCESS:
        #     raise error('Thread: Disconnect ... Fail !!: '+SCardGetErrorMessage(hresult))
        # print('Thread: Device... Disconnected')

        
        
    def releaseContext(self):        
        # Release
        hresult = SCardReleaseContext(self.hContext)
        if hresult != SCARD_S_SUCCESS:
            raise error('Thread: Unload Driver ... Fail !!: '+ SCardGetErrorMessage(hresult))
        
        print('Thread: Monitor... หยุดแล้ว')
        

    def getStateValue(self,state):
        reader, eventstate, atr = state
        _cardState = CardState.UNKNOWN    
        #print(f"Thread: ติดต่อเครื่องอ่าน {reader}  ATR: {smartcard.util.toHexString(atr, smartcard.util.HEX)}" )
                    
        if eventstate & SCARD_STATE_ATRMATCH:
            _cardState = CardState.ATR_MATCH
            
        elif eventstate & SCARD_STATE_UNAWARE:
            _cardState = CardState.UNAWARE
            
        elif eventstate & SCARD_STATE_IGNORE:
            _cardState = CardState.IGNORE
            
        elif eventstate & SCARD_STATE_UNAVAILABLE:
            _cardState = CardState.UNAVAILABLE                
            
        elif eventstate & SCARD_STATE_EMPTY:
            _cardState = CardState.EMPTY

        elif eventstate & SCARD_STATE_PRESENT:
            _cardState = CardState.PRESENT

        elif eventstate & SCARD_STATE_EXCLUSIVE:
            _cardState = CardState.EXCLUSIVE

        elif eventstate & SCARD_STATE_INUSE:
            _cardState = CardState.INUSE        

        elif eventstate & SCARD_STATE_MUTE:
            _cardState = CardState.MUTE

        elif eventstate & SCARD_STATE_CHANGED:
            _cardState = CardState.CHANGED

        elif eventstate & SCARD_STATE_UNKNOWN:
            _cardState = CardState.UNKNOWN
            
        return _cardState


    def getReaders(self):
        try:
            
            hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
            if hresult != SCARD_S_SUCCESS:
                raise error('Thread: Load Driver ... Fail !! : ' +SCardGetErrorMessage(hresult))
            else:
                print('Thread: โหลดไดร์ฟเวอร์...สำเร็จ')


            print('Thread: Monitor...เริ่มแล้ว')            
            hresult, _readersList = SCardListReaders(hcontext, [])
            self.readerList = _readersList

            if hresult != SCARD_S_SUCCESS:
                raise error('Thread: Device Not Found !! : ' + SCardGetErrorMessage(hresult))

            self.hContext = hcontext
            return hcontext

        except Exception as err:
            raise ValueError(f'Thread: Get Device Fail !! : {err}')        


    def checkCardState(self):
        
        try:
            readerstates = [(self.readerList[self.selectedIndex],SCARD_STATE_UNAWARE)]
            _hresult, newstates = SCardGetStatusChange(self.hContext, 0, readerstates)
            return self.getStateValue(newstates[0])

        except Exception as err:
            raise ValueError(f'Thread: @CheckCardState > Get Card State ... Fail !! : {err}')
    
