import tkinter as tk
import customtkinter as ctk
import os
from CTkMessagebox import CTkMessagebox
import ast

class CaseSelector(ctk.CTkFrame):
    """Window that enables the user to select cases by opening the folders
    Window then saves the file path and displays it.
    Goes into save.txt with all the case files so that when it is next opened, can just be clicked and it will appear
    """
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.root.title("Case Selector")
        self.root.protocol("WM_DELETE_WINDOW", self.savecases)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # Other themes: "blue", "green"
        self.fontsize = 15
        self.font = 'Helvetica'
        self.settings = {}
        self.paths = []

        self.root.grid_columnconfigure(0,weight=1)
        self.root.grid_rowconfigure(0,weight=1)
        self.root.geometry("675x300")

        mainframe = ctk.CTkFrame(master = self.root, width=675, height=300)
        self.original_width = self.root.winfo_width()
        self.original_height = self.root.winfo_height()
        self.scale_factor = 1
        mainframe.grid_rowconfigure(0,weight=1)
        mainframe.grid_columnconfigure(0,weight=1)
        mainframe.grid(row=0, column=0,padx=10, pady=10, sticky="nsew")

        self.scrollframe = ctk.CTkScrollableFrame(master=mainframe, label_text="Case Selector", label_anchor="w", label_font=(self.font,self.fontsize*self.scale_factor))
        self.scrollframe.grid(row=0, column=0,sticky="nsew")

        self.preloadcases()

        btn = ctk.CTkButton(master=mainframe,text="Select Case", command=self.selectcase, font=(self.font,self.fontsize*self.scale_factor))
        btn.grid(row=1, column=0, padx=10, pady=10, sticky="e")

    def selectcase(self):
        self.base_path = tk.filedialog.askdirectory(title="Select the Case")
        if self.base_path in self.paths:
            CTkMessagebox(message="This Case is already present", icon="cancel")
        else:
            self.paths += [str(self.base_path)]
            self.createbutton(self.base_path)
        return
    
    def savecases(self):
        with open('save.txt', "r") as f:
            lines = f.readlines()
            # Step 2: Check if 'paths' exists and update it
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("paths="):
                lines[i] = f"paths={self.paths}\n"  # Update the 'paths' value
                updated = True
                break

        # Step 3: If 'paths' doesn't exist, add it
        if not updated:
            lines.append(f"paths={self.paths}\n")

        # Step 4: Write the updated content back to the file
        with open('save.txt', 'w') as file:
            file.writelines(lines)
        self.root.destroy()  
    
    def preloadcases(self):
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
                self.createbutton(path)
        return

    def createbutton(self, path):
        case = os.path.basename(os.path.normpath(path))
        btn = ctk.CTkButton(master=self.scrollframe, text=f"{case}", command=self.loadcase(),font=(self.font,self.fontsize*self.scale_factor),anchor="center")
        btn.pack(padx=5,pady=5, fill=tk.BOTH, expand=True)
        btn.bind("<Button-3>", self.handle_right_click)

    def handle_right_click(self, event):
        #Pull up context menu to be able to delete the case

        print("button pressed")
        return

    def loadcase(self):
        return


if __name__ == "__main__":
    root=ctk.CTk()
    app = CaseSelector(root)
    root.mainloop()
