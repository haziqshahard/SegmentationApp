import tkinter as tk
from tkinter import filedialog, Text
import os
from customtkinter import *

mode = "dark"
set_default_color_theme("GhostTrain.json")

def doNothing():
    print("ok ok I wont")

app=CTk()
app.geometry("500x400")

#--------TaskBar at top--------
menu = tk.Menu(app)
app.config(menu = menu)

def switchDarkmode():
    global mode
    if mode == "dark":
        set_appearance_mode("light")
        mode = "light"
    else:
        set_appearance_mode("dark")
        mode = "dark"

subMenu = tk.Menu(menu)
menu.add_cascade(label="File",menu=subMenu)
subMenu.add_command(label="Do Nothing",command=doNothing)
subMenu.add_separator()
subMenu.add_command(label="Exit",command=doNothing)
subMenu.add_command(label="Light/Dark",command=switchDarkmode)

editMenu=tk.Menu(menu)
menu.add_cascade(label="Edit",menu=editMenu)
editMenu.add_command(label="Undo",command=doNothing)

# frame = CTkFrame(master=app, border_width=2)
# frame.pack(expand=True)

# btn = CTkButton(master=frame, text="Click Me", corner_radius=32,command=doNothing)
# btn.place(relx=0.5, rely=0.5, anchor="center")



app.mainloop()

# tabview = CTkTabview(master=app)

# tabview.pack(padx=20,pady=20)
# tabview.add("Tab 1") #CAN USE TABS TO PLACE THE TYPE OF VIEWER YOU WANT
# tabview.add("Tab 2")