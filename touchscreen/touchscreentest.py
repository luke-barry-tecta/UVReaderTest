# hello_world.py

from tkinter import *
import cv2
from tkvideo import tkvideo

window = Tk()
window.title("Screen Test")

window.geometry('900x600')

window.tk.call('tk', 'scaling', 3.0)

buttontest = Button(window, text='button test', height = 15, width = 25, command = lambda:ButtonTestPage())
buttontest.grid(row = 0, column = 0)
screentest = Button(window, text='screen test', height = 15, width = 25, command = lambda:ScreenTestPage())
screentest.grid(row = 0, column = 1)

def ButtonTestPage():
    print("Button Test")
    window2 = Toplevel(window)
    window2.title('button test')
    window.geometry('900x600')
    btn=  [[0 for x in range(20)] for x in range(60)]
    #create buttons in a row
    for x in range(60):
         for y in range(20):
            btn[x][y] = Button(window2,command= lambda x = x, y = y :color_change(x,y))
            btn[x][y].grid(column=x, row=y)
    
    def color_change(x,y):
     btn[x][y].config(bg="red")
     
def ScreenTestPage():
    print("Screen Test")
    window3 = Toplevel(window)
    window3.title('screen test')
    window.geometry('900x600')
    lblVideo = Label(window3)
    lblVideo.pack()
    string = ('Downloads/screen.mp4')
    player = tkvideo(string, lblVideo, loop=1, size=(500,500))

    player.play()


def Exit():
    window.destroy()

window.mainloop()