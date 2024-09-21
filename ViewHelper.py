import os   
import re
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw,ImageOps
import cv2
import numpy as np
import matplotlib.pyplot as plt
from CTkMessagebox import CTkMessagebox
import ast

class ViewHelper(ctk.CTkFrame):
    """
    Features to add:
    has to check for the existence of a "segmented" folder within the current directory
    if it does exist, draw a polygon of "region of interest" on top of the existing slice
    the opacity has to be adjustable
        Add a slider with polygon opacity adjustment
    Has to check live for segmentation being drawn, and also check for 
    ISSUES:
    render_polygon has to show the polygon if it exists, and not show it if it doesnt
    shouldn't need constant toggling in order to show the thing
    """
    def __init__(self, window, debug=False, row=1, column=0):
        super().__init__(window)
        self.debug = debug
        self.configure(fg_color="transparent")
        self.window = window
        # self.grid(sticky="nsew")
        ctk.set_appearance_mode("dark")
        if self.debug == False:
            ctk.set_default_color_theme(self.window.theme)  # Other themes: "blue", "green"
        else:
            ctk.set_default_color_theme("blue")
        self.font = "Helvetica"

        if debug==True:
            self.window.columnconfigure(0, weight=1)
            self.window.rowconfigure(0, weight=1)

        self.root = ctk.CTkFrame(master=self.window)
        if debug==False:
            self.root.grid(row=row, column=column,padx=5, pady=5, sticky="nsew")
        else:
            self.root.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Initialize variables
        self.time_index = 0
        self.slice_index = 0
        self.original_width = 200
        self.original_height = 400
        self.aspect_ratio = 1
        self.last_width = 200
        self.font_size=15
        self.show_polygon = False

        self.points = []
        self.currentdottags = []
        self.scale_factor = 1
        self.scaledpoints = []
        self.lines=[]
        self.polytag = None

        self.line_width = 3
        self.linecolor = "#001C55"
        self.polygoncolor = (0,0,255,int(0.2*255))

        # Load base path and images
        if debug==False:
            self.base_path = window.base_path
        else:
            self.base_path = filedialog.askdirectory(title="Select the base folder")
        #If the base_path is empty, needs to just display "Please select case file"

        # print(self.base_path)
        self.load_images()
        self.settings = {}
        self.load_settings()

        # Load the initial image
        self.load_image(self.slice_index, self.time_index)
       
        self.context_menu = tk.Menu(master=self.root, tearoff=0)
        self.context_menu.add_command(label="Toggle Drawn Polygon", command=self.toggle_polygon)
        self.context_menu.add_command(label="Invert All Folder Masks", command=self.invert_masks)
        # self.context_menu.add_command(label = "Toggle Current Polygon")
        # Bind arrow keys
        self.bind_keys()
        self.window.focus_set()

    def hextocomp(self,hex):
            factor = 0.5
            factor = max(0, min(factor, 1))
            if isinstance(hex, tuple):
                r,g,b,a = hex
                # Calculate the darker color by applying the factor
                r = int(r * factor)
                g = int(g * factor)
                b = int(b * factor)

                return (r,g,b,a)
            else:
                # Ensure the factor is between 0 and 1
                hex = hex.replace(f"#", "")
                # Convert the hex color to RGB
                r, g, b = tuple(int(hex[i:i + 2], 16) for i in (0, 2, 4))
                # Calculate the darker color by applying the factor
                r = int(r * factor)
                g = int(g * factor)
                b = int(b * factor)

                # Convert back to hex
                return f'#{r:02x}{g:02x}{b:02x}'

    def update(self):
        self.destroy()
        self.window.viewhelper = ViewHelper(self.window, row=0, column=1)

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

    def load_image(self, slice_index, time_index):
        """Load and display the image based on current slice and time index."""
        time_folder = self.time_folders[time_index]
        slice_file = self.slice_files[time_index][slice_index]
        self.image_path = os.path.join(self.base_path, time_folder, slice_file)

        # Convert to the correct format for the operating system
        self.image_path = self.image_path.replace('\\', '/')
        self.mask_path = self.base_path + "/time{time:03}/segmented/Segmented Slice{slice:03}.png".format(time=self.time_index+1, slice=self.slice_index+1)
        # print(self.image_path)
        # print(f"Loading image: {image_path}")  # Debugging line

        try:
            self.img = Image.open(self.image_path) # Resize the image for display
            self.photo = ImageTk.PhotoImage(self.img)
            
            self.original_width = self.img.width
            self.original_height = self.img.height
            self.last_width = self.original_width
            self.aspect_ratio = self.original_width/self.original_height

            pad_frame = ctk.CTkFrame(master=self.root, width = 200,height=200,border_width = 0, border_color="blue")
            # pad_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=20)
            pad_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10,0))
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
            pad_frame.configure(width=self.original_width, height=self.original_height)    

            #Time/Slice info
            self.info = ctk.CTkFrame(master=self.root)
            self.info.grid(row=1, column=0, padx=5, pady=5, sticky="ns")    
            self.info.grid_rowconfigure(0, weight=1)
            self.info.grid_columnconfigure(0, weight=1)
            self.labelinfo =ctk.CTkLabel(master=self.info, text=f"Time: {self.time_index+1:02d}/{len(self.time_folders)}, Slice: {self.slice_index+1:02d}/{len(self.slice_files[0])}",
                                         font=('TkDefaultFont',self.font_size+5,'bold'))
            self.labelinfo.grid(row=0,column=0, padx=10, sticky="")

            #Info box for file movements
            self.moveinfo = ctk.CTkFrame(master=self.root)
            self.moveinfo.grid(row=1, column=0, padx=(10,10), pady=5,sticky="e")
            self.moveinfo.rowconfigure(0, weight=0)
            self.moveinfo.rowconfigure(1, weight=0)
            right_arrow = "\u2192"
            left_arrow = "\u2190"
            up_arrow = "\u219F"
            down_arrow = "\u21A1"

            self.labelfontsize = 15

            padx=4
            upbox = ctk.CTkFrame(master=self.moveinfo, border_width =1)
            upbox.grid(row=0,column=1, padx=padx, pady=0, sticky="nsew")
            uplabel = ctk.CTkLabel(master=upbox, text=f"△", font=(self.font, self.labelfontsize,'bold'), anchor='center', justify='center')
            uplabel.grid(row=0,column=0, padx=7, pady=(1,1), sticky="nsew")
            
            downbox = ctk.CTkFrame(master=self.moveinfo, border_width =1)
            downbox.grid(row=1,column=1, padx=padx, pady=0, sticky="nsew")
            downlabel = ctk.CTkLabel(master=downbox, text=f"▽", font=(self.font, self.labelfontsize,'bold'), anchor='center', justify='center')
            downlabel.grid(row=0,column=0, padx=7, pady=(1,1), sticky="nsew")
            
            leftbox = ctk.CTkFrame(master=self.moveinfo, border_width =1)
            leftbox.grid(row=1,column=0, padx=(padx,0), pady=0, sticky="nsew")
            leftlabel = ctk.CTkLabel(master=leftbox, text=f"◁", font=(self.font, self.labelfontsize+10,'bold'), anchor='center', justify='center')
            leftlabel.grid(row=0,column=0, padx=7, pady=(1,1), sticky="nsew")

            rightbox = ctk.CTkFrame(master=self.moveinfo, border_width =1)
            rightbox.grid(row=1,column=2, padx=(0,padx), pady=0, sticky="nsew")
            rightlabel = ctk.CTkLabel(master=rightbox, text=f"▷", font=(self.font, self.labelfontsize+10,'bold'), anchor='center', justify='center')
            rightlabel.grid(row=1,column=2, padx=7, pady=(1,1), sticky="nsew")

            #Display image
            self.canvimg = self.canvas.create_image(0,0,image=self.photo, anchor=tk.NW, tags="image") #tagged to easily access from the canvas items
            
            # #Display polygon
            # self.render_polygon()     
        
        except Exception as e:
            CTkMessagebox(master=self.window, message=f"Error loading image: {e}", icon="cancel")
            
    def bind_keys(self):
        self.canvas.bind("<Configure>", self.on_resize)

        if self.debug == True:
            """Bind arrow keys to the widget."""
            self.window.bind("<Right>", self.on_key_press)
            self.window.bind("<Left>", self.on_key_press)
            self.window.bind("<Up>", self.on_key_press)
            self.window.bind("<Down>", self.on_key_press)

        self.canvas.bind("<Button-3>", self.handle_right_click)

    def on_resize(self,event):
        self.root.grid_rowconfigure(0,minsize=self.root.winfo_height()*(9/10))
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

        if len(self.points) != 0:
            self.scaledpoints = [(a * self.scale_factor, b * self.scale_factor) for a, b in self.points] #Scale all the original points to match the current scale
        self.line_width = self.line_width*self.item_scale_factor
        self.delete_polygon()
        self.render_polygon()

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
        if self.show_polygon:
            if os.path.isfile(self.mask_path):
                self.masktopoints(self.mask_path)
                # print(path)
                self.render_polygon()
            else:
                # print("should be deleting")
                self.delete_polygon()
                self.points = []
                self.scaledpoints = []
        else:
            # print("clearing points")
            self.points = []
            self.scaledpoints = []

    def handle_right_click(self,event):
        clicked_items = self.canvas.find_withtag("current")
        if not clicked_items or ("dot" not in self.canvas.gettags(clicked_items[0]) and 
                                 "line" not in self.canvas.gettags(clicked_items[0])):
            self.context_menu.post(event.x_root, event.y_root)

    def invert_masks(self):
        def invert_images_in_folder(folder_path):
            # Loop through all files in the specified folder
            for filename in os.listdir(folder_path):
                # Construct full file path
                file_path = os.path.join(folder_path, filename)
                
                # Check if the file is an image (you can add more extensions if needed)
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    try:
                        # Open the image
                        with Image.open(file_path) as img:
                            # Invert the image colors
                            inverted_image = ImageOps.invert(img.convert("L"))
                            
                            # Save the inverted image back to the original file
                            inverted_image.save(file_path)
                            
                        # print(f"Inverted and saved: {filename}")
                    except Exception as e:
                        print(f"Could not process {filename}: {e}")

        msg = CTkMessagebox(master=self.window, title="Invert Masks?", message=f"Do you want to invert all the masks in {os.path.dirname(self.mask_path)}?",
                        icon="question", option_1="Cancel", option_3="Yes")
        response = msg.get()
        
        if response == "Yes":
            invert_images_in_folder(os.path.dirname(self.mask_path))
            CTkMessagebox(master=self.window, message=f"Successfully inverted all images in {os.path.dirname(self.mask_path)}")
        else:
            return
    


    def load_settings(self):
        if os.path.exists('save.txt'):
            with open("save.txt", 'r') as file:
                for line in file:
                    # Strip any surrounding whitespace and skip empty lines
                    line = line.strip()
                    if line and '=' in line:
                        # Split the line into key and value
                        key, value = line.split('=', 1)
                        self.settings[key.strip()] = value.strip()
            if self.settings.get('linecolor') is not None:
                self.linecolor = self.settings.get('linecolor')
            if self.settings.get('numpoints') is not None:
                self.numpoints = 2*int(self.settings.get('numpoints'))
            if self.settings.get('polygoncolor') is not None:
                try:
                    self.polygoncolor = ast.literal_eval(self.settings.get('polygoncolor'))
                except:
                    self.polygoncolor = None


    def toggle_polygon(self):
        #check if the segmented mask even exists
        if self.show_polygon:
            self.show_polygon = False
            # print("NOT Showing polygon")
        else:
            self.show_polygon = True
        self.render_polygon()
    
    def render_polygon(self):
        if self.show_polygon:
            # print(f"Current time:{self.time_index}, Current Slice:{self.slice_index}")
            self.delete_polygon()
            if os.path.isfile(self.mask_path):
                self.masktopoints(self.mask_path)
            if len(self.points) == 0:
                return
            else:
                 # Draw lines between points
                if len(self.scaledpoints) > 1:
                    if len(self.scaledpoints) > 2:
                        self.PILdrawpoly()
                        self.polytag = self.canvas.create_image(0, 0, image=self.polygon, anchor=tk.NW)
                        lowest_item_id = self.canvas.find_all()[1]
                        self.canvas.tag_lower(self.polytag, lowest_item_id)
                    for i in range(len(self.scaledpoints) - 1):
                        if "cavity" in self.currentdottags[i] and "cavity" in self.currentdottags[i+1]:
                            line = self.canvas.create_line(self.scaledpoints[i], self.scaledpoints[i+1], fill=self.hextocomp(self.linecolor), tags=("line","cavity"), width = self.line_width*self.scale_factor)
                        else:
                            line = self.canvas.create_line(self.scaledpoints[i], self.scaledpoints[i+1], fill=self.linecolor, tags="line", width = self.line_width*self.scale_factor)               
                        self.lines.append(line)
                    if len(self.points) > 2 and self.points[0] != self.points[-1]:
                        if "cavity" in self.currentdottags[-1] and "cavity" in self.currentdottags[0]:
                            line = self.canvas.create_line(self.scaledpoints[-1], self.scaledpoints[0], fill=self.hextocomp(self.linecolor), tags=("line","cavity"), width = self.line_width*self.scale_factor)
                        else:
                            line = self.canvas.create_line(self.scaledpoints[-1], self.scaledpoints[0], fill=self.linecolor, tags="line", width = self.line_width*self.scale_factor)               
                        self.lines.append(line)
        else:
            self.delete_polygon()

    def delete_polygon(self):
        for line in self.canvas.find_withtag("line"):
                    self.canvas.delete(line)
        if self.polytag is not None:
            self.canvas.delete(self.polytag)    
                  
    def PILdrawpoly(self):
        # print(self.currentdottags)
        if len(self.currentdottags) >2:
            dottags = self.currentdottags
            # print(f"Switched tags:{dottags}")
        #If cavity is present in the tag, get the index and then take it from self.scaledpoints

        cavidx = [index for index, tup in enumerate(dottags) if "cavity" in tup]
        cavitypoints = [self.scaledpoints[i] for i in cavidx]

        overlay = Image.new('RGBA', (self.current_width, self.current_height), (255,255,255,0))
        draw = ImageDraw.Draw(overlay)
        #Draw the polygon on the image
        draw.polygon(self.scaledpoints, fill = self.polygoncolor)
        if len(cavitypoints)>2:
            draw.polygon(cavitypoints, fill=self.hextocomp(self.polygoncolor))

        # Display the result on the canvas
        self.polygon = ImageTk.PhotoImage(overlay)

    def updateimage(self, slice_index, time_index):
        time_folder = self.time_folders[time_index]
        slice_file = self.slice_files[time_index][slice_index]
        self.image_path = os.path.join(self.base_path, time_folder, slice_file)

        # Convert to the correct format for the operating system
        self.image_path = self.image_path.replace('\\', '/')
        try:
            self.img = Image.open(self.image_path) # Resize the image for display
            self.photo = ImageTk.PhotoImage(self.img)
        except OSError:
            CTkMessagebox(message=f"Image f{self.image_path} not loaded, likely OneDrive Issue.",icon="cancel")
            
        # Calculate new width and height while maintaining aspect ratio
        new_width = int(self.original_width * self.scale_factor)
        new_height = int(self.original_height * self.scale_factor)

        #Updating canvas with the current scaled image
        scaled_image = self.img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.scaled_photo = ImageTk.PhotoImage(scaled_image)
        #Update canvas and the image size
        self.canvas.itemconfig(self.canvimg, image=self.scaled_photo)

        #Update label
        self.labelinfo.configure(text=f"Time: {self.time_index+1:02d}/{len(self.time_folders)}, Slice: {self.slice_index+1:02d}/{len(self.slice_files[0])}")    
    
    def masktopoints(self,maskpath):
        # Load the PNG image as a grayscale image (0 means grayscale mode)
        binary_mask = cv2.imread(maskpath, cv2.IMREAD_GRAYSCALE)
        myocard_mask = binary_mask.copy()
        myocard_mask[myocard_mask==127] = 0 
        contours, _ = cv2.findContours(myocard_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Get the first contour (assuming you only have one object)
        boundary_points = contours[0]  # (N, 1, 2) array representing x, y coordinates

        numpoints = self.numpoints
        step = len(boundary_points)//numpoints
        boundary_points = boundary_points[::step]
        self.points = [tuple(arr.flatten()) for arr, in boundary_points]
        if len(self.points) != 0:
            self.scaledpoints = [(a * self.scale_factor, b * self.scale_factor) for a, b in self.points] #Scale all the original points to match the current scale
        self.currentdottags = [("dot",)] * len(self.points)

        def check_cavity_around_point(center, radius,image=binary_mask):
            # Create a mask with the same size as the image, initialized to zeros
            mask = np.zeros(image.shape[:2], dtype=np.uint8)

            # Draw a filled circle on the mask
            cv2.circle(mask, center, radius, 255, thickness=-1)

            # Use the mask to get the region of interest from the image
            circular_patch = cv2.bitwise_and(image, image, mask=mask)

            # Check if any pixel in the circular patch has the value of 127
            return np.any(circular_patch == 127)

        for i in range(len(self.points)):
            if check_cavity_around_point(self.points[i], 4):
                #Set the tag to be "dot","cavity"
                self.currentdottags[i] = ("dot","cavity")

# Create the main window
if __name__ == "__main__":
    root = ctk.CTk()
    root.title("ViewHelper")

    imagescroller = ViewHelper(root, debug=True)
    root.mainloop()
            

