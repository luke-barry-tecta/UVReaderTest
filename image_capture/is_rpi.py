import os

def isRPi():
    bReturn = False
    try:
        with open('/sys/firmware/devicetree/base/model', 'r') as inFile:
            if 'raspberry pi' in inFile.read().lower():
                bReturn = True
    except Exception: 
        pass

    return bReturn

def isRPiScreen():
    bReturn = False
    try:
        if isRPi() and not os.environ['DISPLAY'].startswith("localhost"): # if we're logged in remotely
            bReturn = True
    except Exception: 
        pass

    return bReturn
