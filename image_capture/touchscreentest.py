import tkinter as tk
import tkinter.ttk as ttk
import cv2
from tkvideo import tkvideo
import os
import shutil
import sys

class DisplayTestFrame(tk.Frame):
    def __init__(self, pRoot, bIsRPi, **kwargs):
        super().__init__(pRoot, kwargs)
        
        self.pToplevel = DisplayTestPanel(self, bIsRPi)
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

class DisplayTestPanel(tk.Frame):
    def __init__(self, pRoot, bIsRPi, **kwargs):

        nFrameHeight = 600
        nFrameWidth = 1024
        kwargs["height"] = nFrameHeight
        kwargs["width"] = nFrameWidth        
        super().__init__(pRoot, kwargs)
        self.pRoot = pRoot

        window = tk.Frame(self)
        window.pack()
        buttontest = tk.Button(window, text='button test', height = "25", width = "20")
        buttontest.pack (side=tk.LEFT)
        screentest = tk.Button(window, text='screen test',  height = "25", width = "20")
        screentest.pack (side=tk.LEFT)

   
    
    def ScreenTestPage(self):
        print("Screen Test")
        window3 = Toplevel(window)
        window3.title('screen test')
        window.geometry('900x600')
        lblVideo = Label(window3)
        lblVideo.pack()
        string = ('Downloads/screen.mp4')
        player = tkvideo(string, lblVideo, loop=1, size=(500,500))

        player.play()

    

class ButtonTestFrame(tk.Frame):
    def __init__(self, pRoot, bIsRPi, **kwargs):
        super().__init__(pRoot, kwargs)
        
        self.pToplevel = ButtonTestPanel(self, bIsRPi)
        self.pToplevel.pack(fill=tk.BOTH, expand=1)
        self.pack(fill=tk.BOTH, expand=1)


class ButtonTestPanel(tk.Frame):
    def __init__(self, pRoot, bIsRPi, **kwargs):

        nFrameHeight = 600
        nFrameWidth = 1024
        kwargs["height"] = nFrameHeight
        kwargs["width"] = nFrameWidth        
        super().__init__(pRoot, kwargs)
        self.pRoot = pRoot

        window = tk.Frame(self)
        print("Button Test")
        window2 = tk.Toplevel(window)
        window2.title('button test')
        btn=  [[0 for x in range(20)] for x in range(60)]
        #create buttons in a row
        for x in range(60):
            for y in range(20):
                btn[x][y] = tk.Button(window2,command= lambda x = x, y = y :color_change(x,y))
                btn[x][y].grid(column=x, row=y)
        
        def color_change(x,y):
            btn[x][y].config(bg="red")

   