from tkinter import filedialog
import os
import sys
from utils import *
from CTkMenuBar import *

from Segmentor import *
from ViewHelper import *
from CaseSelector import *
from MaskViewer import *
from ThreeDViewer import *

class App(ctk.CTk):
    """
    #Add a commenting system for individual points with the right click   

    Remove the window that confirms saves, put a text confirmation at the bottom of the window
    Change the font sizing for mac, seems like a bug setting the default font for everything
    add a keyboard shortcut for saving

    """
    def __init__(self):
        super().__init__()
        self.theme = "dark-blue"
        self.darklight = "dark"
        ctk.set_appearance_mode(self.darklight)
        ctk.set_default_color_theme(self.theme)
        self.settings = {}
        self.base_path = ""
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
        self.line_width = 1
        self.polygoncolor = None
        self.current_time = int(self.slice_files[0][0][12:15])
        self.time_index = self.time_folders.index(f"time{self.current_time:03d}")
        self.slice_index = self.slice_files[self.time_index].index(f"slice{self.current_slice:03d}time{self.current_time:03d}.png")
        self.load_image(slice_index = self.slice_index, time_index = self.time_index)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # self.inforow = ctk.CTkFrame(self, fg_color=self.cget("fg_color"),border_width=0)
        # self.inforow.grid(row=1, column=0, columnspan=2, sticky="nsew")
        # self.inforow.grid_rowconfigure(0, weight=1)
        # self.inforow.grid_columnconfigure(0, weight=1)

        self.bottomrow = ctk.CTkFrame(self, fg_color=self.cget("fg_color"))
        self.bottomrow.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.bottomrow.grid_rowconfigure(0, weight=1)
        self.bottomrow.grid_columnconfigure(1, weight=1)
        self.bottomrow.grid_columnconfigure(2, weight=1)
        self.bottomrow.grid_columnconfigure(0, weight=1)

        self.inforow = ctk.CTkFrame(self, fg_color = self.cget("fg_color"),border_width=0)
        self.inforow.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.savelabel = ctk.CTkLabel(master=self.inforow, text="")
        self.savelabel.grid(row=0, column=0, padx=10)

        self.segmentor = PolygonDrawer(self, row=0, column=0,darklight=self.darklight)
        self.viewhelper = ViewHelper(self, row=0, column=1,darklight=self.darklight)
        self.caseselector = CaseSelector(self.bottomrow, row=0, column=0,theme=self.theme,darklight=self.darklight)
        self.maskviewer = MaskViewer(self.bottomrow, row=0,column=2,theme=self.theme,darklight=self.darklight)
        self.threedviewer = ThreeDViewer(self.bottomrow, row=0, column=1, theme=self.theme, darklight = self.darklight)
        
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
        caseselectorminsize = self.current_width *(3/7)

        self.grid_columnconfigure(0, minsize = self.current_width * (1/2))
        self.grid_columnconfigure(1, minsize = self.current_width * (1/2))
        self.grid_rowconfigure(0,minsize=toprowminsize)
        self.grid_rowconfigure(1, minsize=self.current_height * (1/4) * (10/11))    
        self.grid_rowconfigure(2, minsize=self.current_height * (1/4) * (1/11))

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
                check1, check2 = utils.load_images(self.base_path)
                while len(check1) == 0 or len(check2)==0:
                    self.base_path = filedialog.askdirectory(title="Please select an initial case")
                    check1, check2 = utils.load_images(self.base_path)
                    while self.base_path == '':
                        self.base_path= filedialog.askdirectory(title="Please select an initial case")
                        check1, check2 = utils.load_images(self.base_path)
                
            
        else:
            with open('save.txt', 'w') as file:
                pass
            #Force the user to select an initial case 
            check1, check2 = utils.load_images(self.base_path)
            while len(check1) == 0 or len(check2)==0:
                self.base_path = filedialog.askdirectory(title="Please select an initial case")
                check1, check2 = utils.load_images(self.base_path)
                while self.base_path == '':
                    self.base_path= filedialog.askdirectory(title="Please select an initial case")
                    check1, check2 = utils.load_images(self.base_path)

    def load_image(self, slice_index = 0, time_index=0):
        """Load and display the image based on current slice and time index."""
        time_folder = self.time_folders[time_index]
        slice_file = self.slice_files[time_index][slice_index]
        self.image_path = os.path.join(self.base_path, time_folder,"image" ,slice_file)
        # print("Image Path:" + self.image_path)

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