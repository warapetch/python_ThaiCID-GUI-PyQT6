"""
    โปรแกรมอ่านข้อมูลบัตรประชาชน Python + PyQT6
    วรเพชร  เรืองพรวิสุทธิ์
    12/01/2567
    # update : 14/01/2567 20:00 น
"""    

import sys
from pathlib import Path

from thaiCIDHelper import *
from DataThaiCID import *
from imageHelper import *
from threadCheckCardState import *

from PyQt6 import *
from PyQt6 import uic,QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui  import QPixmap



class MainWindow(QWidget):
    
    def __init__(self):
        
        super().__init__()
        self.appVersion = "20240114-20.00"
        self.appUpdate  = "14/01/2567 20.00น"
        self.setAppAbout()
        self.imgPerson = None
        self.imgPersonFileName = ""
        self.loadUI()
        self.setupUI()


    def loadUI(self):        

        ### ERROR ??
        # ('Wrong base class of toplevel widget', (<class '__main__.MainWindow'>, 'QMainWindow'))
        # เปลี่ยนในไฟล์ ui 'QMainWindow' เป็น 'QWidget'
        
        _window = uic.loadUi("main.ui", self)
        #_window.show()

            


    def setAppAbout(self):
        self.appInfo = f'''โปรแกรมอ่านบัตรประชาชน (คนไทย)
พัฒนาด้วยภาษา Python 
และส่วนของ GUI ใช้ PyQt6

เวอร์ชั่น: {self.appVersion}

ออกแบบและพัฒนา โดย 
วรเพชร  เรืองพรวิสุทธิ์
อัพเดต: {self.appUpdate}'''
        
        
    def setupUI(self):
    
        self.setWindowTitle("Python Qt6: โปรแกรมอ่านบัตรประชาชน")       

        # show รูปภาพเบื้องต้น
        self.imgPerson = QPixmap()
        self.setImageToLabel("images/member.png")
        
        # Initialize
        self.lbStatus.setText("...")
        self.btnReadData.setEnabled(False)
        

        # Set Signal (Event)
        self.btnReset.clicked.connect(self.btnResetClick)
        self.btnReadData.clicked.connect(self.btnReadDataClick)       
        self.btnClose.clicked.connect(self.btnCloseClick)
        self.btnSaveText.clicked.connect(self.btnSaveTextClick)
        self.btnSaveImage.clicked.connect(self.btnSaveImageClick)
        self.btnAbout.clicked.connect(self.btnAboutClick)


        # กำหนดค่า StyleSheet QSS/CSS
        self.lbVersion.setObjectName("labelstatus")
        self.lbStatus.setObjectName("labelstatus")
        self.btnReadData.setObjectName("buttonreaddata")
        self.btnReadData.setAutoFillBackground(True)
        self.btnSaveText.setAutoFillBackground(True)
        self.btnSaveImage.setAutoFillBackground(True)
        
        # self.btnReset.setObjectName("button")
        # self.btnClose.setObjectName("button")
        # self.btnAbout.setObjectName("button")
        # self.btnSaveText.setObjectName("button")
        # self.btnSaveImage.setObjectName("button")
        
        # self.btnReadData.setStyleSheet(
        #     "QPushButton{ background-color: rgb(144,238,144);}"
        #     "QPushButton:pressed{ border:none; border-width=0px; background-color: rgb(255,238,144);}"
        #     )
        self.lbVersion.setText(f"version:\n{self.appVersion}")
        self.lbVersion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.CIDReader = None
        
        # run Thread Check CardState        
        self.runThreadCheckCardState()
        



