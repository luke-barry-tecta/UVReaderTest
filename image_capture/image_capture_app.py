# -*- coding: utf-8 -*-

import tkinter as tk
import tkinter.ttk as ttk

from is_rpi import isRPi, isRPiScreen
from image_capture_panel import ImageCapturePanel

import xml.etree.ElementTree as ET

import os
import shutil
import sys

defaultFont = "helvetica 12"    

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
pRoot.wm_title("IDEXX Image Capture "+strVersion)

pRoot.option_add("*font", defaultFont)

bFullscreenStart = isRPiScreen()
if bFullscreenStart:
    pRoot.attributes("-fullscreen", True)
    pRoot.bind("<F11>", lambda event: pRoot.attributes("-fullscreen",
                                        not pRoot.attributes("-fullscreen")))
    pRoot.bind("<Escape>", lambda event: pRoot.attributes("-fullscreen", False))

pProcessor = ImageCaptureFrame(pRoot, isRPi())
        
pRoot.after(25, pProcessor.heartbeatImpl)
pRoot.mainloop()
