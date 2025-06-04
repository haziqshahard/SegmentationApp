#Only really needs to view the viewhelpers mask, not the segmented one

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import utils
from PIL import ImageFont
import numpy as np
import cv2
import matplotlib.pyplot as plt
import threading
import ast
import re

class ThreeDViewer(ctk.CTkFrame):
    def __init__(self, window, debug=False, row=1, column=1, theme="blue",darklight="dark"):
        super().__init__(window)
        self.debug = debug
        self.window = window
        # self.grid(sticky="nsew")
        ctk.set_appearance_mode(darklight)
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
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Initialize variables
        self.time_index = 0
        self.slice_index = 0
        self.original_width = 10
        self.original_height = 50
        self.aspect_ratio = 1
        self.last_width = self.original_width
        self.scale_factor = 1
        self.current_view = 0
        self.fontsize = 17
        self.font = 'Helvetica'
        self.settings = {}

        # Load base path and images
        if debug==False:
            self.base_path = self.window.master.base_path
        elif debug ==True:
            self.base_path = filedialog.askdirectory(title="Select the base folder")
            """Bind arrow keys to the widget."""

        self.loadimg()
        # print(self.images)

        # Left button
        self.labelfontsize = 15
        padx=4
        pady=0

        self.bind_buttons()
        self.context_menu = tk.Menu(master=self.root, tearoff=0)
        self.context_menu.add_command(label="Reload Image Views", command=self.reload_images)
        self.context_menu.add_command(label="Change Time", command=self.changetime)

    def bind_buttons(self):
        self.leftbutton = ctk.CTkButton(master=self.root, text="◁",
                                        font=("Arial", self.labelfontsize + 10, 'bold'),
                                        command=lambda: self.next_view(-1),
                                        fg_color="gray", width=50, height=40)
        self.leftbutton.place(relx=0.05, rely=0.95, anchor="sw")  # Positioning with relative coordinates

        # Right button
        self.rightbutton = ctk.CTkButton(master=self.root, text="▷",
                                         font=("Arial", self.labelfontsize + 10, 'bold'),
                                         command=lambda: self.next_view(+1),
                                         fg_color="gray", width=50, height=40)
        self.rightbutton.place(relx=0.95, rely=0.95, anchor="se")  # Align right

    def next_view(self, view_idx):
        new_view = self.current_view + view_idx
        if new_view < 0:
            self.current_view = 0
        elif new_view > 2:
            self.current_view = 2
        else:
            self.current_view = new_view
        self.load_screenshot()
        self.update_canvas()

    def changetime(self):
        self.time_index = 1 - self.time_index
        self.loadimg()
        self.bind_buttons()

    def update(self):
        self.destroy()
        self.window.master.threedviewer = ThreeDViewer(self.window, row=0, column=1)

    def loadimg(self):
        # Load the initial image
        self.slice_files, self.time_folders = utils.load_images(self.base_path)

        #Need a check to see if there are 36 slices in the first place
        #If not, 

        #What should happen is, load the images and the masks
            #Calculate centroid and store it
            #Get rid of the stored images because dont need
            #Enable option to manually choose the centroid
        
        #Then load the mplot3d render
        #Enable choosing downscaling factor
        self.load_paths()
        self.load_images_centroid()
        self.load_canvas()  

        self.canvas.bind("<Configure>", self.on_resize)


    def handle_right_click(self,event):
        # print("Right Button Clicked")
        self.context_menu.post(event.x_root, event.y_root)

    def load_slices(self,images):
        def downsample_image(image, factor):
            # Get the current dimensions of the image
            height, width = image.shape[:2]

            # Compute the new dimensions
            new_height = height // factor
            new_width = width // factor
            # Resize the image to the new dimensions
            downsampled_image = cv2.resize(image, (new_width, new_height), cv2.INTER_NEAREST)
            kernel = np.ones((2,2),np.uint8)

            myo_mask = (downsampled_image == 254).astype(np.uint8)
            endo_mask = (downsampled_image == 127).astype(np.uint8)

            dilated_mask = cv2.dilate(myo_mask, kernel, iterations=1)

            eroded_endo = cv2.erode(endo_mask, kernel, iterations=1)
            dilated_mask[eroded_endo == 1] = 0

            dilated_image = downsampled_image.copy()
            dilated_image[dilated_mask==1] = 255

            # Ensure that the values are 0, 127, or 255
            dilated_image = np.clip(dilated_image, 0, 255)  # To make sure we only have valid pixel values

            # # Optional: You can also round values to ensure only 0, 127, or 255 remain
            dilated_image = np.round(dilated_image / 127) * 127  # Normalize and multiply back to preserve levels

            return dilated_image
        
        slices = []
        for image_path in images:
            image = np.array(Image.open(image_path).convert("L"))
            # print(np.unique(image))        
            image = downsample_image(image, 2)
            slices += [image]
        return np.array(slices)

    def find_centroid(self, image_paths):
        # Get indices of non-zero elements
        image_stack = self.load_slices(image_paths)
        # std = np.std(image_stack,axis=0)
        # column_std = np.mean(std, axis=0)  # Shape: (width,)
        # # Find the column index with the minimum standard deviation
        self.centroid = image_stack.shape[2]//2
    
    def load_paths(self):
        time_folder = self.time_folders[self.time_index] #Time folder will change based on what is being viewed
        images = [self.slice_files[self.time_index][i] for i in range(0, 36)]
        self.images = [os.path.join(self.base_path, time_folder, "image" ,img) for img in images]
        self.find_centroid(self.images) #Determine the centroid for the image stack
        self.images = self.images[0] #Saving just the first one for image size purposes

    def reload_images(self):
        self.load_images_centroid(reload=True)

    def load_images_centroid(self, reload=False):

        self.mask_paths = [os.path.join(self.base_path, self.time_folders[self.time_index], "segmented", f"Segmented Slice{slice_index+1:03d}.png") for slice_index in range(0,36)]
        all_exist = all(os.path.exists(path) for path in self.mask_paths)

        path = self.images
        new_path = os.path.join(os.path.dirname(path), "3D Views")  # Remove last two parts
        views_exist = 0
        for i in range(0,3):
            if os.path.exists(f"{new_path}/View_{i}.png"):
                views_exist = 1
            else:
                views_exist=0
                break

        def loading_image():
            image = Image.open(self.images)
            text = f"Loading 3D Views"
            # Create a black image
            width, height = image.size[0], image.size[1] # Set the desired dimensions
            img = Image.new("RGB", (width, height), "black")

            # Create a Draw object
            draw = ImageDraw.Draw(img)
            # Optionally, load a font (default font is used if not specified)
            font = ImageFont.load_default()            # Alternatively, you can specify a font: font = ImageFont.truetype("arial.ttf", font_size)

            # Get the bounding box for the text
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            # Calculate position to center the text
            position = ((width - text_width) // 2, (height - text_height) // 2)
            # Add white text to the image
            draw.text(position, text, fill="white", font=font, align = "center")
            return np.array(img)

        if all_exist and (views_exist == 0 or reload == True): #Then create the screenshots and load them
            self.screenshot_array = [[],[],[]]
            self.screenshot_array[0] = loading_image()
            self.screenshot_array[1] = loading_image()
            self.screenshot_array[2] = loading_image()
            self.masks = self.load_slices(self.mask_paths)
            # Render the 3D view and store it in the buffer, then extract the screenshots for:
            # top down, isometric, front-facing
            #Need to set up a list of views to show - top down, 

            thread = threading.Thread(target=self.process_views)
            thread.start()
            self.load_screenshot()
            pass
        elif all_exist and views_exist == 1:
            self.screenshot_array = [[],[],[]]
            for i in range(0,3):
                self.screenshot_array[i] = np.array(Image.open(f"{new_path}/View_{i}.png"))
            self.load_screenshot()
        else:
            image = Image.open(self.images)
            text = f"This time does not have 36 segmentations"
            # Create a black image
            width, height = image.size[0], image.size[1] # Set the desired dimensions
            img = Image.new("RGB", (width, height), "black")

            # Create a Draw object
            draw = ImageDraw.Draw(img)
            # Optionally, load a font (default font is used if not specified)
            font = ImageFont.load_default()            # Alternatively, you can specify a font: font = ImageFont.truetype("arial.ttf", font_size)

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
            #Render image saying it doesn't exist


    def process_views(self):
        self.figs_list = []
        self.views = [[90,0],[45,45],[0,0]]
        path = self.images
        new_path = os.path.join(os.path.dirname(path), "3D Views")  # Remove last two parts
        if not os.path.exists(new_path):
            os.mkdir(new_path)
        for i in range(0, len(self.views)):
            self.figs_list += [self.plot_cylindrical_stack(self.masks,self.centroid,2,self.views[i][0],self.views[i][1],capture=True)]
            self.screenshot_array[i] = self.capture_screenshot(self.figs_list[i])
            image = Image.fromarray(self.screenshot_array[i])
            image.save(f"{new_path}/View_{i}.png")

    def load_screenshot(self):
        self.img = Image.fromarray(self.screenshot_array[self.current_view])
        self.photo = ImageTk.PhotoImage(self.img)

    def update_canvas(self):
        new_width = int(self.original_width * self.scale_factor)
        new_height = int(self.original_height * self.scale_factor)

        if new_width == 0 :
            new_width = 1
        if new_height == 0:
            new_height = 1 

        scaled_image = self.img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.scaled_photo = ImageTk.PhotoImage(scaled_image)
        #Update canvas and the image size
        self.canvas.itemconfig(self.canvimg, image=self.scaled_photo)

    def plot_cylindrical_stack(self,mask_slices, centroid, downsample_factor=1, elev=30, azim=90, capture=False):
        """
        Create a 3D cylindrical stack plot from a stack of 2D mask slices,
        then optionally capture a screenshot of the rendered figure.
        
        Parameters:
        mask_slices: numpy array of shape (n_slices, height, width)
        centroid: tuple with at least three elements; uses centroid[1] and centroid[2]
        downsample_factor: factor to downsample the coordinates for speed (default=1)
        elev: elevation angle for the 3D view (default=30)
        azim: azimuth angle for the 3D view (default=90)
        capture: if True, capture and return the screenshot as a NumPy array
        
        Returns:
        If capture=True, returns the screenshot image (as a NumPy array). Otherwise, None.
        """
        n_slices, H, W = mask_slices.shape
        
        # Precompute the 2D grid indices (shared by all slices)
        x_indices, y_indices = np.indices((H, W))
        # Calculate offsets relative to the centroid (assumed to be provided as (dummy, x_center, y_center))
        y_offset = y_indices - centroid
        
        # Accumulate data from all slices for one scatter call
        xs_list, ys_list, zs_list, colors_list = [], [], [], []
        cmap = plt.get_cmap('gray')
        
        for n in range(n_slices):
            mask = mask_slices[n]
            theta = n * 5  # Theta in degrees for this slice
            theta_rad = np.radians(theta)
            
            # Transform into cylindrical coordinates:
            # Rotate the y_offset by theta for x and y
            x_trans = y_offset * np.cos(theta_rad)
            y_trans = y_offset * np.sin(theta_rad)
            # Use the x_indices as the z-coordinate (or adjust as needed)
            z_trans = x_indices
            
            # Downsample the data for speed
            x_ds = x_trans[::downsample_factor, ::downsample_factor]
            y_ds = y_trans[::downsample_factor, ::downsample_factor]
            z_ds = z_trans[::downsample_factor, ::downsample_factor]
            mask_ds = mask[::downsample_factor, ::downsample_factor]
            
            # Normalize the mask for color mapping; safeguard against division by zero.
            m_min, m_max = np.min(mask_ds), np.max(mask_ds)
            if m_max - m_min == 0:
                img_norm = np.zeros_like(mask_ds, dtype=float)
            else:
                img_norm = (mask_ds - m_min) / (m_max - m_min)
            
            # Map normalized values to RGBA colors; make black pixels transparent.
            flat_norm = img_norm.flatten()
            colors = cmap(flat_norm)
            colors[flat_norm == 0] = (0, 0, 0, 0)
            
            # Append flattened arrays
            xs_list.append(x_ds.flatten())
            ys_list.append(y_ds.flatten())
            zs_list.append(z_ds.flatten())
            colors_list.append(colors)
        
        # Concatenate arrays from all slices
        xs = np.concatenate(xs_list)
        ys = np.concatenate(ys_list)
        zs = np.concatenate(zs_list)
        all_colors = np.concatenate(colors_list, axis=0)
        
        # Create the 3D plot with a black background.
        fig = plt.figure(figsize=(8, 8))
        fig.patch.set_facecolor('black')
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor("black")
        ax.tick_params(axis='both', colors='black')
        
        # One scatter call for all data points
        ax.scatter(xs, ys, zs, c=all_colors, marker=',', s=10)
        
        # Set the camera view using provided elevation and azimuth angles.
        ax.view_init(elev=elev, azim=azim)
        ax.dist = 10
        ax.set_proj_type('ortho')

        last_nonzero_index = np.max(np.nonzero(img_norm))
        last_non_col = np.max(np.nonzero(img_norm),axis=1)

        lim = last_nonzero_index//2 + 5
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_zlim(0, last_non_col[-1]+10)
        # ax.xaxis._axinfo['grid'].update(color='black')
        # ax.yaxis._axinfo['grid'].update(color='black')
        # ax.zaxis._axinfo['grid'].update(color='black')
        
        plt.axis('off')
        plt.close()

        return fig

    def capture_screenshot(self,fig):
        """
        Render the current figure and return the image as a NumPy array.
        """
        fig.canvas.draw()  # Force a draw so that the canvas is updated
        buf = fig.canvas.tostring_argb()
        ncols, nrows = fig.canvas.get_width_height()
        # Convert the string buffer to a (nrows, ncols, 3) uint8 array
        buf = np.frombuffer(buf, dtype=np.uint8).reshape(nrows, ncols, 4)
        return buf[:,:,1:]

    def set_aspect(self,content_frame, pad_frame, aspect_ratio):
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

    def load_canvas(self):
        self.original_width = self.img.width
        self.original_height = self.img.height
        self.last_width = self.original_width
        self.aspect_ratio - self.original_width/self.original_height


        pad_frame = ctk.CTkFrame(master=self.root, width = 20,height=20,border_width = 0, border_color="blue", fg_color="transparent")
        pad_frame.grid(row=0, column=0, padx=10, pady=10)
        self.canvas = tk.Canvas(self.root, width=self.original_width, height=self.original_height, scrollregion=(0, 0, 0, 0), borderwidth=0, highlightbackground="#000000" )
        self.set_aspect(self.canvas,pad_frame, aspect_ratio=self.aspect_ratio)

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0,weight=1)
        pad_frame.configure(width=self.original_width, height=self.original_height)    
        #Display image
        self.canvimg = self.canvas.create_image(0,0,image=self.photo, anchor=tk.NW, tags="image") #tagged to easily access from the canvas items
        self.canvas.bind("<Button-3>", self.handle_right_click) 

    def update(self):
        self.destroy()
        self.window.master.threedviewer = ThreeDViewer(self.window, row=0, column=1)

    def loadmask(self):
        """
        This function loads available masks, and displays a message ifelse
        """

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
            font = ImageFont.load_default()            # Alternatively, you can specify a font: font = ImageFont.truetype("arial.ttf", font_size)

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
        self.mask_path = os.path.join(self.base_path, self.time_folders[self.time_index], "segmented", f"Segmented Slice{self.slice_index+1:03d}.png")
        # time_folder = self.time_folders[time_index]
        # slice_file = self.slice_files[time_index][slice_index]
        # self.image_path = os.path.join(self.base_path, time_folder, slice_file)
        self.loadmask()
        # Convert to the correct format for the operating system
        # self.image_path = self.image_path.replace('\\', '/')
        # Calculate new width and height while maintaining aspect ratio
        new_width = int(self.original_width * self.scale_factor)
        new_height = int(self.original_height * self.scale_factor)

        if new_width == 0 :
            new_width = 1
        if new_height == 0:
            new_height = 1 

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

        if self.debug == False and (event.keysym == "A" or event.keysym == "a" or event.keysym == "D" or event.keysym == "d"):
            self.time_index = self.time_folders.index(f"time{self.window.master.segmentor.current_time:03d}")
            self.slice_index = self.slice_files[self.time_index].index(f"slice{self.window.master.segmentor.current_slice:03d}time{self.window.master.segmentor.current_time:03d}.png")

        self.updateimage(self.slice_index, self.time_index)
        self.mask_path = os.path.join(self.base_path, self.time_folders[self.time_index], "segmented", f"Segmented Slice{self.slice_index+1:03d}.png")
        # print(self.time_index, self.slice_index)
    
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



if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Mask Viewer")

    imagescroller = ThreeDViewer(root, debug=True)
    root.mainloop()