### - ---[ T H R E A D ]------------------------------------
### Check Card State

    def doOnThreadStop(self):
        self.threadCheckCard.quit()
        self.threadCheckCard.wait()
        del self.threadCheckCard
        print('Thread: Free Thread')
    
    
    def doOnCardStateChange(self,cardState):

        #print('Thread: ตรวจสอบสถานะบัตร: ',cardState[1])
        self.doShowTextNotify(f"ตรวจสอบสถานะบัตร: {cardState[1]}")
        
        foundCard = cardState == CardState.PRESENT
        self.btnReadData.setEnabled(foundCard)
        
        # auto อ่านบัตร
        if foundCard == True:
            self.btnReadDataClick()
            

    # def doOnGetReaders(self,hContext,reader):
    #     self.hContext = hContext
    #     self.readerObj = reader
    #     print(hContext)
        

    def runThreadCheckCardState(self):
        # เลือก CardReader 0 == ตัวที่ 1
        # mainThread = QThread(self)
        # work = Worker()
        self.threadCheckCard = ThreadCheckCardState(selectedReaderIndex = 0)
        self.threadCheckCard.stateChange.connect(self.doOnCardStateChange)
        self.threadCheckCard.finished.connect(self.doOnThreadStop)
        # Worker.MoveToThread()
        # mainThread.start()
        self.threadCheckCard.start()


### - ---[ U T I L I T Y ]------------------------------------

    def setImageToLabel(self,fileName):
        self.imgPersonFileName = fileName

        self.imgPerson = None
        self.imgPerson = QPixmap()
        self.imgPerson.load(fileName)
        
        self.lbImage.setPixmap(self.imgPerson)
        self.lbImage.setScaledContents(True)
        self.lbImage.update()


    def clearText(self):
        self.listData.setPlainText("")
        self.listData.update()
        
        
    def clearImage(self):
        self.setImageToLabel("images/member.png")        



### - ---[ C A L L  B A C K ]------------------------------------

    def doShowTextNotify(self,message):

        self.lbStatus.setText(f"{getNowTime():<9} > {message}")
        self.lbStatus.update()
        #self.horizontalLayout.update() #update Frame
        # เพิ่ม QApplication.processEvents() ใน Loop เพื่อให้ วินโดว์อัพเดตหน้าจอถี่ขึ้น        
        QApplication.processEvents()
        
        
    def doOnGetValue(self,key,response):
        # key = Data of DATA ข้อมูลจากไฟล์ DataThaiCID
        # response = ข้อมูลที่บัตรส่งมาให้ 
        # response[0] = text-คนอ่านออก
        # response[1] = text-hex
        print(f"{key['desc']} = {response[0]}")

    
    def doOnWriteFileText(self,fieldName,listOfData):
        # listOfData[0] = plaintext ,  ข้อความ ธรรมดา พร้อมใช้งาน (แสดงหน้าจอ)
        # listOfData[1] = JsonStringUser, key : (key=value) 
        # listOfData[2] = JsonStringDev,  key : value
        # listOfData[3] = [JsonObject]
        # listOfData[3][0] = key-Thai : value
        # listOfData[3][1] = key-Eng  : value
        print("doOnWriteFileText")
        data = str(listOfData[0]).encode('utf-8')        
        with open("textFilename.txt","wb") as file:
            file.write(data)
            file.close()


    def doOnReadTextFinish(self,listOfData):
        # listOfData[0] = plaintext ,  ข้อความ ธรรมดา พร้อมใช้งาน (แสดงหน้าจอ)
        # listOfData[1] = JsonStringUser, key : (key=value) 
        # listOfData[2] = JsonStringDev,  key : value
        # listOfData[3] = [JsonObject]
        # listOfData[3][0] = key-Thai : value
        # listOfData[3][1] = key-Eng  : value        
        self.listData.setPlainText(listOfData[0])
        self.listData.update()
        
        
    def doOnWriteFilePhoto(self,fieldName,photoData):        
        # fieldName
        # photoData
        print("doOnWriteFilePhoto")
        with open("photoFilename.png","wb") as file:
            file.write(photoData)
            file.close()


    def doOnReadPhotoFinish(self,fileName):
        self.setImageToLabel(fileName)


    def doOnReadAllFinish(self,elapsedTime):
        self.btnReadData.setEnabled(True)

    
    
    
