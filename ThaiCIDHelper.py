"""
    Class ThaiCIDHelper for PyQT6 (And Other...)  
    ไฟล์ประกอบของการอ่านข้อมูลบัตรประชาชน
    วรเพชร  เรืองพรวิสุทธิ์
    09/01/2567
    Python 3.11.5 - 3.11.7
    pyscard==2.0.7
    
    update : 14/01/2567 20:00 น
    
    https://pyscard.sourceforge.io/epydoc/smartcard-module.html
    https://pyscard.sourceforge.io/epydoc/smartcard.CardConnectionDecorator.CardConnectionDecorator-class.html    
"""

import time, codecs , subprocess
# pyscard 2.0.7
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.scard import *

from DataThaiCID  import *
from imageHelper  import *

####- --------------------------------------------------
# Thai CID Smartcard Helper @GUI
####- --------------------------------------------------
class ThaiCIDHelper():
    
    def __init__(self,
                apduSELECT = [0x00, 0xA4, 0x04, 0x00, 0x08],
                apduTHCard = [0xA0, 0x00, 0x00, 0x00, 0x54, 0x48, 0x00, 0x01], 
                ShowThaiDate= True,
                pathTempFile = "tmp",
                procStepNotify = None
                ):
        
        # Super().__init__()
        # Initialize
        self.LastError = ""
        self.CardReaderCount = 0          
        self.CardReaderConn = None
        self.CardData = []
        self.apduSELECT  = apduSELECT
        self.apduTHCard = apduTHCard
        self.apduRequest = []
        self.ATR = ""
        self.ShowThaiDate = ShowThaiDate
        self.SelectedReaderIndex = -1
        self.pathTempFile = pathTempFile

        self.getAvailableReader(procStepNotify)
                
        
        
    def getAvailableReader(self,procStepNotify = None):
        self.LastError = ""
        self.CardReaderCount = 0
        try:
            self.CardReaderList = readers()  # PC/SC
            self.CardReaderCount = len(self.CardReaderList)
        except Exception as err:
            self.LastError = f'{err}'

        if procStepNotify:
            procStepNotify (f'Reader: Available Count = {self.CardReaderCount}')
        

        
            
    def reset(self,index,procStepNotify = None):
        
        self.getAvailableReader()
        self.connectReader(self,index,procStepNotify)

        
            
####- --------------------------------------------------    
#### connectReader
####- --------------------------------------------------    
    def connectReader(self,index,procStepNotify = None):
        """
            connectReader ติดต่อเครื่องอ่านบัตร \n
            พารามิเตอร์ : 
            index ลำดับของเครื่องอ่านบัตร \n
            Default 0 (ตัวที่ 1) ** ถ้ามี ** \n
            return >> Reader-connection , Connected Status
        """
        
        if procStepNotify:
            procStepNotify(f'Reader: Select ... [{index}] = [{self.CardReaderList[index]}]')
        
        _HWCardReader = self.CardReaderList[index]
        _connected = False
        self.Connected = False
        
        try: 
            # Create Connection
            self.CardReaderConn = _HWCardReader.createConnection()
            
            # Reader Connection [OK]
            self.CardReaderConn.connect()       

            self.SelectedReaderIndex = index
            self.Connected = True
            _connected = True
            
            if procStepNotify:
                procStepNotify(f'Reader: Connected ... [{self.CardReaderList[index]}]')
        
        except Exception as err:
            self.LastError = f'{err}'
            if procStepNotify:
                procStepNotify(f'Connection : Error = {err}')
            # 0x80100069 Unable to connect: The smart card has been removed,so that further communication is not possible
            # Unable to connect with protocol: T0 or T1. The smart card is not responding to a reset.
        
                        
        if _connected == True:
            ### read ATR (format for storage cards)
            # 3B 8N 80 01 {XX} {XX}
            # 3B 8N 80 01 80 4F 0C A0 00 00 03 06 {SS} {NN} 00 00 00 00 {XX}
            
            atr = self.CardReaderConn.getATR()
            self.ATR = toHexString(atr)
            if procStepNotify:
                procStepNotify (f"Reader: ATR = {self.ATR}")
            
            ### Check Version
            # Get-Data command format
            if (atr[0] == 0x3B & atr[1] == 0x67):
                self.apduRequest = [0x00, 0xc0, 0x00, 0x01]
            else:
                self.apduRequest = [0x00, 0xc0, 0x00, 0x00]        

            return  self.CardReaderConn

        return None
    

    def disconnect(self):
        self.CardReaderConn.disconnect()
    
    
