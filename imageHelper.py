"""   
    from :: https://stackoverflow.com/questions/7050448/write-image-to-windows-clipboard-in-python-with-pil-and-win32clipboard
    
    update : 14/01/2567 20:00 น
"""

from io import BytesIO
import os
from pathlib import Path

# pip install pillow
from PIL import Image as PILImage

# pip install pywin32
import win32clipboard 

# pip install pytz
import datetime, pytz



def saveImageFileToClipboard(filepath):
    
    image = PILImage.open(filepath)

    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()
    
    
def saveImageDataToClipboard(image : PILImage):
    output = BytesIO()
    image.convert('RGB').save(output, 'BMP')
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()
    
    
    
def convertJpgToPng(InputJpgFileName,OutputPngFileName):
    imgJpg = PILImage.open(InputJpgFileName)
    imgJpg.save(OutputPngFileName)    
    
    return True


def deleteFile(fileName:str):
    if os.path.isfile(fileName):
        os.remove(fileName)
            
            

# https://stackoverflow.com/questions/74612487/how-do-i-delete-a-file-from-a-folder-in-python            
def deleteFiles(folder,fileName:str , fileExt: str = ""):
    files = os.listdir(folder)
    
    # delete all files    
    for file in files:
        # Delete All
        # os.remove(file) 
        
        # delete file based on their name or suffix
        if Path(file).name == fileName or Path(file).suffix == fileExt:
            os.remove(file)
            


### - -- D A T E   T I M E   T H A I ---------------------------

tz = pytz.timezone('Asia/Bangkok')

def getNowThaiDateTime():
    _now = datetime.datetime.now(tz)
    _year = _now.year + 543
    _date = _now.strftime('%d/%m')
    _time = _now.strftime('%H:%M:%S')
    
    return f"{_date}/{_year} {_time}"


def getNowTime():
    _now = datetime.datetime.now(tz)
    _time = _now.strftime('%H:%M:%S')
    
    return _time