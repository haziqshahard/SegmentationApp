#Only really needs to view the viewhelpers mask, not the segmented one

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, Text
import re
import os
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont

class MaskViewer(ctk.CTkFrame):
    def __init__(self, window, debug=False, row=1, column=1, theme="blue"):
        super().__init__(window)
        self.debug = debug
        self.window = window
        # self.grid(sticky="nsew")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme(theme)
        self.font = "Helvetica"
        
        self.root = ctk.CTkFrame(master=self.window)
        if debug==True:
            self.window.columnconfigure(0, weight=1)
            self.window.rowconfigure(0, weight=1)
            self.configure(fg_color="transparent")
            self.root.grid(row=0, column=0, padx=5, pady=5)
        else:
            self.root.grid(row=row, column=column,columnspan=1,padx=5, pady=5, sticky="nsew")
            # self.configure(fg_color="transparent")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        # self.configure(fg_color="blue",corner_radius=0)
        # Initialize variables
        self.time_index = 0
        self.slice_index = 0
        self.original_width = 10
        self.original_height = 50
        self.aspect_ratio = 1
        self.last_width = self.original_width
        self.scale_factor = 1

        # Load base path and images

        if debug==False:
            self.base_path = self.window.master.base_path
        elif debug ==True:
            self.base_path = filedialog.askdirectory(title="Select the base folder")
            """Bind arrow keys to the widget."""
            self.window.bind("<Right>", self.on_key_press)
            self.window.bind("<Left>", self.on_key_press)
            self.window.bind("<Up>", self.on_key_press)
            self.window.bind("<Down>", self.on_key_press)

        # Load the initial image
        self.load_images()
        self.load_image(self.slice_index, self.time_index)
        self.canvas.bind("<Configure>", self.on_resize)


    def update(self):
        self.destroy()
        self.window.master.maskviewer = MaskViewer(self.window, row=0, column=1)

    def loadmask(self):
        if os.path.isfile(self.mask_path):
            self.img = Image.open(self.mask_path) # Resize the image for display
            self.photo = ImageTk.PhotoImage(self.img)
        else:
            image = Image.open(self.image_path)
            text = f"time{self.time_index+1:03}/slice{self.slice_index+1:03}\nhas no segmentations"
            # Create a black image
            width, height = image.size[0], image.size[1] # Set the desired dimensions
            img = Image.new("RGB", (width, height), "black")

            # Create a Draw object
            draw = ImageDraw.Draw(img)
            # Optionally, load a font (default font is used if not specified)
            font = ImageFont.truetype("arial.ttf", 30)  # Use default font
            # Alternatively, you can specify a font: font = ImageFont.truetype("arial.ttf", font_size)

            # Get the bounding box for the text
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            # Calculate position to center the text
            position = ((width - text_width) // 2, (height - text_height) // 2)
            # Add white text to the image
            draw.text(position, text, fill="white", font=font, align = "center")
            self.img = img
            self.photo = ImageTk.PhotoImage(img)

    def updateimage(self, slice_index, time_index):
        self.mask_path = self.base_path + "/time{time:03}/segmented/Segmented Slice{slice:03}.png".format(time=self.time_index+1, slice=self.slice_index+1)
        # time_folder = self.time_folders[time_index]
        # slice_file = self.slice_files[time_index][slice_index]
        # self.image_path = os.path.join(self.base_path, time_folder, slice_file)
        self.loadmask()
        # Convert to the correct format for the operating system
        # self.image_path = self.image_path.replace('\\', '/')
        # Calculate new width and height while maintaining aspect ratio
        new_width = int(self.original_width * self.scale_factor)
        new_height = int(self.original_height * self.scale_factor)

        #Updating canvas with the current scaled image
        scaled_image = self.img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.scaled_photo = ImageTk.PhotoImage(scaled_image)
        #Update canvas and the image size
        self.canvas.itemconfig(self.canvimg, image=self.scaled_photo)

    def on_key_press(self, event):
        """Handle key press events."""
        # print(f"Key pressed: {event.keysym}")  # Debugging line
        if event.keysym == "Up":
            self.time_index = (self.time_index + 1) % len(self.time_folders)
        elif event.keysym == "Down":
            self.time_index = (self.time_index - 1) % len(self.time_folders)
        elif event.keysym == "Left":
            self.slice_index = (self.slice_index - 1) % len(self.slice_files[self.time_index])
        elif event.keysym == "Right":
            self.slice_index = (self.slice_index + 1) % len(self.slice_files[self.time_index])

        self.updateimage(self.slice_index, self.time_index)
        self.mask_path = self.base_path + "/time{time:03}/segmented/Segmented Slice{slice:03}.png".format(time=self.time_index+1, slice=self.slice_index+1)
        # print(self.time_index, self.slice_index)

    def load_images(self):
        """Load time folders and slice files."""
        # Regular expression to match time folders in the format time001, time002, etc.
        #The base path will be the cases path
        time_pattern = re.compile(r'^time\d{3}$')

        # Get all time folders matching the format
        self.time_folders = sorted([d for d in os.listdir(self.base_path) 
                                    if os.path.isdir(os.path.join(self.base_path, d)) and time_pattern.match(d)])
        # print(f"Time folders found: {len(self.time_folders)}")  # Debugging line

        # Get all slice files for each time folder
        self.slice_files = [sorted([f for f in os.listdir(os.path.join(self.base_path, t)) if os.path.isfile(os.path.join(self.base_path, t, f))]) for t in self.time_folders]
        # print(f"Slice files found: {len(self.slice_files[0])}")  # Debugging line

    
    def on_resize(self,event):
        scale_x = self.canvas.winfo_width() / self.original_width
        scale_y = self.canvas.winfo_height() / self.original_height

        self.current_width = self.canvas.winfo_width()
        self.current_height = self.canvas.winfo_height()

        self.scale_factor = min(scale_x, scale_y)
         
        # Calculate new width and height while maintaining aspect ratio
        new_width = int(self.original_width * self.scale_factor)
        new_height = int(self.original_height * self.scale_factor)

        #Debugging step - for whatever reason it initializes at 0
        if new_height == 0:
            new_height = 1

        if new_width == 0:
            new_width = 1

        #Scaling image and photo
        scaled_image = self.img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.scaled_photo = ImageTk.PhotoImage(scaled_image)
        #Update canvas and the image size
        self.canvas.configure(width=new_width,height = new_height)
        self.canvas.itemconfig(self.canvimg, image=self.scaled_photo)
        
        #Item scaling information
        self.item_scale_factor = new_width / self.last_width
        self.last_width = new_width

    def load_image(self, slice_index, time_index):
        """Load and display the image based on current slice and time index."""
        time_folder = self.time_folders[self.time_index]
        slice_file = self.slice_files[self.time_index][self.slice_index]
        self.image_path = os.path.join(self.base_path, time_folder, slice_file)

        # Convert to the correct format for the operating system
        # self.image_path = self.image_path.replace('\\', '/')
        self.mask_path = self.base_path + "/time{time:03}/segmented/Segmented Slice{slice:03}.png".format(time=self.time_index+1, slice=self.slice_index+1)
        # print(self.image_path)
        # print(f"Loading image: {image_path}")  # Debugging line
        self.loadmask()
        try:            
            self.original_width = self.img.width
            self.original_height = self.img.height
            self.last_width = self.original_width
            self.aspect_ratio = self.original_width/self.original_height

            pad_frame = ctk.CTkFrame(master=self.root, width = 20,height=20,border_width = 0, border_color="blue", fg_color="transparent")
            # pad_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=20)
            pad_frame.grid(row=0, column=0, padx=10, pady=10)
            self.canvas = tk.Canvas(self.root, width=self.original_width, height=self.original_height, scrollregion=(0, 0, 0, 0), borderwidth=0, highlightbackground="#000000" )

            def set_aspect(content_frame, pad_frame, aspect_ratio):
                    # Taken from user Bryan Oakley : https://stackoverflow.com/a/16548607
                    # a function which places a frame within a containing frame, and
                    # then forces the inner frame to keep a specific aspect ratio
                        def enforce_aspect_ratio(event):
                            # when the pad window resizes, fit the content into it,
                            # either by fixing the width or the height and then
                            # adjusting the height or width based on the aspect ratio.

                            # start by using the width as the controlling dimension
                            desired_width = event.width
                            desired_height = int(event.width / aspect_ratio)

                            # if the window is too tall to fit, use the height as
                            # the controlling dimension
                            if desired_height > event.height:
                                desired_height = event.height
                                desired_width = int(event.height * aspect_ratio)

                            x_center = (event.width - desired_width) // 2
                            y_center = (event.height - desired_height) // 2

                            # place the window, giving it an explicit size
                            content_frame.place(in_=pad_frame, x=x_center, y=y_center, anchor="nw",
                                width=desired_width, height=desired_height)

                        pad_frame.bind("<Configure>", enforce_aspect_ratio)
            set_aspect(self.canvas,pad_frame, aspect_ratio=self.aspect_ratio)
            self.root.rowconfigure(0, weight=1)
            self.root.columnconfigure(0,weight=1)
            pad_frame.configure(width=self.original_width, height=self.original_height)    
            #Display image
            self.canvimg = self.canvas.create_image(0,0,image=self.photo, anchor=tk.NW, tags="image") #tagged to easily access from the canvas items
            
            # #Display polygon
            # self.render_polygon()     
        
        except Exception as e:
            CTkMessagebox(master=self.window, message=f"Error loading image: {e}", icon="cancel")

if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Mask Viewer")

    imagescroller = MaskViewer(root, debug=True)
    root.mainloop()