####- --------------------------------------------------    
#### readData
####- --------------------------------------------------    

    def readData(self,readPhoto=True,
                saveText : SaveType = SaveType.FILE,
                savePhoto: SaveType = SaveType.FILE,
                
                procStepNotify = None,
                procGetValue = None,   # แสดงสถานะการอ่าน Text
                procGetPhoto = None,
                
                procReadTextFinish = None,
                procReadPhotoFinish = None,
                procReadAllFinish = None,

                onWriteFileText = None,
                onWriteFilePhoto = None,
                ): # แสดงสถานะการอ่าน Photo
        """
            readData อ่านข้อมูลจากบัตร ตาม apdu ที่กำหนด \n
            พารามิเตอร์ : \n
            readPhoto อ่านรูปภาพ ? \n
            saveText บันทึกข้อความ ? None-File-Clip \n
            savePhoto บันทึกข้อมูลภาพ ? None-File-Clip \n
            procStepNotify = (message) \n
            procGetValue (dataKey,[Value]) \n
            procGetPhoto (filename-PNG) \n
            procReadTextFinish = ([message]) \n
            procReadPhotoFinish = (fileName) \n
            procReadAllFinish = (elapsed) \n
            onWriteFileText = (filename, [data]) \n
            onWriteFilePhoto = (filename, data) \n
        """

        self.CardData = []
        start_time = time.time()

        # เริ่มอ่านข้อมูลบัตร 
        # SELECT + CARD TYPE
        data, sw1, sw2 = self.CardReaderConn.transmit(self.apduSELECT + self.apduTHCard)
        if procStepNotify:
            #_txt = "Reader: Send `SELECT` Response = %02X %02X" % (sw1, sw2)
            _txt = f"Reader: Send `SELECT` Response = {sw1},{sw2}"
            procStepNotify(_txt)


        # set CardReader State
        #self.dataOpened = True

        responseJson = []
        _jsonThaiDesc , _Json4Dev ,  _JsonRawData = {},{},{}
        _plaintextThaiDesc ,_textThaiDesc , _textJson = "","",""

        ##- -----------------------------------------------------
        ### Read Value
        if procStepNotify:
            procStepNotify("Reader: อ่านข้อมูล เริ่มแล้ว...")
        apduCount = len(APDU_DATA) 
        for index,data in enumerate(APDU_DATA):
            
            _apdu = searchDATAValue('key',data['key'],'apdu')
            if procStepNotify:
                procStepNotify(f"Reader: อ่าน {data['desc']}")
            
            response = self.getValue(_apdu,data['type'])
        ##- ----------------------------------------------------
        
            # make Json
            _jsonThaiDesc[data['desc']] = response[0]
            _Json4Dev[data['id']] = response[0]
            #_JsonRawData['raw'] = response[1]
            
            if procGetValue:
                procGetValue(data,response)
            
            # make Text
            if index == (apduCount-1): 
                _plaintextThaiDesc += f'{data["desc"]}: {response[0]}\n'
                _textThaiDesc += f'"{index}":"{data["desc"]}={response[0]}"\n'
                _textJson += f'"{data["id"]}":"{response[0]}"\n'
            else:
                _plaintextThaiDesc += f'{data["desc"]}: {response[0]}\n'
                _textThaiDesc += f'"{index}":"{data["desc"]}={response[0]}",\n'
                _textJson += f'"{data["id"]}":"{response[0]}",\n'
                
        
        ### make Json List
        responseJson.append(_jsonThaiDesc)
        responseJson.append(_Json4Dev)
        # responseJson.append(_JsonRawData)
        
        # ให้ค่า CardData ด้วย JsonObject
        self.CardData = responseJson[1] 
        
        ### Copy Text To Clipboard
        if saveText == SaveType.CLIPBOARD:
            if procStepNotify:
                procStepNotify("Reader: บันทึกข้อมูลข้อความ [ไปคลิปบอร์ด] ...")
            copyTextToClipboard(f'{_textThaiDesc}\n{_textJson}')
    
    
        if saveText == SaveType.FILE:
            if procStepNotify:
                procStepNotify("Reader: บันทึกข้อมูลข้อความ [ลงไฟล์] ...")
                
            ### Save Text To File
            filename = f"{self.pathTempFile}/{self.CardData['CID']}.json"
                
            if onWriteFileText:
                # filename, [data]
                onWriteFileText(filename,[_plaintextThaiDesc,_textThaiDesc,_textJson,responseJson])
            else:     
                with open(filename, "wb" ) as file:
                    file.write ('[{\n'.encode('utf-8'))
                    file.write (_textThaiDesc.encode('utf-8'))
                    file.write ('},\n'.encode('utf-8'))

                    file.write ('{\n'.encode('utf-8'))
                    file.write (_textJson.encode('utf-8'))
                    file.write ('}]'.encode('utf-8'))
                    
                    file.close()


        # After read text Finish
        # Text-Desc , Text-Json , JsonObject
        if procReadTextFinish:
            procReadTextFinish([_plaintextThaiDesc,_textThaiDesc,_textJson,responseJson])


        ##- -----------------------------------------------------
        ### Read Photo
        if readPhoto:
            if procStepNotify:
                procStepNotify("Reader: อ่าน  รูปภาพ...")
                
            photoStr = []
            for index,data in enumerate(APDU_PHOTO):
                _apdu = searchAPDUPhoto(data['key'])
                photoStr += self.getPhoto(_apdu)
                
                if procGetPhoto:
                    procGetPhoto(f"Reader: อ่านรูปภาพ {index+1}/{len(APDU_PHOTO)}")
            
            
            filename = f"{self.pathTempFile}/{self.CardData['CID']}.jpg"
            pngfilename = f"{self.pathTempFile}/{self.CardData['CID']}.png"
            imageData = bytes(photoStr)
            
            ### Save Photo to File
            if savePhoto == SaveType.FILE:
                # use bytes แปลง [] เป็น Bytes ** ถ้าเป็น String จะ Error
                if procStepNotify:
                    procStepNotify("Reader: บันทึกข้อมูลรูป [ลงไฟล์] ...")
                    
                # ให้ค่า CardData['filename'] ด้วยการเขียนเอง
                self.CardData['filename'] = 'CUSTOM_WRITE'
                if onWriteFilePhoto:
                    onWriteFilePhoto(filename,imageData)
                else:
                    with codecs.open(filename, "wb" ) as file:
                        file.write (imageData)                        
                        file.close()
                        
                    # Conver JPG to PNG
                    convertJpgToPng(filename,pngfilename)
                    deleteFile(filename)
                
                    # ให้ค่า CardData['filename'] ด้วย pngfilename เป็นไฟล์รูปถ่าย ชนิด *.PNG
                    self.CardData['filename'] = pngfilename
                

                    ## Copy Photo to Clipboard
                    if savePhoto == SaveType.CLIPBOARD:
                        if procStepNotify:
                            procStepNotify("Reader: บันทึกข้อมูลรูป [ไปคลิปบอร์ด] ...")
                        saveImageFileToClipboard(filename)
                
                
        ##- -----------------------------------------------------
        
        # After read Photo Finish
        # filename ext '.PNG'
        if procReadPhotoFinish:
            procReadPhotoFinish(pngfilename)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        elapsed_str  = time.strftime("%S.{}".format(str(elapsed_time % 1)[2:])[:6], time.gmtime(elapsed_time))

        if procStepNotify:
            procStepNotify(f"Reader: อ่านข้อมูล เสร็จแล้ว... [{elapsed_str} ms]")
        
        
        if procReadAllFinish:
            procReadAllFinish(elapsed_str)
        

