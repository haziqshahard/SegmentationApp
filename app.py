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
        self.theme = "dark-blue"
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme(self.theme)
        # self.after(0, lambda:self.state('zoomed'))
        self.settings = {}
        self.base_path = None
        self.preloadcases()
        
        self.current_slice = 1
        self.slice_index = 0
        self.current_time = 1
        self.time_index = 0

        self.load_images()

        self.grid_rowconfigure(0, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.segmentor = PolygonDrawer(self, row=0, column=0)
        # segmentor.grid(row=0, column=0, sticky="ns")
        self.viewhelper = ViewHelper(self, row=0, column=1)
        # viewhelper.grid(row=0, column=1, sticky="ns")
        self.caseselector = CaseSelector(self, row=1, column=0)

        self.title("Segmentor App")
        self.protocol("WM_DELETE_WINDOW", lambda d="delete": saveeverything(d))

        def saveeverything(d):
            self.segmentor.save_settings(d)
            self.caseselector.savecases()

        #Run app 
        self.mainloop()

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