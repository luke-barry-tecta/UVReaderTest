import os
import shutil
import sys

import image_capture.image_capture_app

from tkinter import *

import tkinter.ttk as ttk




mainMenu =  Tk()

mainMenu.title('UV Reader Test Main Menu')

optionsFrame = Frame(mainMenu)
optionsFrame.pack()

quitFrame = Frame(mainMenu)
quitFrame.pack(side=BOTTOM)

displayButton = Button(optionsFrame, text="Display")#command to open touchscreen test
displayButton.pack (side=LEFT)

cameraButton = Button(optionsFrame, text="Camera")#command to open camera app
cameraButton.pack (side=LEFT)

quitButton = Button(quitFrame, text = "Quit") #quit command from image_capture_panel
quitButton.pack (side=BOTTOM)


mainMenu.mainloop()



