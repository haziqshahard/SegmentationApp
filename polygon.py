import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog

class PolygonDrawer:
    def __init__(self, root):
        self.root = root
        self.root.title("Polygon Drawer")
        
        # Load image
        self.image_path = filedialog.askopenfilename(title="Select an Image")
        self.image = Image.open(self.image_path)
        self.photo = ImageTk.PhotoImage(self.image)
        
        # Create Canvas
        self.canvas = tk.Canvas(root, width=self.image.width, height=self.image.height)
        self.canvas.pack()
        
        # Display image on canvas
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        
        # Initialize variables
        self.points = []  # List to store points
        self.dots = []    # List to store dot objects
        self.lines = []   # List to store line objects
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Delete Polygon", command=self.delete_polygon)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.add_or_select_point)  # Left click to add or select a point
        self.canvas.bind("<Button-3>", self.handle_right_click)    # Right click to delete or show context menu

    def add_or_select_point(self, event):
        clicked_items = self.canvas.find_withtag("current")
        dot_size = 6

        if clicked_items and "dot" in self.canvas.gettags(clicked_items[0]):
            closest_dot = clicked_items[0]
            index = self.dots.index(closest_dot)
            selected_point = self.points[index]
            
            # Connect the selected dot to the last placed dot
            if len(self.points) > 0:
                line = self.canvas.create_line(self.points[-1], selected_point, fill="blue", tags="line")
                self.lines.append(line)
        elif clicked_items and "line" in self.canvas.gettags(clicked_items[0]):
            # If clicked on a line, place a new dot on that line
            line = clicked_items[0]
            coords = self.canvas.coords(line)
            x1, y1, x2, y2 = coords
            new_point = (event.x, event.y)
            
            # Calculate the distance from the new point to each end of the line
            dist1 = ((new_point[0] - x1)**2 + (new_point[1] - y1)**2)**0.5
            dist2 = ((new_point[0] - x2)**2 + (new_point[1] - y2)**2)**0.5
            
            # Determine the order of insertion
            if dist1 < dist2:
                index = self.points.index((x1, y1)) + 1
            else:
                index = self.points.index((x2, y2))
            
            # Insert the new point into the points list and redraw the lines
            self.points.insert(index, new_point)
            self.redraw_polygon()
        else:
            # If no dot or line is selected, add a new dot
            x, y = event.x, event.y
            self.points.append((x, y))
            
            # Draw the point
            dot = self.canvas.create_oval(x-dot_size, y-dot_size, x+dot_size, y+dot_size, fill="red", tags="dot")
            self.dots.append(dot)
            
            # Bind hover events
            self.canvas.tag_bind(dot, "<Enter>", lambda e, d=dot: self.on_hover_enter(e, d))
            self.canvas.tag_bind(dot, "<Leave>", lambda e, d=dot: self.on_hover_leave(e, d))
            
            # Connect points if there are more than one
            if len(self.points) > 1:
                line = self.canvas.create_line(self.points[-2], self.points[-1], fill="blue", tags="line")
                self.lines.append(line)
            
            # If it's a closed polygon, fill it
            self.check_and_fill_polygon()
    
    def on_hover_enter(self, event, dot):
        self.canvas.itemconfig(dot, fill="yellow")
    
    def on_hover_leave(self, event, dot):
        self.canvas.itemconfig(dot, fill="red")
    
    def handle_right_click(self, event):
        clicked_items = self.canvas.find_withtag("current")
        
        if clicked_items and "dot" in self.canvas.gettags(clicked_items[0]):
            self.delete_point(event, clicked_items[0])
        else:
            self.show_context_menu(event)
    
    def delete_point(self, event, dot):
        index = self.dots.index(dot)
        point_to_delete = self.points[index]
        
        self.canvas.delete(dot)
        self.dots.pop(index)
        self.points.pop(index)
        
        lines_to_remove = []
        for line in self.lines:
            coords = self.canvas.coords(line)
            if (coords[:2] == [point_to_delete[0], point_to_delete[1]] or 
                coords[2:] == [point_to_delete[0], point_to_delete[1]]):
                lines_to_remove.append(line)
        
        for line in lines_to_remove:
            self.canvas.delete(line)
            self.lines.remove(line)
        
        self.redraw_polygon()
    
    def show_context_menu(self, event):
        clicked_items = self.canvas.find_withtag("current")
        if not clicked_items or ("dot" not in self.canvas.gettags(clicked_items[0]) and 
                                 "line" not in self.canvas.gettags(clicked_items[0])):
            self.context_menu.post(event.x_root, event.y_root)
    
    def delete_polygon(self):
        for dot in self.dots:
            self.canvas.delete(dot)
        for line in self.lines:
            self.canvas.delete(line)
        self.points.clear()
        self.dots.clear()
        self.lines.clear()
    
    def redraw_polygon(self):
        for line in self.lines:
            self.canvas.delete(line)
        self.lines.clear()
        if len(self.points) > 1:
            for i in range(len(self.points) - 1):
                line = self.canvas.create_line(self.points[i], self.points[i+1], fill="blue", tags="line")
                self.lines.append(line)
        self.check_and_fill_polygon()
    
    def check_and_fill_polygon(self):
        if len(self.points) > 2 and self.points[0] == self.points[-1]:
            self.canvas.create_polygon(self.points, fill="lightblue", outline="blue", tags="polygon")
    
if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonDrawer(root)
    root.mainloop()
