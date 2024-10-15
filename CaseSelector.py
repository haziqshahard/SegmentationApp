import tkinter as tk
import customtkinter as ctk
import os
from CTkMessagebox import CTkMessagebox
import ast
import webbrowser
import utils
import shutil
import re
import threading
class CaseSelector(ctk.CTkFrame):
    """Window that enables the user to select cases by opening the folders
    Window then saves the file path and displays it.
    Goes into save.txt with all the case files so that when it is next opened, can just be clicked and it will appear

    #Needs to have a check to see if the selected folder is valid and has the required folders/files within, if not, reject the folder
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
        self.base_path = tk.filedialog.askdirectory(title="Select the Case")
        if any(self.base_path in sublist for sublist in self.paths):
            CTkMessagebox(message="This Case is already present", icon="cancel")
        else:
            if os.path.exists(self.base_path):
                self.paths += [[str(self.base_path),"notcompleted"]]
                self.createbutton(self.base_path)
                self.renderbuttons()
                self.savecases()
            else:
                self.selectcase()
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
        valid_extensions = (".png", ".jpg", ".jpeg")
        dataset_dir = os.path.join(dir, "dataset")

        # Ensure the dataset directory exists
        os.makedirs(dataset_dir, exist_ok=True)

        for case in self.paths:
            if case[1] == "completed":
                casename = case[0]
                dataset_case_dir = os.path.join(dataset_dir, os.path.basename(casename))

                # Create necessary folders (mask and image)
                os.makedirs(os.path.join(dataset_case_dir, "mask"), exist_ok=True)
                os.makedirs(os.path.join(dataset_case_dir, "image"), exist_ok=True)

                # Load images and time folders (assuming utils.load_images() is available)
                img_files, time_folders = utils.load_images(casename)

                # Total time folders for this case
                total_time_folders = len(time_folders)

                # Process mask and image files for each time folder
                for idx, time_folder in enumerate(time_folders):
                    time_folder_path = os.path.join(casename, time_folder)
                    segmented_path = os.path.join(time_folder_path, "segmented")

                    if not os.path.exists(segmented_path):
                        self.update_progress(f"Segmented path does not exist: {segmented_path}", idx, total_time_folders)
                        continue

                    mask_paths = [os.path.join(segmented_path, f) for f in os.listdir(segmented_path) if os.path.isfile(os.path.join(segmented_path, f))]

                    current_time_folder = os.path.join(dataset_case_dir, "mask", os.path.basename(time_folder_path))
                    os.makedirs(current_time_folder, exist_ok=True)

                    for mask_path in mask_paths:
                        try:
                            shutil.copyfile(mask_path, os.path.join(current_time_folder, os.path.basename(mask_path)))
                        except Exception as e:
                            self.update_progress(f"Failed to copy mask {mask_path}: {e}", idx, total_time_folders)

                    # Process image files (Results -> Images)
                    case_image = casename.replace("Results", "Images")
                    if not os.path.exists(case_image):
                        self.update_progress(f"Image folder does not exist: {case_image}", idx, total_time_folders)
                        continue
                    
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

                    # Update progress after each time folder is processed
                    progress = (idx + 1) / total_time_folders
                    self.update_progress(f"Processed {os.path.join(os.path.basename(casename), time_folder)}", progress)

        self.update_progress("Transfer completed!", 1)

    def update_progress(self, message, progress):
        # Update the label with the progress message
        self.progress_label.configure(text=message)
        # Update the progress bar (progress is a value between 0 and 1)
        self.progress_bar.set(progress)
        self.transfer_window.update()  # Force the window to update its content

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
        case = os.path.join(components[-2], components[-1])
        btn = ctk.CTkButton(master=self.scrollframe, height=30, text=f"{case}", 
                            font=(self.font,self.fontsize),anchor="w")
        btn.bind("<Button-1>", command=lambda event, path=path: self.loadcase(event, path = path))
        btn.bind("<Button-3>", command=lambda event, path=path: self.handle_right_click(event, path = path))

        self.buttons.append(btn)
    
    def handle_right_click(self, event, path):
        pathidx = self.find_index(self.paths,path)
        # Create a context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Delete Case", command=lambda: self.delete_button(pathidx))
        context_menu.add_command(label="Mark Completed",command = lambda: self.switchcompleted(pathidx))
        context_menu.add_command(label="Open Folder",command = lambda: os.startfile(path))

        context_menu.tk_popup(event.x_root, event.y_root)

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
        elif self.debug == True:
            print(self.paths[pathidx][0])
        self.selectedbutton = button
        
if __name__ == "__main__":
    root=ctk.CTk()
    app = CaseSelector(root, debug=True)
    root.mainloop()
