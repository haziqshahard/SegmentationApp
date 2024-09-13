import tkinter as tk
from tkinter import filedialog, Text
import os
import sys
from customtkinter import *
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Segmentor import *
from ViewHelper import *
from CaseSelector import *

#When the app launches
#Pull from the case viewer
#If there is nothing in the case viewer
#Display in the polygon viewer and the view helper (please select a case)
#Whatever button is clicked in the case viewer, update the base path for both the segmentor and the view helper

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # self.grid(sticky="nsew")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # Other themes: "blue", "green"

        self.base_path = []
        self.current_slice = 1
        self.slice_index = 0
        self.current_time = 1
        self.time_index = 0

if __name__ == "__main__":
    app = App()
    app.mainloop()
            



# frame = CTkFrame(master=app, border_width=2)
# frame.pack(expand=True)

# btn = CTkButton(master=frame, text="Click Me", corner_radius=32,command=doNothing)
# btn.place(relx=0.5, rely=0.5, anchor="center"_
# tabview = CTkTabview(master=app)

# tabview.pack(padx=20,pady=20)
# tabview.add("Tab 1") #CAN USE TABS TO PLACE THE TYPE OF VIEWER YOU WANT
# tabview.add("Tab 2")