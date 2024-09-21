import tkinter as tk
import customtkinter as ctk
import os
from CTkMessagebox import CTkMessagebox
import ast
import webbrowser
class CaseSelector(ctk.CTkFrame):
    """Window that enables the user to select cases by opening the folders
    Window then saves the file path and displays it.
    Goes into save.txt with all the case files so that when it is next opened, can just be clicked and it will appear
    """
    def __init__(self, window, debug=False, row=1, column=0, theme="blue"):
        super().__init__(window)
        self.debug = debug
        self.window = window

        if debug==True:
            self.window.title("Case Selector")
            self.window.protocol("WM_DELETE_WINDOW", self.savecases)
            self.window.columnconfigure(0, weight=1)
            self.window.rowconfigure(0, weight=1)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme(theme)

        self.root = ctk.CTkFrame(master=self.window)
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
                                                  ,label_font=(self.font,self.fontsize*self.scale_factor))
        self.scrollframe.grid(row=0, column=0,sticky="nsew")

        self.buttons = []

        btn = ctk.CTkButton(master=self.root,text="Select Case", command=self.selectcase, font=(self.font,self.fontsize*self.scale_factor))

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
        btn.grid(row=1, column=0, padx=10, pady=10, sticky="se")

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
                # print(self.paths)
                self.createbutton(self.base_path)
                self.renderbuttons()
            else:
                self.selectcase()
        return
    
    def savecases(self):
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
        #CAN DEPRECATE THIS AS DOING IT IN THE SUPER 
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
        case = os.path.basename(os.path.normpath(path))

        # pathidx = self.find_index(self.paths,path)
        # print(self.paths)
        # print(pathidx)    
        # pathidx = self.paths.index(path)
        btn = ctk.CTkButton(master=self.scrollframe, height=30, text=f"{case}", 
                            font=(self.font,self.fontsize),anchor="w")
        btn.bind("<Button-1>", command=lambda event, path=path: self.loadcase(event, path = path))
        btn.bind("<Button-3>", command=lambda event, path=path: self.handle_right_click(event, path = path))

        self.buttons.append(btn)
    
    def handle_right_click(self, event, path):
        pathidx = self.find_index(self.paths,path)
        # Create a context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        # Add 'Delete Case' option to the context menu
        context_menu.add_command(label="Delete Case", command=lambda: self.delete_button(pathidx))
        context_menu.add_command(label="Mark Completed",command = lambda: self.switchcompleted(pathidx))
        # Show the menu at the position of the right-click
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
            image_path = os.path.join(self.window.master.base_path, "time001", 'slice001time001.png')
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
