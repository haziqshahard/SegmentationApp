from tkinter import filedialog
import os
import sys
from utils import *
from CTkMenuBar import *

from Segmentor import *
from ViewHelper import *
from CaseSelector import *
from MaskViewer import *

class App(ctk.CTk):
    """
    Increase size of cursor when holding c down
    """
    def __init__(self):
        super().__init__()
        self.theme = "dark-blue"
        self.darklight = "dark"
        ctk.set_appearance_mode(self.darklight)
        ctk.set_default_color_theme(self.theme)
        self.settings = {}
        self.base_path = None
        self.preloadcases()
        # Make the window fullscreen on the monitor
        self.attributes('-fullscreen', True)
        toggle = True
    
        # Optionally, you can bind the 'Esc' key to exit fullscreen
        def exit_fullscreen(event=None):
            self.attributes('-fullscreen', False)
            self.state('zoomed')

        self.bind("<Escape>", exit_fullscreen)

        self.original_width = self.winfo_width()
        self.original_height = self.winfo_height()

        self.slice_files, self.time_folders = utils.load_images(self.base_path)
        # print(self.slice_files)
        # print(self.time_folders)

        self.current_slice = 1
        self.current_time = int(self.slice_files[0][0][12:15])
        self.time_index = self.time_folders.index(f"time{self.current_time:03d}")
        self.slice_index = self.slice_files[self.time_index].index(f"slice{self.current_slice:03d}time{self.current_time:03d}.png")
        self.load_image(slice_index = self.slice_index, time_index = self.time_index)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # self.inforow = ctk.CTkFrame(self, fg_color=self.cget("fg_color"),border_width=0)
        # self.inforow.grid(row=1, column=0, columnspan=2, sticky="nsew")
        # self.inforow.grid_rowconfigure(0, weight=1)
        # self.inforow.grid_columnconfigure(0, weight=1)

        self.bottomrow = ctk.CTkFrame(self, fg_color=self.cget("fg_color"),border_width=0)
        self.bottomrow.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.bottomrow.grid_rowconfigure(0, weight=1)
        self.bottomrow.grid_columnconfigure(1, weight=1)
        self.bottomrow.grid_columnconfigure(0, weight=1)

        self.segmentor = PolygonDrawer(self, row=0, column=0,darklight=self.darklight)
        self.viewhelper = ViewHelper(self, row=0, column=1,darklight=self.darklight)
        self.caseselector = CaseSelector(self.bottomrow, row=0, column=0,theme=self.theme,darklight=self.darklight)
        self.maskviewer = MaskViewer(self.bottomrow, row=0,column=1,theme=self.theme,darklight=self.darklight)
        # self.maskviewer.configure(fg_color="white",corner_radius=0)
        # self.caseselector.configure(height=5)
        
        self.title("Segmentor App")
        self.protocol("WM_DELETE_WINDOW", lambda d="delete": saveeverything(d))
        self.bind("<Control-d>", self.switchDarkmode)
        # self.bind("<Control-t>", self.switchtheme)
        self.bind("<Configure>", self.on_resize)
        self.bind("<Right>", self.on_key_press)
        self.bind("<Left>", self.on_key_press)
        self.bind("<Up>", self.on_key_press)
        self.bind("<Down>", self.on_key_press)
        self.bind("<A>", self.on_key_press)
        self.bind("<a>", self.on_key_press)
        self.bind("<D>", self.on_key_press)
        self.bind("<d>", self.on_key_press)

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
        # self.grid_rowconfigure(1, minsize=(1-toprowminsize)*(1/2))
        self.bottomrow.grid_columnconfigure(0, minsize=caseselectorminsize)

    def on_key_press(self, event):
        self.segmentor.on_key_press(event)
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

    def load_image(self, slice_index = 0, time_index=0):
        """Load and display the image based on current slice and time index."""
        time_folder = self.time_folders[time_index]
        slice_file = self.slice_files[time_index][slice_index]
        self.image_path = os.path.join(self.base_path, time_folder, slice_file)

        # Convert to the correct format for the operating system
        self.image_path = self.image_path.replace('\\', '/')
        # print(f"Loading image: {image_path}")  # Debugging 

    def switchDarkmode(self,event):
        if self.darklight == "dark":
            ctk.set_appearance_mode("light")
            self.darklight = "light"
        else:
            ctk.set_appearance_mode("dark")
            self.darklight = "dark"
            
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