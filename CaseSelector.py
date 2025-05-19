import tkinter as tk
import customtkinter as ctk
import os
from CTkMessagebox import CTkMessagebox
import ast
import webbrowser
import utils
import shutil
import threading
from PIL import Image
import numpy as np
import cv2
import platform
class CaseSelector(ctk.CTkFrame):
    """Window that enables the user to select cases by opening the folders
    Window then saves the file path and displays it.
    Goes into save.txt with all the case files so that when it is next opened, can just be clicked and it will appear

    #Needs to have a check to see if the selected folder is valid and has the required folders/files within, if not, reject the folder
    #Make a "Create Results Folder" button
    #Make a "Generate Check Folder" button with the overlay for the segmented times
    """
    def __init__(self, window, debug=False, row=1, column=0, theme="blue",darklight="dark"):
        super().__init__(window)
        self.debug = debug
        self.window = window

        if debug==True:
            self.window.title("Case Selector")
            self.window.protocol("WM_DELETE_WINDOW", self.savecases)
            self.window.columnconfigure(0, weight=1)
            self.window.rowconfigure(0, weight=1)
        
        ctk.set_appearance_mode(darklight)
        ctk.set_default_color_theme(theme)

        self.root = ctk.CTkFrame(master=self.window,fg_color="transparent")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.grid(row=0, column=0, padx=5, pady=5)

        if debug==False:
            # self.root.configure(height=300)
            self.root.grid(row=row, column=column, columnspan=1,  sticky="nsew")
        else:
            self.root.grid(row=0, column=0, sticky="nsew")

        self.original_width = 50
        self.original_height = 50
        self.scale_factor = 1
        
        self.fontsize = 15
        self.font = 'Helvetica'
        self.settings = {}
        self.paths = []

        self.scrollframe = ctk.CTkScrollableFrame(master=self.root, label_text="Case Selector", label_anchor="w"
                                                  ,label_font=(self.font,self.fontsize*self.scale_factor),corner_radius=7)
        self.scrollframe.grid(row=0, column=0,padx=5,pady=5,sticky="nsew")

        self.buttons = []

        btndialog = ctk.CTkFrame(master=self.root)
        btndialog.grid(row=1, column=0, sticky="se", padx = 5)
        btn = ctk.CTkButton(master=btndialog,text="Select Case", command=self.selectcase, font=(self.font,self.fontsize*self.scale_factor))
        btn2 = ctk.CTkButton(master=btndialog,text="Create Dataset", command=self.open_transfer_window, font=(self.font,self.fontsize*self.scale_factor))

        def open_url(url):
            webbrowser.open_new(url)
        link = ctk.CTkLabel(self.root, 
                            text="By: Haziq Shahard", 
                            text_color="#696969", 
                            cursor="hand2", font=("Helvetica", 14) 
                            )
        # Bind the label to the open_url function
        link.bind("<Button-1>", lambda e: open_url("https://github.com/haziqshahard/SegmentationApp"))
        link.grid(row=1, column=0, padx=10, pady=10, sticky="sw")
        def on_enter(event):
            link.configure(text_color="#878787")  # Change text color on hover
        def on_leave(event):
            link.configure(text_color="#696969")  # Reset text color when not hovering
        
        link.bind("<Enter>", on_enter)
        link.bind("<Leave>", on_leave)
        
        self.fg_color = getattr(btn, "_fg_color")
        self.hover_color = getattr(btn, "_hover_color")
        self.originalborder = btn.cget("border_color")  
        btn.grid(row=0, column=1, padx=10, pady=10, sticky="se")
        btn2.grid(row=0, column=0, padx=10, pady=10, sticky="se")

        self.selectedbutton = None

        if self.paths == [] and self.debug == False:
            self.paths = [self.window.master.base_path]
        elif self.paths == [] and self.debug == True:
            pass

        self.preloadcases()

        if debug == False:
            idx = self.find_index(self.paths,self.window.master.base_path)
            self.selectedbutton = self.buttons[idx]
            self.selectedbutton.configure(border_color = "white", border_width=2)
            #Whatever the app's base path is, check the 

    def selectcase(self):
        base_path = tk.filedialog.askdirectory(title="Select the Case")
        if any(base_path in sublist for sublist in self.paths):
            CTkMessagebox(message="This Case is already present", icon="cancel")
        else:
            check1, check2 = utils.load_images(base_path)
            if os.path.exists(base_path) and (len(check1)!=0 and len(check2) != 0):
                self.base_path = base_path
                self.paths += [[str(base_path),"notcompleted"]]
                self.createbutton(base_path)
                self.renderbuttons()
                self.savecases()
            elif base_path == "":
                return
            else:
                CTkMessagebox(message="This file path is not valid.", icon="cancel")
                return
        
    
    def open_transfer_window(self):
        msg = CTkMessagebox(master=self.window, title="Create Dataset", message=f"Do you want to create a dataset from all the completed cases?",
                        icon="warning", option_1="Cancel", option_3="Yes")
        response = msg.get()

        if response == "Yes":
            # Open a new window to show the transfer progress
            self.transfer_window = ctk.CTkToplevel(self)
            self.transfer_window.title("File Transfer Progress")
            self.transfer_window.geometry("400x200")

            # Add a label to display progress updates
            self.progress_label = ctk.CTkLabel(self.transfer_window, text="Starting transfer...")
            self.progress_label.pack(pady=10)

            # Add a progress bar for file transfer
            self.progress_bar = ctk.CTkProgressBar(self.transfer_window)
            self.progress_bar.pack(pady=20)
            self.progress_bar.set(0)  # Initialize progress bar to 0

            # Run the file transfer in a separate thread
            transfer_thread = threading.Thread(target=self.create_dataset)
            transfer_thread.start()
        else:
            return

    def create_dataset(self):
        dir = tk.filedialog.askdirectory(title="Select the Folder to Create the dataset within")
        dataset_dir = os.path.join(dir, "dataset")
        # Ensure the dataset directory exists
        os.makedirs(dataset_dir, exist_ok=True)

        for case in self.paths:
            if case[1] == "completed" and "/Results/" in case[0]:
                dataset_case_dir = os.path.join(dataset_dir, os.path.basename(case[0]))

                # Create necessary folders (mask and image)
                os.makedirs(os.path.join(dataset_case_dir, "mask"), exist_ok=True)
                os.makedirs(os.path.join(dataset_case_dir, "image"), exist_ok=True)

                _, time_folders = utils.load_images(case[0])
                
                self.process_mask__image(time_folders = time_folders, casename = case[0], dataset_case_dir=dataset_case_dir) #Transfers all the images and masks to the dataset folder
                ES,ED = self.determine_ES_ED(time_folders, case[0]) #Determines which of the masks are ES/ED based on the mask area
                self.write_info(dataset_case_dir, case[0], ES, ED) #Writes all the necessary info to the dataset/info.txt file
                self.update_progress(f"Creating check folder in {dataset_case_dir}", 50/100)
                try: 
                    self.create_check(case_path=os.path.join(dataset_case_dir, "mask"), dataset=True) #Creates a check folder with overlaid masks on top of the intensities for only the mask timepoints
                except ValueError:
                    print(ValueError)

        self.update_progress("Transfer completed!", 1)

    def write_info(self, dataset_case_dir, case, ES, ED):
        try:
            #with open(f"{os.path.join(case.replace("Results", "Images"), "scale.txt")}", mode="r") as scaletxt:
            with open(f"{os.path.join(case.replace('Results', 'Images'), 'scale.txt')}", mode='r') as scaletxt:
                # Perform operations with scaletxt
                scale = scaletxt.read()  # Example read operation
        except FileNotFoundError:
            #raise FileNotFoundError(f"The file at path {f"{os.path.join(case.replace("Results", "Images"), "scale.txt")}"} was not found.")
            raise FileNotFoundError(f'The file at path {os.path.join(case.replace("Results", "Images"), "scale.txt")} was not found.')
        
        all_items = os.listdir(case.replace("Results", "Images"))
        nbframe = len([item for item in all_items if item.startswith("time")])

        with open(f"{dataset_case_dir}/info.txt", mode="w") as txt:
            txt.write(f"ES:{ES}\n")
            txt.write(f"ED:{ED}\n")
            txt.write(f"NbFrame:{nbframe}\n")
            #txt.write(f"Spacing: {scale if len(scale) != 0 else "Scale not available"}")
            txt.write(f"Spacing: {scale if len(scale) != 0 else 'Scale not available'}")

    def determine_ES_ED(self, time_folders, casepath):
        mask1path = os.path.join(casepath, time_folders[0], "segmented","Segmented Slice001.png")
        mask2path = os.path.join(casepath, time_folders[1], "segmented","Segmented Slice001.png")
        if os.path.exists(mask1path) and os.path.exists(mask2path):
            time_str = [part for part in mask1path.split(os.sep) if 'time' in part][0]
            # Extract the numeric part of 'time'
            time_value = time_str.replace('time', '')
            mask1time = int(time_value)

            time_str = [part for part in mask2path.split(os.sep) if 'time' in part][0]
            # Extract the numeric part of 'time'
            time_value = time_str.replace('time', '')
            mask2time = int(time_value)

            mask1 = Image.open(mask1path).convert('L')
            mask1 = np.array(mask1)
            mask1[mask1>0] == 1

            mask2 = Image.open(mask2path).convert('L')
            mask2 = np.array(mask2)
            mask2[mask2>0] == 1

            ES, ED = (mask1time, mask2time) if np.sum(mask2) > np.sum(mask1) else (mask2time, mask1time) #ED is larger than ES
        else:
            ES = "Error"
            ED = "Error"

        return ES, ED

    def update_progress(self, message, progress):
        # Update the label with the progress message
        self.progress_label.configure(text=message)
        # Update the progress bar (progress is a value between 0 and 1)
        self.progress_bar.set(progress)
        self.transfer_window.update()  # Force the window to update its content

    def process_mask__image(self, time_folders, casename, dataset_case_dir):
        valid_extensions = (".png", ".jpg", ".jpeg")
        total_time_folders = len(time_folders)
        # Process mask and image files for each time folder
        for idx, time_folder in enumerate(time_folders):
            time_folder_path = os.path.join(casename, time_folder)
            segmented_path = os.path.join(time_folder_path, "segmented")

            if not os.path.exists(segmented_path):
                self.update_progress(f"Segmented path does not exist: {segmented_path}", (idx+1)/ total_time_folders)
                continue

            mask_paths = [os.path.join(segmented_path, f) for f in os.listdir(segmented_path) if os.path.isfile(os.path.join(segmented_path, f))]

            current_time_folder = os.path.join(dataset_case_dir, "mask", os.path.basename(time_folder_path))
            os.makedirs(current_time_folder, exist_ok=True)

            for mask_path in mask_paths:
                try:
                    shutil.copyfile(mask_path, os.path.join(current_time_folder, os.path.basename(mask_path)))
                except Exception as e:
                    self.update_progress(f"Failed to copy mask {mask_path}: {e}", (idx+1)/ total_time_folders)

            # Process image files (Results -> Images)
            case_image = casename.replace("Results", "Images")
            if not os.path.exists(case_image):
                self.update_progress(f"Image folder does not exist: {case_image}", (idx+1)/ total_time_folders)
                break
            
            total = len(os.listdir(case_image))
            for idx, folder_name in enumerate(os.listdir(case_image)):
                prog = (idx+1)/total
                self.update_progress(f"Processing {os.path.join(os.path.basename(casename), folder_name)}...", prog)
                folder_path = os.path.join(case_image, folder_name)

                if os.path.isdir(folder_path) and folder_name.startswith("time") and folder_name[4:].isdigit():
                    dest_time_folder = os.path.join(dataset_case_dir, "image", folder_name)
                    os.makedirs(dest_time_folder, exist_ok=True)

                    image_files = [f for f in os.listdir(folder_path) if f.endswith(valid_extensions)]
                    for file_name in image_files:
                        src_file_path = os.path.join(folder_path, file_name)
                        dest_file_path = os.path.join(dest_time_folder, file_name)

                        try:
                            shutil.copyfile(src_file_path, dest_file_path)
                        except Exception as e:
                            self.update_progress(f"Failed to copy image {file_name}: {e}", idx, total_time_folders)
                    
                    progress = (idx + 1) / total_time_folders
                    self.update_progress(f"Processed {os.path.join(os.path.basename(casename), time_folder)}", progress)

    def savecases(self):
        # print("Saving Cases")
        with open('save.txt', "r") as f:
            lines = f.readlines()
            # Step 2: Check if 'paths' exists and update it
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("paths="):
                lines[i] = f"paths={self.paths}\n" # Update the 'paths' value
                updated = True
                break
        # Step 3: If 'paths' doesn't exist, add it
        if not updated:
            lines.append(f"paths={self.paths}\n")
        # Step 4: Write the updated content back to the file
        with open('save.txt', 'w') as file:
            file.writelines(lines)
        if self.debug == False:
            return
        else:
            self.window.destroy()         
    
    def preloadcases(self):
        if os.path.exists("save.txt"):
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
                for path in self.paths:
                    self.createbutton(path[0])
                self.renderbuttons()
            else:
                if self.debug == False:
                    self.paths = [[self.window.master.base_path,"notcompleted"]]
                    self.createbutton(self.window.master.base_path)
                    self.renderbuttons()
                else:
                    path = tk.filedialog.askdirectory(title="Please select an initial case")
                    self.paths = [[path, "notcompleted"]]
                    self.createbutton(path)
                    self.renderbuttons()

            for i in range(0,len(self.paths)):
                self.markcompleted(i)

        elif self.debug == True and not os.path.exists('save.txt'):
            with open('save.txt', 'w') as file:
                pass
            self.base_path = tk.filedialog.askdirectory(title="Please select an initial case")
    
    def renderbuttons(self):
        for btn in self.buttons:
            btn.pack(padx=5,pady=5, fill=tk.BOTH, expand=True)

    def find_index(self,nested_list, item):
        return [(outer_index, inner_list.index(item)) 
                for outer_index, inner_list in enumerate(nested_list) 
                if item in inner_list][0][0]

    def createbutton(self, path):
        # print(path)
        components = path.split("/")
        case = os.path.join(components[-3], components[-2], components[-1])
        btn = ctk.CTkButton(master=self.scrollframe, height=30, text=f"{case}", 
                            font=(self.font,self.fontsize),anchor="w")
        btn.bind("<Button-1>", command=lambda event, path=path: self.loadcase(event, path = path))
        btn.bind("<Button-2>", command=lambda event, path=path: self.handle_right_click(event, path = path))
        btn.bind("<Button-3>", command=lambda event, path=path: self.handle_right_click(event, path = path))
        self.buttons.append(btn)
    
    def handle_right_click(self, event, path):
        pathidx = self.find_index(self.paths,path)
        # Create a context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Delete Case", command=lambda: self.delete_button(pathidx))
        context_menu.add_command(label="Create Check", command=lambda: self.create_check(pathidx))
        context_menu.add_command(label ="Create Results Folder", command=lambda: self.create_results(pathidx))
        context_menu.add_command(label="Mark Completed",command = lambda: self.switchcompleted(pathidx))
        if platform.system() == "Windows":
            context_menu.add_command(label="Open Folder", command=lambda: os.startfile(path))
        elif platform.system() == "Darwin":  # macOS
            context_menu.add_command(label="Open Folder", command=lambda: os.system(f"open '{path}'"))
        else:  # Linux
            context_menu.add_command(label="Open Folder", command=lambda: os.system(f"xdg-open '{path}'"))

        context_menu.tk_popup(event.x_root, event.y_root)

    def create_check(self, pathidx = 0, case_path = None, dataset=False):
        """
        If case_path is not instantiated, default to the path index
        Else, use the case_path
        Dataset can also be used when making the dataset folders
        """
        #Can only do it for a results folder
        if case_path == None:
            case_path = self.paths[pathidx][0]
        else:
            case_path = case_path
        # print(case_path)
        if "/Results/" in case_path or dataset == True:
            all_items = os.listdir(case_path)
            times = [item for item in all_items if item.startswith("time")]
            check_path = os.path.join(case_path, "check") if dataset == False else os.path.join(os.path.dirname(case_path), "check")
            if not os.path.exists(check_path):
                os.makedirs(check_path) 
            for time in times:
                if not os.path.exists(os.path.join(check_path, time)):
                    os.makedirs(os.path.join(check_path, time)) 
                slices = os.listdir(os.path.join(case_path, time, "segmented")) if dataset == False else os.listdir(os.path.join(case_path, time)) #Mask Slices
                slices = [slice for slice in slices if slice.startswith("Segmented")]
                allintimes = os.listdir(os.path.join(case_path, time)) if dataset == False else os.listdir(os.path.join(os.path.dirname(case_path), "image",time))
                imageslices = [item for item in allintimes if item.startswith("slice")] #Image Slices
                for i in range(len(slices)):
                    maskpath = os.path.join(case_path, time, "segmented", slices[i]) if dataset == False else os.path.join(case_path, time, slices[i])
                    maskoverlay = utils.extract_and_draw_contours(maskpath)
                    image = np.array(Image.open(os.path.join(case_path, time,imageslices[i]))) if dataset == False else np.array(Image.open(os.path.join(os.path.dirname(case_path), "image",time,imageslices[i])))
                    overlaidimg = utils.overlay_images(image, maskoverlay)
                    cv2.imwrite(os.path.join(check_path, time, imageslices[i]), overlaidimg)
        else:
            CTkMessagebox(master=self.window, message="Check folder can only be created for Results", icon="cancel")

    def create_results(self, pathidx):
        case_path = self.paths[pathidx][0]
        all_items = os.listdir(case_path)
        times = [item for item in all_items if item.startswith("time")]
        times_with_segmentation = [time for time in times if os.path.isdir(os.path.join(case_path, time, "segmented"))]
        if "/Images/" in case_path:
            results_path = case_path.replace("Images", "Results")
            if not os.path.exists(results_path):
                os.makedirs(results_path)
            for time in times_with_segmentation:
                image_time_path = os.path.join(case_path, time)
                results_time_path = os.path.join(results_path, time)
                if not os.path.exists(results_time_path):
                    os.makedirs(results_time_path)
                shutil.copytree(image_time_path,results_time_path, dirs_exist_ok= True)
        else:
            CTkMessagebox(master=self.window, message="Incorrect folder path, Please make sure the case is within an \"Images\" folder", icon="cancel")
        self.create_check(case_path = results_path)
        

    def delete_button(self,pathidx):
        # Destroy the button that was right-clicked
        self.paths.pop(pathidx)
        button = self.buttons.pop(pathidx)
        if self.selectedbutton == button:
            self.selectedbutton = None
        button.destroy()
        self.renderbuttons()
        self.scrollframe.update_idletasks()
        if len(self.buttons) == 1:
            self.loadcase("",self.paths[0][0])

        if self.debug == False:
            if len(self.paths) == 0:
                self.selectcase()
        
        self.savecases()

    def switchcompleted(self, pathidx):
        button = self.buttons[pathidx]
        # fg_color = getattr(button, "_fg_color")
        if self.paths[pathidx][1] == "completed":
            button.configure(fg_color=self.fg_color[1], hover_color = self.hover_color[1])
            self.paths[pathidx][1] = "notcompleted"
        else:
            button.configure(fg_color="green4", hover_color="darkolivegreen4")
            # print(self.paths[pathidx])
            self.paths[pathidx][1] = "completed"
        
        self.savecases()

    def markcompleted(self, pathidx):
        button = self.buttons[pathidx]
        # fg_color = getattr(button, "_fg_color")
        # print(self.paths)
        if self.paths[pathidx][1] == "completed":
            button.configure(fg_color="green4", hover_color="darkolivegreen4")
        else:
            button.configure(fg_color=self.fg_color[1], hover_color = self.hover_color[1])

    def loadcase(self, event, path):
        # print(self.buttons)
        pathidx = self.find_index(self.paths,path)
        button = self.buttons[pathidx]
        #Check if any other buttons have been selected
        #If any other buttons are selected, set the selected one to normal and 
        # change the clicked button to white 
        button.configure(border_color = "white", border_width=2)
        if self.selectedbutton is not None and button != self.selectedbutton:
            self.selectedbutton.configure(border_color = self.originalborder, border_width=0)
        else:
            button.configure(border_color = "white", border_width=2)
        if self.debug == False: 
            self.window.master.base_path = self.paths[pathidx][0]
            self.window.master.slice_files, self.window.master.time_folders = utils.load_images(self.window.master.base_path)
            self.window.master.current_time = int(self.window.master.slice_files[0][0][12:15])
            image_path = os.path.join(self.window.master.base_path, f"time{self.window.master.current_time:03d}", f'slice001time{self.window.master.current_time:03d}.png')
            self.window.master.image_path = image_path.replace('\\', '/')
            self.window.master.segmentor.update()
            self.window.master.viewhelper.update()
            self.window.master.maskviewer.update()
            self.window.master.threedviewer.update()
        elif self.debug == True:
            print(self.paths[pathidx][0])
        self.selectedbutton = button
        
if __name__ == "__main__":
    root=ctk.CTk()
    app = CaseSelector(root, debug=True)
    root.mainloop()
