
import atexit
from datetime import datetime
import os
import sys

import tkinter as tk
from tkinter import filedialog
import tkinter.ttk as ttk

from PIL import Image
try:
    from PIL import ImageTk
except ImportError as e:
    print("Trying to install ImageTk")
    if not os.system("sudo apt-get install python3-pil.imagetk"):
        print("SUCCESS")
        from PIL import ImageTk
    else:
        print("FAILED. Please install manually")
        sys.exit(-1)

import numpy as np

sys.path.append("../processor") # append processor directory to search path
from quanti_tray import QuantiTray
from constants import *
from write_images import writeTagged

def validateReadOnly(): 
    return False

def validateNumeric(action, index, value_if_allowed,
                   prior_value, text, validation_type, trigger_type, widget_name):
    if value_if_allowed:
        if not len(value_if_allowed):
            return True # permit empty string
        try:
            float(value_if_allowed)
            return True
        except ValueError:
            return False
    else:
        return True # permit empty string

def getCountString(nCount):
    strReturn = ""
    if nCount < 10:
        strReturn = "   "+str(nCount)
    elif nCount < 100:
        strReturn = "  "+str(nCount)
    elif nCount < 1000:
        strReturn = " "+str(nCount)
    else:
        strReturn = str(nCount)
    return strReturn

class ProgressRunner:
    
    def __init__(self, pProgressBar):
        self.pProgressBar = pProgressBar
        self.pProgressBar.start()
        
    def __del__(self):
        self.pProgressBar.stop()

def addSlider(pParent, strLabel, nLow, nHigh, fResolution):
    pPanel = tk.Frame(pParent)
    dvarVariable = tk.DoubleVar()
    dvarVariable.set(1.0)
    tk.Label(pPanel, text="\n"+strLabel).pack(side="left")
    tk.Scale(pPanel, from_=nLow, to=nHigh, length=150, variable=dvarVariable, orient=tk.HORIZONTAL, resolution=fResolution).pack(side="left")
    pPanel.pack(side="top")    
    return dvarVariable

