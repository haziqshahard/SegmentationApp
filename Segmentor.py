import tkinter as tk 
import re
import customtkinter as ctk
from CTkColorPicker import *
from CTkMenuBar import *
import ctk_color_picker_alpha as ctkpa
from PIL import Image, ImageTk, ImageDraw,ImageOps
from tkinter import filedialog
import numpy as np
import os
from scipy.interpolate import splprep, splev
from CTkMessagebox import CTkMessagebox
import ast
import cv2
import utils

class PolygonDrawer(ctk.CTkFrame):
    """
    #Window that enables the user to draw on the image required
    #Features:
    -Dots can be individually placed, deletable
    -Lines automatically generate between each dot
    -The space fills with a choosable color
    -The whole polygon can be removed
    -TWO MODES:
        Draw mode: Can bring forth previous mask, but does NOT save the current one when switching modes
        Edit mode: Checks to see the existence of segmented, and allows for redrawing and then saving.
    Features:
    Implement a dragging path to automatically convert any points within to cavity

    #BUG:
    When deleting a point, and trying to place a new point on that line, it bugs out.
    When saving mask, just print it somewhere on the segmentor, rather than bringing up the ctktoplevel
    """
    def __init__(self,window, image_path="", debug=False, row=1, column=0,darklight="dark"):
        super().__init__(window)
        self.debug = debug
        self.window = window
        ctk.set_appearance_mode(darklight)
        if self.debug == False:
            ctk.set_default_color_theme(self.window.theme)  # Other themes: "blue", "green"
        else:
            ctk.set_default_color_theme("blue")
        self.fontsize = 20
        self.font = 'Helvetica'
        self.settings = {}

        if debug==True:
            self.window.columnconfigure(0, weight=1)
            self.window.rowconfigure(0, weight=1) 
        self.window.protocol("WM_DELETE_WINDOW", lambda d="delete": self.save_settings(d))

        self.root = ctk.CTkFrame(master=self.window)
        if debug==False:
            self.root.grid(row=row, column=column, padx=5, pady=5,  sticky="nsew")
        else:
            self.root.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        # Configure rows
        for i in range(2): 
            self.root.grid_rowconfigure(i, weight=1)

        # Configure columns
        for i in range(3):
            self.root.grid_columnconfigure(i, weight=1)

        pad_frame = ctk.CTkFrame(master=self.root)
        # pad_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=20)
        pad_frame.grid(row=0, column=0,columnspan=3, sticky="nsew", padx=10, pady=(10,0))
        
        #Loading image
        if debug==False:
            self.image_path = window.image_path
        else:
            self.image_path = filedialog.askopenfilename(title="Select an image")
        self.current_slice = int(os.path.basename(self.image_path)[5:8])
        self.current_time = int(os.path.basename(self.image_path)[12:15])
        
        self.base_path = "/".join(self.image_path.split("/")[:-2])
        self.pilimage = Image.open(self.image_path)
        self.photo = ImageTk.PhotoImage(self.pilimage)
        self.slice_files, self.time_folders = utils.load_images(self.base_path)

        #Just get these from the slice/time folders
            #For time index, check the index from the time folder

        self.time_index = self.time_folders.index(f"time{self.current_time:03d}")
        self.slice_index = self.slice_files[self.time_index].index(f"slice{self.current_slice:03d}time{self.current_time:03d}.png")
        
        #ORIGINAL SCALE INFORMATION
        self.original_width = self.pilimage.width
        self.original_height = self.pilimage.height
        self.points = []
        self.switchpoints = [] #Surely smarter way to write this
        self.switchdots = []
        self.currentdottags = []

        #Create Canvas
        self.canvas = tk.Canvas(self.root, width=self.pilimage.width, height=self.pilimage.height,borderwidth=0, 
                                highlightbackground=pad_frame.cget("fg_color")[1 if darklight=="dark" else 0],scrollregion=(0, 0, 0, 0))
        
        #Setting a fixed aspect ratio
        self.aspect_ratio = self.original_width/self.original_height
        utils.set_aspect(self.canvas,pad_frame, aspect_ratio=self.aspect_ratio)

        #-------INFORMATION FRAMES-------
        #Mode Info
        self.current_mode = "Draw"
        self.currentmodedialog = ctk.CTkFrame(master=self.root)
        self.currentmodedialog.grid(row=1, column=0, padx=10, pady=(10,10), sticky="nsw")
        self.currentmodedialog.grid_rowconfigure(0, weight=1)
        self.modelabel = ctk.CTkLabel(master=self.currentmodedialog, 
                                        text=f"{self.current_mode} Mode",
                                        font=(self.font,self.fontsize),
                                        justify="center")
        self.modelabel.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")   

        #Save image button
        self.btn = ctk.CTkButton(master=self.root, text="Save Mask", command=self.save_mask, font=(self.font, self.fontsize), height=40)
        self.btn.grid(row=1, column=1, padx=5, pady=(10,10), sticky="ns")

        #Slice/Time info
        self.info = ctk.CTkFrame(master=self.root,fg_color="transparent", border_width=0)
        self.info.grid(row=1, column=2, padx=5, pady=(10,10),sticky="nse")
        self.info.grid_columnconfigure(0, weight=1)
        self.info.grid_rowconfigure(0, weight=1)

        #Info box for current slice/time
        self.fileinfo = ctk.CTkFrame(master=self.info, fg_color=self.currentmodedialog.cget('fg_color'))
        self.fileinfo.grid(row=0, column=0, padx=10, pady=0,sticky="nse")
        self.fileinfo.grid_rowconfigure(0, weight=1)
        self.filelabel = ctk.CTkLabel(master=self.fileinfo 
                                      ,text=f"Time:{self.current_time:02d}/{len(self.time_folders)}, Slice:{self.current_slice:02d}/{len(self.slice_files[0])}"
                                      ,font=(self.font,self.fontsize-3,'bold'),anchor="center")
        self.filelabel.grid(row=0, column=0, padx=5, pady=6, sticky="nsew")

        #Info box for file movements
        self.moveinfo = ctk.CTkFrame(master=self.info,fg_color=self.currentmodedialog.cget('fg_color'))
        self.moveinfo.grid(row=0, column=1, padx=(0,5), pady=0,sticky="ns")
        self.moveinfo.grid_rowconfigure(0, weight=1)
        self.alabel = ctk.CTkLabel(master=self.moveinfo, text=f"A\nPrev. Slice", font=(self.font, self.fontsize-7), anchor='center', justify='center')
        self.alabel.grid(row=0,column=0, padx=5, pady=(0,5), sticky="nsew")
        self.dlabel = ctk.CTkLabel(master=self.moveinfo, text=f"D\nNext Slice", font=(self.font, self.fontsize-7), anchor='center', justify='center')
        self.dlabel.grid(row=0,column=1, padx=5, pady=(0,5), sticky="nsew")
        
        #Display image on canvas
        self.canvimg=self.canvas.create_image(0,0,image=self.photo, anchor=tk.NW, tags="image") #tagged to easily access from the canvas items

        #------BINDINGS-------
        # Bind canvas resize event
        self.canvas.bind("<Configure>", self.on_resize)

        #Binding mouse actions
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Button-3>", self.handle_right_click)
        self.canvas.configure(cursor="circle")
        self.window.bind("<C>", self.switchplacecavity)
        self.window.bind("<c>", self.switchplacecavity)

        if self.debug == True:
            self.window.bind("<a>", self.on_key_press)
            self.window.bind("<d>", self.on_key_press)
            self.window.bind("<A>", self.on_key_press)
            self.window.bind("<D>", self.on_key_press)
        self.focus_set()

        #-------CONTEXT MENU-------
        self.context_menu = tk.Menu(master=self.root, tearoff=0)
        self.context_menu.add_command(label="Select Time", command=self.selecttime)
        self.context_menu.add_command(label="Delete Polygon", command=self.delete_polygon)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Dot Settings", command=self.dot_settings)
        self.context_menu.add_command(label="Line Settings", command=self.line_settings)
        self.context_menu.add_command(label="Redraw/Save Settings", command = self.redrawsave_settings)
        self.context_menu.add_command(label="Polygon Color", command=self.polygon_colorset)
        self.context_menu.add_separator()
        # self.context_menu.add_command(label="Auto-Segment(WIP)", command=self.autosegment)
        self.context_menu.add_command(label="Toggle Edit/Draw Mode", command=self.toggle_mode)
        self.context_menu.add_command(label="Refresh Current Edit Segmentation",command=self.edit_mode)
        self.context_menu.add_command(label="Bring Previous", command = self.previous_poly)

        #-------CURRENT SCALE INFORMATION-------
        self.current_width = self.canvas.winfo_width()
        self.current_height = self.canvas.winfo_height()
        self.scaledpoints = []
        self.scaledcavity = []

        #-------VARIABLES-------
        self.scale_factor = 1.0

        self.last_width = self.original_width
        self.last_height = self.original_height
        self.item_scale_factor = self.scale_factor

        self.event_data = {"item": None, "x": 0, "y": 0, "type": None}
        self.drag_threshold = 1 #Threshold in pixels to determine if the movement is large enough
        self.is_dragging = False

        self.dot_size = 6
        self.line_width = 3

        self.smoothing = 100
        self.numpoints = 50
        
        self.dots = []
        self.lines = []
        self.polygon = None
        self.drawptbtwline = True

        #-------COLORS------- 
        self.dotcolor = "#E2856E"
        self.dothovercolor = "#55DDE0"
        self.linecolor = "#001C55"
        self.linehovercolor = "#55DDE0"
        self.polygoncolor = None
        
        self.load_settings()

        if self.polygoncolor == None:
            self.polygoncolor = (0,0,255,int(0.1*255))

    def selecttime(self):
        def submit_action():
            try:
                val = int(input_entry.get())
                if val >= 1 and val<=len(self.time_folders):
                    self.time_index = int(input_entry.get())-1
                    self.current_time = val
                    timewindow.destroy()
                    if self.debug == False:
                        self.window.image_path = os.path.join(self.base_path, f"time{val:03d}", f"slice{self.current_slice:3d}.png")
                        self.window.time_index = self.time_index
                        self.window.current_time = val
                        self.window.slice_files, self.window.time_folders = utils.load_images(self.base_path)
                        self.window.load_image(slice_index = self.current_slice-1, time_index = self.time_index)
                        self.update()
                elif val<1 or val>len(self.time_folders):         
                    CTkMessagebox(master=self.window, message="Please Enter a Valid Time from the Range", icon="warning")
            except ValueError:
                CTkMessagebox(master=self.window, message="Please Enter a Valid Time from the Range", icon="warning")

        timewindow = ctk.CTkToplevel(self.root)
        timewindow.resizable(False, False)
        timewindow.grab_set()
        label = ctk.CTkLabel(timewindow, text=f"Please Select a Time from 1-{len(self.time_folders)}:"
                             ,font=(self.font, self.fontsize-5))
        label.grid(row=0, column=0, pady=5, padx=10)

        # Create an entry widget for text input
        input_entry = ctk.CTkEntry(timewindow, width=200, font=(self.font, self.fontsize-5))
        input_entry.grid(row=1, column=0, pady=5, padx=5)
        # Create a button that triggers the submit_action function
        submit_button = ctk.CTkButton(timewindow, text="Submit", 
                                      command=submit_action, font=(self.font, self.fontsize-5))
        submit_button.grid(row=2, column=0, pady=5, padx=5)
        return

    def update(self):
        self.destroy()
        self.window.segmentor = PolygonDrawer(self.window, row=0, column=0)

    def on_resize(self,event):
         #Implemented from https://www.tutorialspoint.com/how-to-set-the-canvas-size-properly-in-tkinter
        #Initializing new width and height        

        scale_x = self.canvas.winfo_width() / self.original_width
        scale_y = self.canvas.winfo_height() / self.original_height

        self.current_width = self.canvas.winfo_width()
        self.current_height = self.canvas.winfo_height()
        
        # Choose the smaller scale factor to maintain aspect ratio
        self.scale_factor = min(scale_x, scale_y)
        # print("scale_factor: ", self.scale_factor)

        # Calculate new width and height while maintaining aspect ratio
        new_width = int(self.original_width * self.scale_factor)
        new_height = int(self.original_height * self.scale_factor)

        #Debugging step - for whatever reason it initializes at 0
        if new_height == 0:
            new_height = 1

        # print("new_width: ", new_width)
        # print("new_height: ", new_height)

        #Scaling image and photo
        scaled_image = self.pilimage.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.scaled_photo = ImageTk.PhotoImage(scaled_image)

        #Update canvas and the image size
        self.canvas.configure(width=new_width,height = new_height)
        self.canvas.itemconfig(self.canvimg, image=self.scaled_photo)

        #Item scaling information
        self.item_scale_factor = new_width / self.last_width
        self.last_width = new_width

        # Scale the dots, lines, and polygons based on the original positions and new scale factor
        items = self.canvas.find_all()
        for item in items:
            self.canvas.scale(item, 0,0, self.item_scale_factor, self.item_scale_factor)
        
        self.scalepoints()
        self.redraw_polygon()

        self.root.grid_rowconfigure(0,minsize=self.root.winfo_height()*(9/10))
        self.root.grid_rowconfigure(1,minsize=self.root.winfo_height()*(1/10))

    def on_mouse_down(self,event):
        self.event_data["x"]= event.x
        self.event_data["y"] = event.y
        #This information is collected from the current scale

        clicked_items = self.canvas.find_withtag("current") #Represents the top-most item directly under the mouse
        # print(clicked_items)

        if clicked_items and "dot" in self.canvas.gettags(clicked_items[0]):
            self.event_data["item"] = clicked_items[0]
            self.event_data["type"] = "dot"
            self.is_dragging = False #Initialize with false, before checking
        elif clicked_items and "line" in self.canvas.gettags(clicked_items[0]):
            self.event_data["item"] = clicked_items[0]
            self.event_data["type"] = "line"
            self.is_dragging = False
            self.drawptbtwline = True
        elif clicked_items and "polygon" in self.canvas.gettags(clicked_items[0]):     
            return
        else:
            self.event_data["item"]=None
    
    def on_mouse_up(self, event):
        if not self.is_dragging and self.event_data["item"] is None:
            self.add_point(event)
        elif not self.is_dragging and self.event_data["type"] == "line" and self.drawptbtwline:
            #Gets triggered because its no longer dragging and has just clicked a line
            self.pointbtwline(event, self.event_data["item"]) #Add point to line 
    
    def do_drag(self,event):
        """This function checks what item is being dragged and performs the action     
        """
        if self.event_data["item"]:
            dx = event.x - self.event_data["x"]
            dy = event.y - self.event_data["y"]

            #Check the drag threshold, then start dragging
            if abs(dx)>self.drag_threshold or abs(dy)>self.drag_threshold:
                self.is_dragging = True
                if self.event_data["type"] == "dot":
                    try:
                        index = self.dots.index(self.event_data["item"])
                    except ValueError:
                        return #Item was not found
                    self.canvas.move(self.event_data["item"], dx, dy)
                    # print(f"point moved {dx},{dy}")

                    #Update the new point coordinates
                    old_x, old_y = self.scaledpoints[index]
                    new_x, new_y = old_x + dx, old_y + dy

                    ogold_x, ogold_y = self.points[index]
                    self.points[index] = (ogold_x + dx/self.scale_factor, ogold_y + dy/self.scale_factor)
                    self.scaledpoints[index] = (self.points[index][0]*self.scale_factor,self.points[index][1]*self.scale_factor)

                    self.event_data["x"] = event.x
                    self.event_data["y"] = event.y
                    if self.current_mode == "Draw":
                        self.redraw_polygon() 
                    else:
                        self.redraw_polygon("switched")
                    #Cannot redraw all the points, as stops the dragging motion
                elif self.event_data["type"] == "line":
                    #Move all dots together then just redraw everything
                    for item in self.canvas.find_all()[1:]:
                            self.canvas.move(item, dx,dy)

                    self.event_data["x"] = event.x
                    self.event_data["y"] = event.y

                    #Updating all the point locations
                    for i in range(0,len(self.dots)):
                        # self.canvas.move(self.dots[i], dx, dy)
                        old_x, old_y = self.scaledpoints[i]
                        ogold_x, ogold_y = self.points[i]
                        self.points[i] = (ogold_x + dx/self.scale_factor, ogold_y + dy/self.scale_factor) 
                        self.scaledpoints[i] = (self.points[i][0]*self.scale_factor,self.points[i][1]*self.scale_factor)

                        # ogold_x, ogold_y = self.points[i]
                        # self.points[i] = (ogold_x + dx/self.scale_factor, ogold_y + dy/self.scale_factor)
                    self.drawptbtwline = False                     
            else:
                self.is_dragging = False
        return 

    def handle_right_click(self,event):
        clicked_items = self.canvas.find_withtag("current")

        if clicked_items and "dot" in self.canvas.gettags(clicked_items[0]):
                self.delete_point(event, clicked_items[0])
        else:
            self.show_context_menu(event)

    def on_key_press(self,event):
        self.updateswitchpoints()
        # print(f"Key pressed: {event.keysym}")  # Debugging line

        if event.keysym == "a" or event.keysym =="A":
            self.slice_index = (self.slice_index - 1) % len(self.slice_files[self.time_index])
            # print("A Clicked")
        if event.keysym == "d" or event.keysym =="D":
            self.slice_index = (self.slice_index + 1) % len(self.slice_files[self.time_index])
            # print("D Clicked")

        # self.delete_polygon()
        self.checkswitchpoints()
        self.updateimage(self.slice_index, self.time_index)

    def switchplacecavity(self,event):
        clicked_items = self.canvas.find_withtag("current")
        if clicked_items and "dot" in self.canvas.gettags(clicked_items[0]):
            if "cavity" in self.canvas.gettags(clicked_items[0]):
                self.canvas.itemconfig(clicked_items[0], tags=("dot","myocardium"))         
                #Have to remove it from the scaledcavitypoints, then 
            elif "myocardium" in self.canvas.gettags(clicked_items[0]):
                self.canvas.itemconfig(clicked_items[0], tags=("dot","cavity"))
        elif clicked_items == False:
            return
        self.currentdottags = [self.canvas.gettags(dot) for dot in self.dots]
        self.redraw_polygon()
    
    def addcavitybtwline(self, event):
        clicked_items = self.canvas.find_withtag("current")
        if clicked_items and "line" in self.canvas.gettags(clicked_items[0]):
            self.pointbtwline(event,clicked_items[0], type="cavity")
        self.currentdottags = [self.canvas.gettags(dot) for dot in self.dots]
        self.redraw_polygon()

    def updateimage(self, slice_index, time_index):
        time_folder = self.time_folders[time_index]
        slice_file = self.slice_files[time_index][slice_index]
        image_path = os.path.join(self.base_path, time_folder, slice_file)

        # Convert to the correct format for the operating system
        image_path = image_path.replace('\\', '/')
        try:
            self.pilimage = Image.open(image_path) # Resize the image for display
            self.photo = ImageTk.PhotoImage(self.pilimage)
        except OSError:
            CTkMessagebox(message=f"Image f{image_path} not loaded, likely OneDrive Issue.",icon="cancel")
            
        # Calculate new width and height while maintaining aspect ratio
        new_width = int(self.original_width * self.scale_factor)
        new_height = int(self.original_height * self.scale_factor)

        #Updating canvas with the current scaled image
        scaled_image = self.pilimage.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.scaled_photo = ImageTk.PhotoImage(scaled_image)
        #Update canvas and the image size
        self.canvas.itemconfig(self.canvimg, image=self.scaled_photo)

        #Update label
        self.current_slice = int(os.path.basename(image_path)[5:8])
        self.current_time = int(os.path.basename(image_path)[12:15])
        self.filelabel.configure(text=f"Time:{self.current_time:02d}/{len(self.time_folders)}, Slice:{self.current_slice:02d}/{len(self.slice_files[0])}")    
            
        self.edit_mode()

    def updateswitchpoints(self):
        exists = any(entry[0] == self.slice_index for entry in self.switchpoints)
        #If the current slice exists in the switchpoints, redraw it only if in draw
        if self.current_mode == "Draw":
            if self.points != []:
                if exists:
                    index = [i for i, entry in enumerate(self.switchpoints) if entry[0] == self.slice_index][0]                
                    self.switchpoints[index][1] = self.points
                    self.switchdots[index][1] = [self.canvas.gettags(dot) for dot in self.dots]
                    # print(f"updating switch points for {self.slice_index}")
                else:
                    # print(f"adding switch points for {self.slice_index}: {self.points}")
                    self.switchpoints.append([self.slice_index, self.points])
                    self.switchdots.append([self.slice_index,[self.canvas.gettags(dot) for dot in self.dots]])
                self.points = []
                self.currentdottags = []
                # self.cavitypoints = []
                self.scalepoints()
                self.redraw_polygon()
                self.redraw_points()
            else:
                return

    def checkswitchpoints(self):
        slicepointsexists = any(entry[0] == self.slice_index for entry in self.switchpoints)
        if slicepointsexists and self.switchpoints != []:
            index = [i for i, entry in enumerate(self.switchpoints) if entry[0] == self.slice_index][0]
            # print(self.switchpoints)
            self.points = self.switchpoints[index][1]
            self.currentdottags = self.switchdots[index][1]
            #Have to pass the dot tags as well, that way can just check what the tags are and redraw
            self.scalepoints()
            self.redraw_polygon("switched")
            self.redraw_points("switched")

    #----------POINT ACTIONS----------
    def draw_point(self,x,y, type="myocardium"):
        dot_size = self.dot_size * self.scale_factor
        fill = self.dotcolor if type == "myocardium" else utils.hextocomp(self.dotcolor)
        dot = self.canvas.create_oval(x-dot_size, y-dot_size, x+dot_size, y+dot_size, fill=fill, tags=("dot",type))

        # Bind hover events to the dot
        self.canvas.tag_bind(dot, "<Enter>", lambda e, d=dot: self.on_hover_enter(e, d))
        self.canvas.tag_bind(dot, "<Leave>", lambda e, d=dot: self.on_hover_leave(e, d))

        # Bind drag events to the dot
        self.canvas.tag_bind(dot, "<ButtonPress-1>", self.on_mouse_down)
        self.canvas.tag_bind(dot, "<B1-Motion>", self.do_drag)
        self.canvas.tag_bind(dot, "<ButtonRelease-1>", self.on_mouse_up)

        return dot
    
    def scalepoints(self):
        self.scaledpoints = [(a * self.scale_factor, b * self.scale_factor) for a, b in self.points] #Scale all the original points to match the current scale

    def add_point(self,event,type="myocardium"):
        x,y = event.x, event.y #Collect coords of event based on the current scale
        # if type == "myocardium":
        self.points.append((x/self.scale_factor, y/self.scale_factor)) #Coords of events based on the original scale
        self.scalepoints()        

        dot=self.draw_point(x,y,type=type)
        self.dots.append(dot) #Collecting the dot tags
        self.currentdottags.append(("dot","myocardium") if type=="myocardium" else ("dot",))
        self.redraw_points()#Elevate all the points to the top
        self.redraw_polygon()

    def pointbtwline(self, event, line, type="myocardium"):
        # Get the exact coordinates where the user clicked
        new_x, new_y = event.x, event.y
        # Get the coordinates of the line
        coords = self.canvas.coords(line)
        x1, y1, x2, y2 = coords
        
        # Find the index of the line in the list of lines
        line_index = self.lines.index(line)
        
        # print(f"{line_index}/{len(self.lines)}")
        start_point_index = line_index
        end_point_index = (line_index + 1) % len(self.points)
        if end_point_index == 0:
            end_point_index = len(self.points)

               
        self.scaledpoints.insert(end_point_index, (new_x, new_y))
        self.points.insert(end_point_index, (new_x/self.scale_factor,new_y/self.scale_factor))
        pointtags = [self.currentdottags[end_point_index-1],self.currentdottags[end_point_index] ]
        # Remove the old line since it will be replaced by two new lines
        self.canvas.delete(line)
        self.lines.pop(line_index)

        if type=="myocardium":
            linetags = ("line","myocardium")
            linefill = self.linecolor
        elif type=="cavity":
            linetags = ("line","cavity")
            linefill = utils.hextocomp(self.linecolor)
        
        # Create two new lines: one from the first point to the new dot, and another from the new dot to the second point
        line1 = self.canvas.create_line(x1, y1, new_x, new_y, fill=linefill, tags=linetags, width=self.line_width*self.scale_factor)
        line2 = self.canvas.create_line(new_x, new_y, x2, y2, fill=linefill, tags=linetags, width=self.line_width*self.scale_factor)
        
        # Insert the new lines into the lines list at the correct positions
        self.lines.insert(line_index, line1)
        self.lines.insert(line_index + 1, line2)
        
        # Bind hover events to the new lines
        self.canvas.tag_bind(line1, "<Enter>", lambda e, l=line1: self.on_line_hover_enter(e, l))
        self.canvas.tag_bind(line1, "<Leave>", lambda e, l=line1: self.on_line_hover_leave(e, l))
        self.canvas.tag_bind(line2, "<Enter>", lambda e, l=line2: self.on_line_hover_enter(e, l))
        self.canvas.tag_bind(line2, "<Leave>", lambda e, l=line2: self.on_line_hover_leave(e, l))
        
        # Draw the new dot at the clicked position
        if all("cavity" in tag for tag in pointtags):
            type = "cavity"
        dot = self.draw_point(new_x, new_y,type=type)
        self.dots.insert(end_point_index, dot)
        self.currentdottags.insert(end_point_index, self.canvas.gettags(dot))
        # Ensure that dots are always on top
        for dot in self.dots:
            self.canvas.tag_raise(dot)

    def redraw_points(self,mode=""):
        # Clear existing dots
        for dot in self.dots:
            self.canvas.delete(dot)
        self.dots.clear()
        # self.currentdottags.clear()

        # Draw the dots based on the scaled points list
        for i in range(len(self.scaledpoints)):
            tags = self.currentdottags[i]
            x,y = self.scaledpoints[i]
            if "cavity" in tags:
                dot=self.draw_point(x,y,"cavity")
            else:
                dot=self.draw_point(x,y)
            self.dots.append(dot)
        # Ensure that dots are always on top
        for dot in self.dots:
            self.canvas.tag_raise(dot)

    def delete_point(self, event, dot):
        if dot in self.dots:
            index = self.dots.index(dot)
            point_to_delete = self.scaledpoints[index]

            self.canvas.delete(dot)
            self.dots.pop(index)
            self.currentdottags.pop(index)
            self.points.pop(index)
            self.scaledpoints.pop(index)

            # Delete lines connected to the point
            lines_to_remove = []
            for line in self.lines:
                coords = self.canvas.coords(line)
                try:
                    if (coords[:2] == [point_to_delete[0], point_to_delete[1]] or 
                    coords[2:] == [point_to_delete[0], point_to_delete[1]]):
                        lines_to_remove.append(line)
                except TypeError:
                    self.redraw_polygon()

            for line in lines_to_remove:
                self.canvas.delete(line)
                self.lines.remove(line)

            self.redraw_polygon()

    class sliders:
        def __init__(self,parent,window,varstring, text,startend,framepos):
            """Variables:
            window - the window the slider will be found in
            variable - the variable to update
            text - the text to be displayed
            startend - (start, end) values
            framepos - row value
            """
            self.parent = parent
            self.Frame = ctk.CTkFrame(window,corner_radius=10)
            self.Frame.grid(row=framepos, column=0, padx=5, pady=5,sticky="ew")
            self.variable = getattr(self.parent, varstring)
            # Function to handle slider value change
            def on_slider_change(value):
                label.configure(text=f"{text} {int(value):n}")
                slider_value = slider.get()
                setattr(self.parent, varstring, int(slider_value))
                self.parent.redraw_polygon()
                self.parent.redraw_points()

            # Create a slider
            slider = ctk.CTkSlider(self.Frame, from_=startend[0], to=startend[1], command=on_slider_change,number_of_steps=startend[1]-startend[0])
            slider.set(self.variable)
            slider.grid(row=1,column=0,padx=5,pady=0)

            # Label to display slider value
            label = ctk.CTkLabel(self.Frame, text=f"{text}{self.variable:n}")
            label.grid(row=0,column=0,padx=5,pady=0)


    def dot_settings(self):
        """Expected settings to change for dots:
        Size
        Color
        """
        dotWindow = ctk.CTkToplevel(self.root)
        dotWindow.title("Dot Settings")
        dotWindow.resizable(False, False)
        dotWindow.grid_columnconfigure(0, weight=1)
        dotWindow.grid_rowconfigure(2, weight=1)
        dotWindow.grab_set()

        def assign(e):
            self.dotcolor = e
            comp = utils.hextocomp(e[1:])
            self.dothovercolor = comp
            self.redraw_points()
               
        self.sliders(self,dotWindow, "dot_size", "Dot Size: ", (1,20), 0)
        colorpicker = CTkColorPicker(dotWindow, command = lambda e: assign(e), orientation="horizontal",corner_radius=10)
        colorpicker.grid(row=1,column=0,padx=5,pady=(0,5))
        
    def redrawsave_settings(self):
        "Just has to have a slider to display the number of points to redraw"
        redrawWindow = ctk.CTkToplevel(self.root)
        redrawWindow.title("Redraw Settings")
        redrawWindow.resizable(False, False)
        redrawWindow.grid_columnconfigure(0, weight=1)
        redrawWindow.grid_rowconfigure(2, weight=1)
        
        redrawWindow.grab_set()

        self.sliders(self,redrawWindow, "numpoints", "Number of Redraw Points: ", (40,100), 0)
        self.sliders(self,redrawWindow, "smoothing", "Smoothing Value: ", (20,200),1)
    
    def line_settings(self):
        """Expected settings to change for line:
        Size(Width)
        Color
        """
        lineWindow = ctk.CTkToplevel(self.root)
        lineWindow.title("Dot Settings")
        lineWindow.resizable(False, False)
        lineWindow.grid_columnconfigure(0, weight=1)
        lineWindow.grid_rowconfigure(2, weight=1)
        lineWindow.grab_set()
        # lineWindow.after(100, lineWindow.lift) # Workaround for bug where main window takes focus

        def assign(e):
            self.linecolor = e
            comp = utils.hextocomp(e[1:])
            self.linehovercolor = comp
            self.redraw_polygon()
               
        self.sliders(self,lineWindow, "line_width", "Line Width: ", (1,20), 0)
        colorpicker = CTkColorPicker(lineWindow, command = lambda e: assign(e), orientation="horizontal",corner_radius=10)
        colorpicker.grid(row=1,column=0,padx=5,pady=(0,5))

    #----------POLYGON ACTIONS----------
    def show_context_menu(self, event):
        clicked_items = self.canvas.find_withtag("current")
        if not clicked_items or ("dot" not in self.canvas.gettags(clicked_items[0]) and 
                                 "line" not in self.canvas.gettags(clicked_items[0])):
            self.context_menu.post(event.x_root, event.y_root)

    def redraw_polygon(self,mode=""):
        """This connects all dots present and draws the polygon contained within"""
        #Clear existing lines and polygons
        for line in self.lines:
            self.canvas.delete(line)
        self.lines.clear()

        if self.polygon:
            self.canvas.delete(self.polygon)
        self.polygon = None

        # Draw lines between points
        if len(self.scaledpoints) > 1:
            #Drawing the polygon
            if len(self.scaledpoints) > 2:
                self.polygon = utils.PILdrawpoly(self.currentdottags, self.scaledpoints, [self.current_width, self.current_height], self.polygoncolor)
                poly = self.canvas.create_image(0, 0, image=self.polygon, anchor=tk.NW)
                lowest_item_id = self.canvas.find_all()[1]
                self.canvas.tag_lower(poly, lowest_item_id)

            #Draw the lines
            for i in range(len(self.scaledpoints) - 1):
                try:
                    if "cavity" in self.currentdottags[i] and "cavity" in self.currentdottags[i+1]:
                        line = self.canvas.create_line(self.scaledpoints[i], self.scaledpoints[i+1], fill=utils.hextocomp(self.linecolor), tags=("line","cavity"), width = self.line_width*self.scale_factor)
                    else:
                        line = self.canvas.create_line(self.scaledpoints[i], self.scaledpoints[i+1], fill=self.linecolor, tags="line", width = self.line_width*self.scale_factor)               
                except IndexError:
                    print(f"Dottags Length:{len(self.currentdottags)}")
                    print(f"Index attempted:{[i,i+1]}")
                    print(f"{self.currentdottags[i+1]}")
                self.lines.append(line)
                # Bind hover events to the line
                self.canvas.tag_bind(line, "<Enter>", lambda e,l=line: self.on_line_hover_enter(e,l))
                self.canvas.tag_bind(line, "<Leave>", lambda e,l=line: self.on_line_hover_leave(e,l))   
        if len(self.points) > 2 and self.points[0] != self.points[-1]:
            if "cavity" in self.currentdottags[-1] and "cavity" in self.currentdottags[0]:
                line = self.canvas.create_line(self.scaledpoints[-1], self.scaledpoints[0], fill=utils.hextocomp(self.linecolor), tags=("line","cavity"), width = self.line_width*self.scale_factor)
            else:
                line = self.canvas.create_line(self.scaledpoints[-1], self.scaledpoints[0], fill=self.linecolor, tags="line", width = self.line_width*self.scale_factor)               
            self.lines.append(line)
            self.canvas.tag_bind(line, "<Enter>", lambda e,l=line: self.on_line_hover_enter(e,l))
            self.canvas.tag_bind(line, "<Leave>", lambda e,l=line: self.on_line_hover_leave(e,l))
        for dot in self.dots:
            self.canvas.tag_raise(dot)

    def delete_polygon(self):
        for line in self.canvas.find_withtag("line"):
            self.canvas.delete(line)
        if self.polygon:
            self.canvas.delete(self.polygon)    
        for dot in self.canvas.find_withtag("dot"):
            self.canvas.delete(dot)
       
        self.points.clear()
        self.currentdottags.clear()
        self.dots.clear()
        self.lines.clear()
        self.polygon = None

    def polygon_colorset(self):
        def rgba_to_hex(rgba):
            r, g, b, a = rgba

            # Ensure that each component is within the valid range (0-255)
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            a = max(0, min(255, a))

            # Convert each component to a two-digit hexadecimal value
            return "#{:02X}{:02X}{:02X}{:02X}".format(r, g, b, a)
        
        pick_color = ctkpa.AskColor(initial_color=rgba_to_hex(self.polygoncolor))
        color = pick_color.get()[1:] #THIS IS IN HEX
        self.polygoncolor = tuple(int(color[i:i+2], 16) for i in (0, 2, 4, 6))
        self.redraw_polygon()

    def load_settings(self):
        settings_mapping = {
        'dotcolor': ('dotcolor', str),
        'dothovercolor': ('dothovercolor', str),
        'linecolor': ('linecolor', str),
        'linehovercolor': ('linehovercolor', str),
        'polygoncolor': ('polygoncolor', ast.literal_eval),
        'dotsize': ('dot_size', int),
        'linewidth': ('line_width', int),
        'smoothing': ('smoothing', int),
        'numpoints': ('numpoints', int),
        }

        if os.path.exists('save.txt'):
            with open("save.txt", 'r') as file:
                for line in file:
                    line = line.strip()
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        self.settings[key.strip()] = value.strip()

            # Loop through the mapping to assign settings dynamically
            for key, (attr, converter) in settings_mapping.items():
                value = self.settings.get(key)
                if value is not None:
                    try:
                        setattr(self, attr, converter(value))
                    except Exception:
                        if key == 'polygoncolor':
                            self.polygoncolor = None
        else:
            with open('save.txt', 'w') as file:
                pass
        
    def update_or_write_paths(self,key, value,file_path='save.txt'):
        # Step 1: Read the file
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
        except FileNotFoundError:
            lines = []  # If file doesn't exist, start with an empty list

        # Step 2: Check if the key exists and update it
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(key):  # Check if the key exists
                lines[i] = f"{key}{value}\n"  # Update the value
                updated = True
                break

        # Step 3: If the key doesn't exist, add it (ensure a newline at the end)
        if not updated:
            lines.append(f"{key}{value}\n")

        # Step 4: Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.writelines(lines)

    def save_settings(self,delete="keep"):
        settings = {
        "points=": self.points,
        "dotcolor=": self.dotcolor,
        "dothovercolor=": self.dothovercolor,
        "linecolor=": self.linecolor,
        "linehovercolor=": self.linehovercolor,
        "polygoncolor=": self.polygoncolor,
        "dotsize=": int(self.dot_size),
        "linewidth=": int(self.line_width),
        "smoothing=": int(self.smoothing),
        "numpoints=": int(self.numpoints)
        }
            # Update or write all settings in the file
        for key, value in settings.items():
            self.update_or_write_paths(key, str(value))

        if delete == "delete":
            self.window.destroy()   

    # def autosegment(self):
    #     from torch import device, cuda, load, unsqueeze, from_numpy, tensor,argmax,unique
    #     import UNET
    #     model = UNET.UNET(in_channels = 1, out_channels = 3, features = [128,256,512,1024])
    #     device = device('cuda') if cuda.is_available() else "cpu"
    #     model = model.to(device)
    #     model.load_state_dict(load(f'./bestcheckpoint.pth', map_location=device))
    #     mask = model(tensor(np.array(self.pilimage)).unsqueeze(0).unsqueeze(0).float())
    #     mask = argmax(mask.squeeze(),dim=0).squeeze()
    #     mask[mask==1]=127
    #     mask[mask==2]=255
    #     print(unique(mask))
    #     img = Image.fromarray(mask.numpy().astype(np.uint8))
    #     img.save('mask.png')
    #     self.pilimage.save('image.png')
    #     del device, cuda, load, unsqueeze, from_numpy, tensor
    #     del UNET

    def toggle_mode(self):
        if self.current_mode == "Draw":
            self.current_mode = "Edit"
            self.modelabel.configure(text=f"{self.current_mode} Mode",font=('TkDefaultFont',self.fontsize))
            self.btn.configure(text="Save Edited Mask")
            self.edit_mode()
        else:
            self.current_mode = "Draw"
            self.modelabel.configure(text=f"{self.current_mode} Mode",font=('TkDefaultFont',self.fontsize))           
            self.btn.configure(text="Save New Mask")
            self.points = []
            self.scaledpoints = []
            self.currentdottags = []
            self.redraw_points()
        return
    
    def edit_mode(self):
        if self.current_mode == "Edit":
            folder = self.base_path + "/"+self.image_path.split("/")[-2] + "/segmented" 
            segmentedslice = folder + f"/Segmented Slice{self.current_slice:03d}.png"
            if os.path.exists(folder):
                if os.path.exists(segmentedslice):
                    self.points, self.scaledpoints, self.currentdottags = utils.masktopoints(self.numpoints, self.scale_factor, segmentedslice)
                    self.redraw_points("switched")
                    self.redraw_polygon("switched")     
                else:
                    CTkMessagebox(message=f"Slice{self.current_slice:03d} at time{self.current_time:03d} does not have segmentations",icon="cancel")
                    self.toggle_mode()
            else:
                CTkMessagebox(message=f"This folder at time{self.current_time:03d} does not have segmentations",icon="cancel")
                self.toggle_mode()
        else:
            return
        #User has to be able to move to the next time and slice and maintain the previous information
    def previous_poly(self):
        #Check if the previous slice(so long as its slice2) has a segmentation
        if self.current_slice >= 2:
            folder = self.base_path + "/"+self.image_path.split("/")[-2] + "/segmented" 
            segmentedslice = folder + f"/Segmented Slice{self.current_slice-1:03d}.png"
            if os.path.exists(folder):
                if os.path.exists(segmentedslice):
                    self.points, self.scaledpoints, self.currentdottags = utils.masktopoints(self.numpoints, self.scale_factor, segmentedslice)
                    self.redraw_polygon("switched")     
                    self.redraw_points("switched")
        else:
            CTkMessagebox(message="There is no previous slice!", icon="warning")

    def save_mask(self):
            if self.points == []:
                CTkMessagebox(master=self.window,message="Please Draw Points before Saving Mask", icon="warning")
            else:
                mask = Image.new('L', self.pilimage.size, 0)
                draw = ImageDraw.Draw(mask)
                # print(self.points)
                cavity = False
                
                # Generate smooth points along the curve
                u_new = np.linspace(0, 1, self.smoothing)
                #If cavity is present in the tag, get the index and then take it from self.scaledpoints
                cavidx = [index for index, tup in enumerate(self.currentdottags) if "cavity" in tup]
                if len(cavidx) >2:
                    cavitypoints = [self.points[i] for i in cavidx]
                    cavitypointsnp = np.array(cavitypoints)
                    unsmoothed_points = cavitypointsnp[[0,-1]]
                    middle_points = cavitypointsnp[1:-1]

                    # Perform smoothing on the middle points
                    tck, u = splprep(middle_points.T, s=0)
                    smoothed_middle_points = np.array(splev(np.linspace(0, 1, self.smoothing), tck)).T

                    # Combine unsmoothed and smoothed points, ensuring the two unsmoothed points stay connected by a straight line
                    all_points = np.vstack([unsmoothed_points[0], smoothed_middle_points, unsmoothed_points[1]])

                    # Close the polygon by adding the first unsmoothed point at the end
                    all_points_closed = np.vstack([all_points, unsmoothed_points[0]])
                    smoothcav_coords = [tuple(point) for point in all_points_closed]

                    def get_centroid(points):
                        x_coords = [p[0] for p in points]
                        y_coords = [p[1] for p in points]
                        return (sum(x_coords) / len(points), sum(y_coords) / len(points))

                    # Function to calculate the distance between two points
                    def distance(point1, point2):
                        return np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

                    # Function to expand a polygon by a fixed number of pixels
                    def expand_polygon(points, pixel_expansion):
                        centroid = get_centroid(points)
                        
                        # Create a new set of vertices, each one moved outward by the given number of pixels
                        new_points = []
                        for point in points:
                            # Calculate the vector from the centroid to the point
                            vector = (point[0] - centroid[0], point[1] - centroid[1])
                            
                            # Normalize the vector
                            vector_length = distance(centroid, point)
                            if vector_length != 0:
                                unit_vector = (vector[0] / vector_length, vector[1] / vector_length)
                            else:
                                unit_vector = (0, 0)
                            
                            # Expand the point by the fixed number of pixels along the direction of the unit vector
                            new_point = (
                                point[0] + unit_vector[0] * pixel_expansion, 
                                point[1] + unit_vector[1] * pixel_expansion
                            )
                            new_points.append(new_point)
                        
                        return new_points
                    
                    smoothcav_coords = expand_polygon(smoothcav_coords, 2)
                    cavity = True
                else:
                    CTkMessagebox(master=self.window, message="Too few Cavity points selected, please add more",icon="warning")

                #Drawing myocardium
                pointsnp = np.array(self.points)
                tck,u = splprep(pointsnp.T, s=0)
                smoothedmyopoints = np.array(splev(u_new, tck)).T
                smoothmyocoords = [tuple(point) for point in smoothedmyopoints]

                # Create two separate masks for the two polygons
                myo_mask = Image.new("L", self.pilimage.size, 0)
                cav_mask = Image.new("L", self.pilimage.size, 0)
                
                # Draw the polygons on their respective masks
                myo_draw = ImageDraw.Draw(myo_mask)
                cav_draw = ImageDraw.Draw(cav_mask)
                
                myo_draw.polygon(smoothmyocoords, fill=255)
                cav_draw.polygon(smoothcav_coords, fill=127)

                # Combine the masks and handle overlap
                image_size = self.pilimage.size
                for x in range(image_size[0]):
                    for y in range(image_size[1]):
                        myo_value = myo_mask.getpixel((x, y))
                        cav_value = cav_mask.getpixel((x, y))
                        
                        if cav_value == 127 and myo_value == 255:
                            # Overlap detected, set to 127
                            draw.point((x, y), fill=255)
                        elif cav_value == 127:
                            # Non-overlapping cavity region
                            draw.point((x, y), fill=127)
                        elif myo_value == 255:
                            # Non-overlapping myo region
                            draw.point((x, y), fill=255)

                # mask.show()  # Display the visualization image
                
                if self.debug == True:
                    impath = "mask.png"
                    mask.save(impath)
                    CTkMessagebox(title="New Mask Save",message = f"Mask saved to {impath}", icon='check')

                if self.current_mode == "Draw" and self.debug==False:
                    folder_path = os.path.dirname(self.image_path) + "/segmented"
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)  # Creates folder and intermediate directories if they don't exist
                    impath = folder_path + "/Segmented Slice" + f"{self.current_slice:03d}" + ".png"
                    mask.save(impath)
                    CTkMessagebox(title="New Mask Save",message = f"Mask saved to {impath}", icon='check')
                elif self.current_mode == "Edit" and self.debug == False:
                    folder = os.path.dirname(self.image_path) + "/segmented"
                    segmentedslice = folder + f"/Segmented Slice{self.current_slice:03d}.png"

                    mask.save(segmentedslice)
                    CTkMessagebox(title="Edited Mask Save",message = f"Edited Mask saved to {segmentedslice}", icon='check')

    #----------HOVER EVENTS----------
    def on_hover_enter(self, event, dot):
        if "myocardium" in self.canvas.gettags(dot):
            self.canvas.itemconfig(dot, fill=self.dothovercolor)
        elif "cavity" in self.canvas.gettags(dot):
            self.canvas.itemconfig(dot, fill=utils.hextocomp(self.dothovercolor))
    
    def on_hover_leave(self, event, dot):
        if "myocardium" in self.canvas.gettags(dot):
            self.canvas.itemconfig(dot, fill=self.dotcolor)
        elif "cavity" in self.canvas.gettags(dot):
            self.canvas.itemconfig(dot, fill=utils.hextocomp(self.dotcolor))
    
    def on_line_hover_enter(self, event, line):
        if "cavity" in self.canvas.gettags(line):
            self.canvas.itemconfig(line, fill=utils.hextocomp(utils.hextocomp(self.linehovercolor)))
        else:
            self.canvas.itemconfig(line, fill=utils.hextocomp(self.linecolor))      

    def on_line_hover_leave(self, event, line):
        if "cavity" in self.canvas.gettags(line):
            self.canvas.itemconfig(line, fill=utils.hextocomp(self.linecolor))
        else:
            self.canvas.itemconfig(line, fill=self.linecolor)        

if __name__ == "__main__":
       root=ctk.CTk()
       root.title("Polygon Drawer")
       app = PolygonDrawer(root, debug=True)
       root.mainloop()