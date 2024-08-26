import tkinter as tk
from tkinter import filedialog, Text
import os
from customtkinter import *

mode = "dark"

def doNothing():
    print("ok ok I wont")

def switchDarkmode():
    global mode
    if mode == "dark":
        set_appearance_mode("light")
        mode = "light"
    else:
        set_appearance_mode("dark")
        mode = "dark"

app=CTk()
app.geometry("500x400")

btn = CTkButton(master=app, text="Click Me", corner_radius=32,command=doNothing)
btn.place(relx=0.5, rely=0.5, anchor="center")

menu = tk.Menu(app)
app.config(menu = menu)

subMenu = tk.Menu(menu)
menu.add_cascade(label="File",menu=subMenu)
subMenu.add_command(label="Do Nothing",command=doNothing)
subMenu.add_separator()
subMenu.add_command(label="Exit",command=doNothing)
subMenu.add_command(label="Light/Dark",command=switchDarkmode)

editMenu=tk.Menu(menu)
menu.add_cascade(label="Edit",menu=editMenu)
editMenu.add_command(label="Undo",command=doNothing)

app.mainloop()