import tkinter as tk
from tkinter import filedialog, Text
import os
import sys
from customtkinter import *
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Segmentor import *
from ViewHelper import *
from CaseSelector import *
from MaskViewer import *

#When the app launches
#Pull from the case viewer
#If there is nothing in the case viewer
#Display in the polygon viewer and the view helper (please select a case)
#Whatever button is clicked in the case viewer, update the base path for both the segmentor and the view helper

"""Have to implement cavity fill
Segmentor:
Have to have a new set of points, selectable with middle mouse button
different polygon fill and different colored dots
Should be able to select or deselect already existing points to make them cavity points
Needs to have error checks if points don't exist for this

ViewHelper:
Now needs to be able to display both the cavity and the myocardium
Have to be able to toggle either one individually
Add line width, color and polygon color settings for this too

#Features to add:
"""

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # self.grid(sticky="nsew")
        self.theme = "dark-blue"
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme(self.theme)
        # self.after(0, lambda:self.state('zoomed'))
        self.settings = {}
        self.base_path = None
        self.preloadcases()
        
        self.original_width = self.winfo_width()
        self.original_height = self.winfo_height()

        self.current_slice = 1
        self.slice_index = 0
        self.current_time = 1
        self.time_index = 0

        self.load_images()

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.segmentor = PolygonDrawer(self, row=0, column=0)
        self.viewhelper = ViewHelper(self, row=0, column=1)

        self.bottomrow = ctk.CTkFrame(self, fg_color=self.cget("fg_color"))
        self.bottomrow.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.bottomrow.grid_rowconfigure(0, weight=1)
        self.bottomrow.grid_columnconfigure(1, weight=1)
        self.bottomrow.grid_columnconfigure(0, weight=1)

        self.caseselector = CaseSelector(self.bottomrow, row=0, column=0,theme=self.theme)
        self.maskviewer = MaskViewer(self.bottomrow, row=0,column=1,theme=self.theme)
        # self.maskviewer.configure(fg_color="white",corner_radius=0)
        # self.caseselector.configure(height=5)
        
        self.title("Segmentor App")
        self.protocol("WM_DELETE_WINDOW", lambda d="delete": saveeverything(d))

        self.bind("<Configure>", self.on_resize)
        self.bind("<Right>", self.on_key_press)
        self.bind("<Left>", self.on_key_press)
        self.bind("<Up>", self.on_key_press)
        self.bind("<Down>", self.on_key_press)

        def saveeverything(d):
            self.segmentor.save_settings(d)
            self.caseselector.savecases()
        #Run app 
        self.mainloop()

    def on_resize(self,event):
        self.current_width = self.winfo_width()
        self.current_height = self.winfo_height()

        toprowminsize = self.current_height * (3/4)
        caseselectorminsize = self.current_width *(6/7)

        self.grid_rowconfigure(0,minsize=toprowminsize)
        self.bottomrow.grid_columnconfigure(0, minsize=caseselectorminsize)

    def on_key_press(self, event):
        self.maskviewer.on_key_press(event)
        self.viewhelper.on_key_press(event)
        
    def preloadcases(self):
        if os.path.exists('save.txt'):
            with open("save.txt", 'r') as file:
                for line in file:
                    # Strip any surrounding whitespace and skip empty lines
                    line = line.strip()
                    if line and '=' in line:
                        # Split the line into key and value
                        key, value = line.split('=', 1)
                        self.settings[key.strip()] = value.strip()
            if self.settings.get('paths') is not None:
                self.paths = ast.literal_eval(self.settings.get('paths'))
                self.base_path = self.paths[0][0]

            elif self.settings.get('paths') == None:
                #Force the user to select a case 
                self.base_path = filedialog.askdirectory(title="Select the base folder")
                while self.base_path == '':
                    self.base_path= filedialog.askdirectory(title="Please select an initial case")
            
        else:
            with open('save.txt', 'w') as file:
                pass
            #Force the user to select an initial case 
            self.base_path = filedialog.askdirectory(title="Please select an initial case")
            while self.base_path == '':
                self.base_path= filedialog.askdirectory(title="Please select an initial case")

    def load_images(self):
        """Load time folders and slice files."""
        # Regular expression to match time folders in the format time001, time002, etc.
        time_pattern = re.compile(r'^time\d{3}$')

        # Get all time folders matching the format
        self.time_folders = sorted([d for d in os.listdir(self.base_path) 
                                    if os.path.isdir(os.path.join(self.base_path, d)) and time_pattern.match(d)])
        # print(f"Time folders found: {len(self.time_folders)}")  # Debugging line

        # Get all slice files for each time folder
        self.slice_files = [sorted([f for f in os.listdir(os.path.join(self.base_path, t)) if os.path.isfile(os.path.join(self.base_path, t, f))]) for t in self.time_folders]
        # print(f"Slice files found: {len(self.slice_files[0])}")  # Debugging line
        self.load_image()

    def load_image(self, slice_index = 0, time_index=0):
        """Load and display the image based on current slice and time index."""
        time_folder = self.time_folders[time_index]
        slice_file = self.slice_files[time_index][slice_index]
        self.image_path = os.path.join(self.base_path, time_folder, slice_file)

        # Convert to the correct format for the operating system
        self.image_path = self.image_path.replace('\\', '/')
        # print(f"Loading image: {image_path}")  # Debugging line


if __name__ == "__main__":
    app = App()
    # app.mainloop()
            

# frame = CTkFrame(master=app, border_width=2)
# frame.pack(expand=True)

# btn = CTkButton(master=frame, text="Click Me", corner_radius=32,command=doNothing)
# btn.place(relx=0.5, rely=0.5, anchor="center"_
# tabview = CTkTabview(master=app)

# tabview.pack(padx=20,pady=20)
# tabview.add("Tab 1") #CAN USE TABS TO PLACE THE TYPE OF VIEWER YOU WANT
# tabview.add("Tab 2")