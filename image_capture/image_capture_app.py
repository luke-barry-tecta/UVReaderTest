# -*- coding: utf-8 -*-

import tkinter as tk
import tkinter.ttk as ttk

from is_rpi import isRPi, isRPiScreen
from image_capture_panel import ImageCapturePanel
from touchscreentest import DisplayTestFrame

import xml.etree.ElementTree as ET

import os
import shutil
import sys

defaultFont = "helvetica 12"  

#root level menu for camera or display test
class menuFrame(tk.Frame):
    def __init__(self, pRoot, bIsRPi, **kwargs):
        super().__init__(pRoot, kwargs)
                   
        self.pToplevel = menuPanel(self, bIsRPi)
        self.pToplevel.pack(fill=tk.BOTH, expand=1)
        self.pack(fill=tk.BOTH, expand=1)
        

    def heartbeatImpl(self):
            # update application state            
        self.pToplevel.update()
    
        self.master.update()
        self.master.update_idletasks()
        self.master.after(25, self.heartbeatImpl)

#root level panel, has size at opening, buttons and def
class menuPanel(tk.Frame):
    def __init__(self, pRoot, bIsRPi, **kwargs):
        # frame
        nFrameHeight = 600
        nFrameWidth = 1024
        kwargs["height"] = nFrameHeight
        kwargs["width"] = nFrameWidth        
        super().__init__(pRoot, kwargs)
        self.pRoot = pRoot

        optionsFrame = tk.Frame(self)
        optionsFrame.pack()

        quitFrame = tk.Frame(self)
        quitFrame.pack(side=tk.BOTTOM)

        displayButton = tk.Button(optionsFrame, text="Display", height = "25", width = "20", command=self.openDisplayTest)#command to open touchscreen test
        displayButton.pack (side=tk.LEFT)

        cameraButton = tk.Button(optionsFrame, text="Camera", height = "25", width = "20", command=self.openImageCapture)#command to open camera app
        cameraButton.pack (side=tk.LEFT)

        quitButton = tk.Button(quitFrame, text = "Quit", command=self.quit) #quit command from image_capture_panel
        quitButton.pack (side=tk.BOTTOM)

    def quit(self):
        self.master.quit()

    #opens image capture
    def openImageCapture(self):
        print("opening Image Capture App")
        ImageCapture = tk.Toplevel()
        ImageCapture.option_add("*font", defaultFont)
        bFullscreenStart = isRPiScreen()
        if bFullscreenStart:
            ImageCapture.attributes("-fullscreen", True)
            ImageCapture.bind("<F11>", lambda event: ImageCapture.attributes("-fullscreen",
                                                not ImageCapture.attributes("-fullscreen")))
            ImageCapture.bind("<Escape>", lambda event: ImageCapture.attributes("-fullscreen", False))
        pProcessor = ImageCaptureFrame(ImageCapture, isRPi())
        ImageCapture.after(25, pProcessor.heartbeatImpl)

    #opens display test
    def openDisplayTest(self):
        print("opening Display Test App")
        DisplayTest = tk.Toplevel()
        DisplayTest.option_add("*font", defaultFont)
        bFullscreenStart = isRPiScreen()
        if bFullscreenStart:
            DisplayTest.attributes("-fullscreen", True)
            DisplayTest.bind("<F11>", lambda event: DisplayTest.attributes("-fullscreen",
                                                not DisplayTest.attributes("-fullscreen")))
            DisplayTest.bind("<Escape>", lambda event: DisplayTest.attributes("-fullscreen", False))
        pProcessor = DisplayTestFrame(DisplayTest, isRPi())
        DisplayTest.after(25, pProcessor.heartbeatImpl)


class ImageCaptureFrame(tk.Frame):
    def __init__(self, pRoot, bIsRPi, **kwargs):
        super().__init__(pRoot, kwargs)
        
        self.pToplevel = ImageCapturePanel(self, bIsRPi)
        self.pToplevel.pack(fill=tk.BOTH, expand=1)
        self.pack(fill=tk.BOTH, expand=1)
        
    def heartbeatImpl(self):
        # update application state            
        self.pToplevel.update()
 
        self.master.update()
        self.master.update_idletasks()
        self.master.after(25, self.heartbeatImpl)

    def quit(self):
        self.master.quit()


pRoot = tk.Tk()
strVersion = "0.1.0"
pRoot.wm_title("IDEXX Reader Test " + strVersion)

pRoot.option_add("*font", defaultFont)

bFullscreenStart = isRPiScreen()
if bFullscreenStart:
    pRoot.attributes("-fullscreen", True)
    pRoot.bind("<F11>", lambda event: pRoot.attributes("-fullscreen",
                                        not pRoot.attributes("-fullscreen")))
    pRoot.bind("<Escape>", lambda event: pRoot.attributes("-fullscreen", False))

pProcessor = menuFrame(pRoot, isRPi())
        
pRoot.after(25, pProcessor.heartbeatImpl)
pRoot.mainloop()