####- --------------------------------------------------    
#### getValue
####- --------------------------------------------------   

    def getValue(self,apdu,dataType):
        """
            getValue อ่านข้อมูลจากบัตร ตาม APDU ที่กำหนด \n
            พารามิเตอร์ : \n
            apdu คำสั่ง APDU ของฟิลด์ที่ต้องการอ่าน \n
            dataType ประเภทของข้อมูล เพื่อจัดรูปแบบตามต้องการ
        """
        
        #print(f"Reader: Send Command")
        _data, _sw1, sw2 = self.CardReaderConn.transmit(apdu)
        #print(f"Reader: Card Response1 >> Size= {sw2} ")
        #ขอข้อมูล ขนาดที่บอกมา Size == sw2
        rawdata, _sw1 , _sw2 = self.CardReaderConn.transmit(self.apduRequest + [sw2])
        #print(f"Reader: Card Response2 >> data")
        
        text = self.encodeTextThai(rawdata)

        if dataType == ThaiCIDDataType.ADDRESS:
            # ข้อมูลที่อยู่
            text = text.replace('#######',' ')
            text = text.replace('######',' ')
            text = text.replace('#####',' ')
            text = text.replace('####',' ')
            text = text.replace('###',' ')
            text = text.replace('##',' ')
            text = text.replace('#',' ')
            data = text
            
        elif dataType == ThaiCIDDataType.NAME:
            # ข้อมูลชื่อ-นามสกุล ไทย และ อังกฤษ
            text = text.replace('##',' ')
            text = text.replace('#','')
            data = text
            
        elif dataType == ThaiCIDDataType.DATE:
            # ปีพ.ศ. + เดือน + ปี  ระวังข้อมูลที่มีแต่ พ.ศ.
            # ระวังข้อมูลเป็นช่องว่าง หรือ มีเฉพาะ ปี พ.ศ.
            if self.ShowThaiDate == True:
                # dd/mm/2567
                _date = textToThaiDate(text)
            else:    
                # 2024-mm-dd
                _date = textToEngDate(text)
            data = _date
            
        elif dataType == ThaiCIDDataType.GENDER:
            # '-' , 'ชาย' ,'หญิง'
            data = GENDER[int(text)]

        elif dataType == ThaiCIDDataType.RELIGION:
            # '-' , 'พุทธ' ,'อิสลาม'
            data = RELIGION[int(text)]
            
        elif dataType == ThaiCIDDataType.DOCNUMBER:
            # เลขใต้รูปภาพ
            data = setformatDocNumber(text)

        else:
            data = text
        
        return [data, rawdata]


    def getPhoto(self,apdu):
        """
            getPhoto อ่านข้อมูลรูปภาพจากบัตร ตาม APDU ที่กำหนด \n
            พารามิเตอร์ : \n
            apdu คำสั่ง APDU ของฟิลด์ที่ต้องการอ่าน \n
        """
                
        _ , _ , sw2 = self.CardReaderConn.transmit(apdu)        
        #ขอข้อมูล ขนาดที่บอกมา Size == sw2        
        rawdata, _ , _ = self.CardReaderConn.transmit(self.apduRequest + [sw2])

        return rawdata


    def encodeTextThai(self,data):

        # แปลงเป็นตัวอักษรไทย TIS-620
        result = bytes(data).decode('tis-620')

        # ตัดช่องว่าง trim
        return result.strip()


    def clearAllFiles(self):
        _filename = f"{self.SelectedReaderIndex}"
        # Delete Image file
        deleteFiles(self.pathTempFile,fileName=_filename)
        # Delete Text file
        deleteFiles(self.pathTempFile,fileName=_filename)        