class ImageCapturePanel(tk.Frame):
    
    def __init__(self, pRoot, bIsRPi, **kwargs):

        # frame
        nFrameHeight = 600
        nFrameWidth = 1024
        kwargs["height"] = nFrameHeight
        kwargs["width"] = nFrameWidth        
        super().__init__(pRoot, kwargs)
        self.pRoot = pRoot
        
        # working directory
        self.strDirectory = os.path.dirname(os.path.realpath(__file__))
        self.strImageDirectory = os.path.join(self.strDirectory, "images")
        if not os.path.exists(self.strImageDirectory):
            os.mkdir(self.strImageDirectory)

        # where images will be saved (generated on capture)
        self.strVisFilename = ""
        self.strUVFilename = ""

        # create room for processed images
        self.strOutputDir = os.path.join(self.strImageDirectory, "processed")
        self.strOutputDirTagged = os.path.join(self.strOutputDir, "tagged")
        os.makedirs(self.strOutputDirTagged, exist_ok=True)

        # read any saved parameters, or initialize them to default values
        self.mapParameters = {}
        self.strParameterFile = os.path.join(self.strDirectory, "parameters.txt")
        if os.path.exists(self.strParameterFile):
            with open(self.strParameterFile) as inFile:
                for strLine in inFile:
                    if strLine.strip().startswith("#"):
                        continue
                    lstLine = strLine.strip().split()
                    if len(lstLine):
                        self.mapParameters[lstLine[0]] = float(lstLine[1])
                        
        # ensure all parmeters exist (handles cases of missing and borken parameters file)
        if "UVAnalogGain" not in self.mapParameters: self.mapParameters["UVAnalogGain"] = 1.0
        if "UVRedGain" not in self.mapParameters: self.mapParameters["UVRedGain"] = 1.0
        if "UVBlueGain" not in self.mapParameters: self.mapParameters["UVBlueGain"] = 1.0
        if "UVExposureTime" not in self.mapParameters: self.mapParameters["UVExposureTime"] = 65.0
        if "VisAnalogGain" not in self.mapParameters: self.mapParameters["VisAnalogGain"] = 1.0
        if "VisRedGain" not in self.mapParameters: self.mapParameters["VisRedGain"] = 1.0
        if "VisBlueGain" not in self.mapParameters: self.mapParameters["VisBlueGain"] = 1.0
        if "VisExposureTime" not in self.mapParameters: self.mapParameters["VisExposureTime"] = 65.0

        if bIsRPi:
            # load real camera and light controllers
            from camera_controller import CameraController
            from light_controller import LightController            
            self.pCameraController = CameraController(self.strDirectory)
            self.pLightController = LightController()            
        else:
            from dummy_camera_controller import DummyCameraController
            from dummy_light_controller import DummyLightController            
            self.pCameraController = DummyCameraController(self.strDirectory)
            self.pLightController = DummyLightController()            

        # upper panel for images
        pTopPanel = tk.Frame(self)

        # images
        self.nImageWidth = nFrameWidth//2 # rescale to fit
        self.nImageHeight = (self.nImageWidth*480)//640 # rescale to fit
        self.pVisImage = Image.fromarray(np.zeros([self.nImageHeight, self.nImageWidth, 3], dtype=np.uint8))
        self.pVisPhotoImage = ImageTk.PhotoImage(self.pVisImage)
        self.pVisPanel = tk.Label(pTopPanel, image = self.pVisPhotoImage)
        self.pVisPanel.pack(side = "left", fill = "both", expand = "yes")

        self.pUVImage = Image.fromarray(np.zeros([self.nImageHeight, self.nImageWidth, 3], dtype=np.uint8))
        self.pUVPhotoImage = ImageTk.PhotoImage(self.pUVImage)
        self.pUVPanel = tk.Label(pTopPanel, image = self.pUVPhotoImage)
        self.pUVPanel.pack(side = "left", fill = "both", expand = "yes")

        pTopPanel.pack(side="top")

        # control panel
        pBottomPanel = tk.Frame(self)
        
        pGainPanel = tk.Frame(pBottomPanel) # analog and colour gain settings
        pPanel = tk.Frame(pGainPanel)
        self.dvarAnalogGain = addSlider(pGainPanel, "AG:", 0, 16, 0.2)
        self.dvarRedGain = addSlider(pGainPanel, "RG:", 0, 32, 0.2)
        self.dvarBlueGain = addSlider(pGainPanel, "BG:", 0, 32, 0.2)
        pGainPanel.pack(side="left", anchor="w", fill=tk.Y)

        pResetButtonPanel = tk.Frame(pBottomPanel) # gain reset button
        tk.Button(pResetButtonPanel, text="Reset\nGains", command=self.resetGains).pack(side="top", fill=tk.BOTH, anchor="n", expand="yes")
        self.pProgressbar = ttk.Progressbar(pResetButtonPanel, mode='indeterminate')
        self.pProgressbar.pack(side="top", fill=tk.BOTH, expand="yes") 
        tk.Button(pResetButtonPanel, text="QUIT", command=self.quit).pack(side="top", fill=tk.BOTH, expand="yes")        
        pResetButtonPanel.pack(side="left", anchor="w", fill=tk.Y)

        pExposurePanel = tk.Frame(pBottomPanel) # exposure time setting
        self.dvarExposureTime_ms = addSlider(pExposurePanel, "Exposure (ms):", 0, 500, 5)
        self.dvarExposureTime_ms.set(65)
        tk.Button(pExposurePanel, text="Reset Exposure", command=self.resetExposure).pack(side="top", fill=tk.BOTH, anchor="n", expand="yes")

        pVisPanel = tk.Frame(pExposurePanel)        
        tk.Button(pVisPanel, text="Save Vis", command=self.saveVisParams).pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        tk.Button(pVisPanel, text="Load Vis", command=self.loadVisParams).pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        pVisPanel.pack(side="top", fill=tk.BOTH, anchor="n", expand="yes")
        
        pUVPanel = tk.Frame(pExposurePanel)        
        tk.Button(pUVPanel, text="Save UV", command=self.saveUVParams).pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        tk.Button(pUVPanel, text="Load UV", command=self.loadUVParams).pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        pUVPanel.pack(side="top", fill=tk.BOTH, anchor="n", expand="yes")
        
        pExposurePanel.pack(side="left", anchor="w", fill=tk.Y)

        pImagePanel = tk.Frame(pBottomPanel) # Image filename
        self.svarFilename = tk.StringVar()
        self.svarFilestub = tk.StringVar()
        self.ivarQT2K = tk.IntVar()
        
        pPanel = tk.Frame(pImagePanel)
        tk.Entry(pPanel, textvariable=self.svarFilename).pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        tk.Label(pPanel, textvariable=self.svarFilestub).pack(side="left", fill=tk.BOTH, anchor="w")
        tk.Checkbutton(pPanel, text="QT2K", variable=self.ivarQT2K).pack(side="left", fill=tk.BOTH, anchor="w")
        self.svarFilestub.set("_vis/uv_DATE-TIME.tiff")
        self.ivarQT2K.set(1)
        pPanel.pack(side="top", fill=tk.BOTH, anchor="n", expand="yes")
        
        pVisPanel = tk.Frame(pImagePanel) # Vis control buttons
        self.pPreviewVisButton = tk.Button(pVisPanel, text="Preview VIS", command=self.previewVis)
        self.pPreviewVisButton.pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        self.pCaptureVisButton = tk.Button(pVisPanel, text="Capture VIS", command=self.captureVis)
        self.pCaptureVisButton.pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        self.pProcessVisButton = tk.Button(pVisPanel, text="Process VIS", command=self.processVis)
        self.pProcessVisButton.pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        pVisPanel.pack(side="top", fill=tk.BOTH, anchor="n", expand="yes")
        
        pUVPanel = tk.Frame(pImagePanel) # UV control buttons
        self.pPreviewUVButton = tk.Button(pUVPanel, text="Preview UV", command=self.previewUV)
        self.pPreviewUVButton.pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        self.pCaptureUVButton = tk.Button(pUVPanel, text="Capture UV", command=self.captureUV)
        self.pCaptureUVButton.pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        self.pProcessUVButton = tk.Button(pUVPanel, text="Process UV", command=self.processUV)
        self.pProcessUVButton.pack(side="left", fill=tk.BOTH, anchor="w", expand="yes")
        pUVPanel.pack(side="top", fill=tk.BOTH, anchor="n", expand="yes")
        
        pImagePanel.pack(side="left", anchor="w", fill=tk.BOTH, expand="yes")
        
        pBottomPanel.pack(side="top", fill="both", expand="yes")

        # ensure we write the new state at exit
        atexit.register(self.writeState)

    def processVis(self):
        
        pRunner = ProgressRunner(self.pProgressbar)
        bUV = False
        try:
            arrImage = self.processImage(bUV)
            self.pVisImage = Image.fromarray(arrImage)
            self.pVisPhotoImage = ImageTk.PhotoImage(self.pVisImage.resize((self.nImageWidth, self.nImageHeight), resample=Image.Resampling.LANCZOS))        
            self.pVisPanel["image"] = self.pVisPhotoImage
        except Exception as e:
            print("Could not process")
            print(e)

    def processUV(self):
        
        pRunner = ProgressRunner(self.pProgressbar)
        bUV = True
        try:
            arrImage = self.processImage(bUV)
            self.pUVImage = Image.fromarray(arrImage)
            self.pUVPhotoImage = ImageTk.PhotoImage(self.pUVImage.resize((self.nImageWidth, self.nImageHeight), resample=Image.Resampling.LANCZOS))        
            self.pUVPanel["image"] = self.pUVPhotoImage
        except Exception as e:
            print("Could not process")
            print(e)

    def pStep(self):
        print('STep')
        self.pProgressbar.step(10)
        self.pRoot.update()
        
    def processImage(self, bUV):
        
        bHasSmallWells = self.ivarQT2K.get()
        bDebug = False # must always be false as directories are not set up for it on RPi
        if bUV:
            pTray = QuantiTray(self.strUVFilename, bUV, bHasSmallWells, bDebug, self.pStep)
        else:
            pTray = QuantiTray(self.strVisFilename, bUV, bHasSmallWells, bDebug, self.pStep)
        pTray.process() # core processing
        pTray.classifyWells() # make the calls

        # write the tagged image
        nBigWellHalfSize_pix = int(fBigWellSize_mm*pTray.fScale/2)
        nSmallWellHalfSize_pix = int(fSmallWellSize_mm*pTray.fScale/2)
        return writeTagged(pTray.arrImage, pTray.strImageFile, pTray.lstBigWells, pTray.lstSmallWells, 
            pTray.pOverflow, pTray.nOverflowLine, pTray.nOverflowStartCol, pTray.nOverflowEndCol, 
            nBigWellHalfSize_pix, nSmallWellHalfSize_pix)        
        
    def captureVis(self):
        
        self.pProgressbar.start()
        
        bPreview = False
        bUV = False

        self.pLightController.WhitelightsOn()
        mapMetadata, arrImage = self.captureImage(bPreview, bUV)
        self.pLightController.WhitelightsOff()
        
        self.writeMetadata(mapMetadata, "vis")
        
        self.pVisImage = Image.fromarray(arrImage)        
        self.strVisFilename = self.getFilename("vis")
        self.pVisImage.save(self.strVisFilename)
        
        self.pVisPhotoImage = ImageTk.PhotoImage(self.pVisImage.resize((self.nImageWidth, self.nImageHeight), resample=Image.Resampling.LANCZOS))        
        self.pVisPanel["image"] = self.pVisPhotoImage

        self.pProgressbar.stop()
        
    def captureUV(self):

        self.pProgressbar.start()

        bPreview = False
        bUV = True
        self.pLightController.UVlightsOn()
        mapMetadata, arrImage = self.captureImage(bPreview, bUV)
        self.pLightController.UVlightsOff()

        self.writeMetadata(mapMetadata, "uv")        
        
        self.pUVImage = Image.fromarray(arrImage)
        self.strUVFilename = self.getFilename("uv")
        self.pUVImage.save(self.strUVFilename)
        
        self.pUVPhotoImage = ImageTk.PhotoImage(self.pUVImage.resize((self.nImageWidth, self.nImageHeight), resample=Image.Resampling.LANCZOS))        
        self.pUVPanel["image"] = self.pUVPhotoImage
        
        self.pProgressbar.stop()

    def getFilename(self, strType):
        strBasename = self.svarFilename.get().lower().replace(" ", "_")
        self.svarFilename.set(strBasename)
        return os.path.join(self.strImageDirectory, strBasename+"_"+strType+"_"+datetime.now().strftime("%Y-%m-%d_%H.%M.%S")+".tiff")
 
    def previewVis(self):

        self.pProgressbar.start()
        
        bPreview = True
        bUV = False

        self.pLightController.lightsOn()
        mapMetadata, arrImage = self.captureImage(bPreview, bUV)
        self.pLightController.lightsOff()
        
        self.pVisImage = Image.fromarray(arrImage)
        self.pVisImage.save("preview_vis.tiff")
        
        self.pVisPhotoImage = ImageTk.PhotoImage(self.pVisImage.resize((self.nImageWidth, self.nImageHeight), resample=Image.Resampling.LANCZOS))        
        self.pVisPanel["image"] = self.pVisPhotoImage

        self.pProgressbar.stop()
        
    def previewUV(self):

        self.pProgressbar.start()

        bPreview = True
        bUV = True
        
        self.pLightController.UVlightsOn()
        mapMetadata, arrImage = self.captureImage(bPreview, bUV)
        self.pLightController.UVlightsOff()

        self.pUVImage = Image.fromarray(arrImage)
        self.pUVImage.save("preview_uv.tiff")
        self.pUVPhotoImage = ImageTk.PhotoImage(self.pUVImage.resize((self.nImageWidth, self.nImageHeight), resample=Image.Resampling.LANCZOS))
        self.pUVPanel["image"] = self.pUVPhotoImage

        self.pProgressbar.stop()

    def captureImage(self, bPreview, bUV):
        
        fAnalogGain = self.dvarAnalogGain.get()
        fRedGain = self.dvarRedGain.get()
        fBlueGain = self.dvarBlueGain.get()
        nExposureTime_us = int(1000*self.dvarExposureTime_ms.get())
        
        return self.pCameraController.captureImage(fAnalogGain, fRedGain, fBlueGain, nExposureTime_us, bPreview, bUV)

    #create and write to a file that stores metadata
    def writeMetadata(self, mapMetadata, strType):
        strFilename = self.getFilename(strType).replace(".tiff", "_metadata.txt")
        with open(strFilename, "w") as outFile:
            lstKeys = list(mapMetadata.keys())
            lstKeys.sort()
            for strKey in lstKeys:
                outFile.write(strKey+": "+str(mapMetadata[strKey])+"\n")
        
    def resetGains(self):
        print("Reset gains")
        self.dvarAnalogGain.set(1.0)
        self.dvarRedGain.set(1.0)
        self.dvarBlueGain.set(1.0)

    def resetExposure(self):
        print("Reset exposure")
        self.dvarExposureTime_ms.set(65)

    def loadUVParams(self):
        print("Loading UV")
        self.dvarAnalogGain.set(self.mapParameters["UVAnalogGain"])
        self.dvarRedGain.set(self.mapParameters["UVRedGain"])
        self.dvarBlueGain.set(self.mapParameters["UVBlueGain"])
        self.dvarExposureTime_ms.set(self.mapParameters["UVExposureTime"])
        
    def saveUVParams(self):
        print("Saving UV")
        self.mapParameters["UVAnalogGain"] = self.dvarAnalogGain.get()
        self.mapParameters["UVRedGain"] = self.dvarRedGain.get()
        self.mapParameters["UVBlueGain"] = self.dvarBlueGain.get()
        self.mapParameters["UVExposureTime"] = self.dvarExposureTime_ms.get()
        
    def loadVisParams(self):
        print("Loading Vis")
        self.dvarAnalogGain.set(self.mapParameters["VisAnalogGain"])
        self.dvarRedGain.set(self.mapParameters["VisRedGain"])
        self.dvarBlueGain.set(self.mapParameters["VisBlueGain"])
        self.dvarExposureTime_ms.set(self.mapParameters["VisExposureTime"])
        
    def saveVisParams(self):
        print("Saving Vis")
        self.mapParameters["VisAnalogGain"] = self.dvarAnalogGain.get()
        self.mapParameters["VisRedGain"] = self.dvarRedGain.get()
        self.mapParameters["VisBlueGain"] = self.dvarBlueGain.get()
        self.mapParameters["VisExposureTime"] = self.dvarExposureTime_ms.get()

    def writeState(self):
        with open(self.strParameterFile, "w") as outFile:
            for strKey in self.mapParameters:
                outFile.write(strKey+" "+str(self.mapParameters[strKey])+"\n")

    def update(self):
        if len(self.svarFilename.get()) and self.pCaptureVisButton["state"] != tk.NORMAL:
            self.pCaptureVisButton["state"] = tk.NORMAL
            self.pCaptureUVButton["state"] = tk.NORMAL
        elif 0 == len(self.svarFilename.get()) and self.pCaptureVisButton["state"] != tk.DISABLED:
            self.pCaptureVisButton["state"] = tk.DISABLED
            self.pCaptureUVButton["state"] = tk.DISABLED

        bFileExists = len(self.strVisFilename) and os.path.exists(self.strVisFilename)
        if  bFileExists and self.pProcessVisButton["state"] != tk.NORMAL:
            self.pProcessVisButton["state"] = tk.NORMAL
        if not bFileExists and self.pProcessVisButton["state"] != tk.DISABLED:
            self.pProcessVisButton["state"] = tk.DISABLED
        
        bFileExists = len(self.strUVFilename) and os.path.exists(self.strUVFilename)
        if  bFileExists and self.pProcessUVButton["state"] != tk.NORMAL:
            self.pProcessUVButton["state"] = tk.NORMAL
        if not bFileExists and self.pProcessUVButton["state"] != tk.DISABLED:
            self.pProcessUVButton["state"] = tk.DISABLED           

    def quit(self):
        self.master.quit()