### - ---[ C O D E ]------------------------------------    
    
    def btnResetClick(self):
        self.clearImage()
        self.clearText()
        self.doShowTextNotify("Reset Reader ...")

        if self.CIDReader != None:
            self.CIDReader.disconnect()
            
        # free Instance
        self.CIDReader = None
        
        # Run Thread Check Card State       
        self.runThreadCheckCardState()
        
        # refresh Form
        self.update()    
        
        
    def btnReadDataClick(self):

        self.btnReadData.setEnabled(False)
        self.clearImage()
        self.clearText()
        
        self.doShowTextNotify("Reader: เริ่มอ่านข้อมูลบัตร ...")
        
        self.CIDReader = None
        self.CIDReader = ThaiCIDHelper(APDU_SELECT,APDU_THAI_CARD,procStepNotify=self.doShowTextNotify)
        self.CIDResponse = self.CIDReader.connectReader(0,procStepNotify=self.doShowTextNotify)
        
        time.sleep(1)
        
        if self.CIDReader.Connected == True:
            # Read Data
            self.CIDReader.readData(
                procStepNotify=self.doShowTextNotify,
                #procGetValue= self.doOnGetValue,
                procGetPhoto= self.doShowTextNotify,               
                procReadTextFinish=self.doOnReadTextFinish,
                procReadPhotoFinish=self.doOnReadPhotoFinish,
                procReadAllFinish=self.doOnReadAllFinish,
                
                #onWriteFileText= self.doOnWriteFileText,
                #onWriteFilePhoto=self.doOnWriteFilePhoto,
                )
            
        else:
            print(f'Error: {self.CIDReader.LastError}')
        
        
    def btnCloseClick(self):
        # Close App        
        # คำสั่ง แบบที่ใช้ QCoreApplication.instance()
        QCoreApplication.instance().quit()
        
        # คำสั่งปกติ ใช้ QApplication.instance()
        #QApplication.instance().quit()

        
    def btnSaveTextClick(self):
        if self.CIDReader == None:
            return               
        elif self.CIDReader.CardData == []:
            return

        tmpFolder = self.CIDReader.pathTempFile
        fileName = f"{tmpFolder}/{self.CIDReader.CardData['CID']}.txt"
        fileFilters = "Text file (*.txt);;All files (*.*)"
        # getSaveFileName(parent,caption,default-filename,fileFilters,default-filter)
        fileName = QFileDialog.getSaveFileName(self, 'บันทึกข้อความลงไฟล์', fileName,fileFilters)

        # fileName = 0= full path filename (user กำหนด Path+FileName) ,1= ext (จาก Filter ที่เลือก)        
        if fileName[0] != "":
            textData = self.listData.toPlainText()
            with open(fileName, 'w') as file:
                file.write(textData)
                file.close()
        
        
    def btnSaveImageClick(self):        
        if self.CIDReader == None:
            return               
        elif self.CIDReader.CardData == []:
            return
        
        fileName = self.CIDReader.CardData['filename']
                
        buffer = QBuffer()
        img = QPixmap(fileName)              
        img.save(buffer, 'png')

        # Alway seek position 0 (begin of File/data)
        buffer.seek(0)
        data = buffer.data()
        fileFilters = "PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif);;All files (*.*)"
        # getSaveFileName(parent,caption,default-filename,fileFilters,default-filter)
        fileName = QFileDialog.getSaveFileName(self, 'บันทึกรูปลงไฟล์', fileName,fileFilters)
        
        # fileName = 0= full path filename (user กำหนด Path+FileName) ,1= ext (จาก Filter ที่เลือก)
        if fileName[0] != "":
            with open(fileName[0], 'wb') as file:
                file.write(bytes(data))
                file.close()
            
        img = None


    def btnAboutClick(self):
        QMessageBox.information(self,"เกี่ยวกับ",self.appInfo) 


def main():
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication([])

    # โหลด QSS( CSS )
    with open("main.css",'r') as File:
        appStyle = File.read()
        app.setStyleSheet(appStyle)
        File.close()            
    
        
    # สร้าง Instance
    window = MainWindow()
    # ปรับ Button on Windows-Caption
    window.setWindowFlags(  QtCore.Qt.WindowType.CustomizeWindowHint 
                          | QtCore.Qt.WindowType.WindowCloseButtonHint 
                          #| QtCore.Qt.WindowType.WindowMinimizeButtonHint
                          #| QtCore.Qt.WindowType.WindowMaximizeButtonHint
                          )

    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
    
    



    
"""
## Py to EXE
pyinstaller --clean --noconsole --onefile --icon reader.ico  main.py

# PyQt6
# https://www.riverbankcomputing.com/static/Docs/PyQt6/
# https://www.pythonguis.com/pyqt6-tutorial/

"""