## External Method ##
### - -------------------------------------------------------------
def textToThaiDate(txt:str):
    # ปีพ.ศ. + เดือน + ปี 
    # บัตร คนมีปัญหา มีแต่ปีเกิด
    # บัตร ตลอดชีพ มีแต่ปีเกิด
    if len(txt) == 8:
        _year   = txt[:4]   # 1-4
        _month  = txt[4:6]  # 5-6
        _day    = txt[6:8]  # 7-8
        # แปลงเป็น วัน/เดือน/ปี
        return f"{_day}/{_month}/{_year}"
    else:
        return txt


def textToEngDate(txt:str):
    # ปีพ.ศ. + เดือน + ปี 
    if len(txt) == 8:
        _year   = txt[:4]   # 1-4
        _month  = txt[4:6]  # 5-6
        _day    = txt[6:8]  # 7-8
        _yearEN = int(_year) - 543
        # แปลงเป็น ปี - เดือน - วัน
        return f"{_yearEN}-{_month}-{_day}"
    else:
        return txt
        
    
def setformatDocNumber(txt:str):
    # 0000-00-00000000    
    t1 = txt[:4]   # 1-4
    t2 = txt[4:6]  # 5-6
    t3 = txt[6:]   # 6+
    
    return f"{t1}-{t2}-{t3}"
    
    
def searchDATAValue(type,value,response):
    
    for data in APDU_DATA:
        if data[type] == value:
            return data[response]

    return None



def searchAPDUPhoto(value):
    
    for data in APDU_PHOTO:
        if data['key'] == value:
            return data['apdu']

    return None


def copyTextToClipboard(txt):

    return subprocess.run("clip", input=txt, check=True, encoding="tis-620")





""" ` packages
user python 3.11.5 - 3.11.7
pip install pyscard
pip install pillow
pip install pywin32
pip install pytz
"""