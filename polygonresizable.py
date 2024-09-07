import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from tkinter import filedialog

class PolygonDrawer:
    """
    #Window that enables the user to draw on the image required
    #Features:
    -Dots can be individually placed, deletable
    -Lines automatically generate between each dot
    -The space fills with a choosable color
    -The whole polygon can be removed
    #Current known bugs:
    -Possibly make the last placed point connect to the nearest point, rather than the point placed before it
    -Resizing of all polygons and objects does not scale correctly, likely due to the anchor point of scaling
        -Rather than scaling the image and storing it, just pull it from the file location each time and resave that after scaling, to avoid loss of info
    #Features to be added
    -Points/Line color/size needs to be adjustable
        .Have to bind right click events directly to the objects?
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Polygon Drawer")
        
        # Load image
        self.image_path = filedialog.askopenfilename(title="Select an Image")
        self.image = Image.open(self.image_path)
        self.photo = ImageTk.PhotoImage(self.image)
        
        # Create Canvas
        self.canvas = tk.Canvas(root, width=self.image.width, height=self.image.height, highlightbackground="blue", highlightthickness=1)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10,pady=10)

        # Display image on canvas
        self.image_item = self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW,tags="image")
        
        # Initialize variables
        self.points = []  # List to store points
        self.dots = []    # List to store dot objects
        self.lines = []   # List to store line objects
        self.polygon = None # Variable to store the polygon
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Delete Polygon", command=self.delete_polygon)
        self.dot_size = 6
        
        # Initialize dragging variables
        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.drag_threshold = 5  # Threshold in pixels to differentiate between click and drag
        self.is_dragging = False
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Button-3>", self.handle_right_click)

        # Bind canvas resize event
        self.canvas.bind("<Configure>", self.on_resize)

        self.dotcolor = "#E2856E"
        self.dothovercolor = "#55DDE0"
        self.linecolor = "#001C55"
        self.linehovercolor = "#55DDE0"

        self.polygoncolor = (0,0,255,int(0.2*255))

        # Track the original size of the canvas
        self.original_width = self.image.width
        self.original_height = self.image.height

        # Track the scale factor
        self.scale_factor = 1.0

    def on_resize(self, event):
        """"MAKE IT SO THAT ASPECT RATIO OF CANVAS DOES NOT CHANGE"""
        # Calculate the new scale factor
        # Calculate the new scale factor based on the original image size and the new canvas size
        scale_x = self.canvas.winfo_width() / self.original_width
        scale_y = self.canvas.winfo_height() / self.original_height

        # Choose the smaller scale factor to maintain aspect ratio
        self.scale_factor = min(scale_x, scale_y)

        # Calculate new width and height while maintaining aspect ratio
        new_width = int(self.original_width * self.scale_factor)
        new_height = int(self.original_height * self.scale_factor)
        scaled_image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.scaled_photo = ImageTk.PhotoImage(scaled_image)

        # Update the canvas image
        self.canvas.itemconfig(self.image_item, image=self.scaled_photo)

        # Scale the dots
        for i, dot in enumerate(self.dots):
            x, y = self.points[i]
            new_x = x * self.scale_factor
            new_y = y * self.scale_factor
            self.canvas.coords(dot, new_x - self.dot_size * self.scale_factor, new_y - self.dot_size * self.scale_factor,
                            new_x + self.dot_size * self.scale_factor, new_y + self.dot_size * self.scale_factor)
        # #Updating dot size
        # self.dot_size = self.scale_factor*self.dot_size

        # Scale the lines
        for i, line in enumerate(self.lines):
            coords = self.canvas.coords(line)
            new_coords = [coord * self.scale_factor for coord in coords]
            self.canvas.coords(line, *new_coords)

        # Recreate the polygon with the scaled points
        if len(self.points) > 2:
            self.scaled_points = [(x * self.scale_factor, y * self.scale_factor) for x, y in self.points]
            self.PILdrawpoly()

        # # Update the scroll region
        # self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mouse_down(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        clicked_items = self.canvas.find_withtag("current")

        if clicked_items and "dot" in self.canvas.gettags(clicked_items[0]):
            self.drag_data["item"] = clicked_items[0]
            self.is_dragging = False
        elif clicked_items and "line" in self.canvas.gettags(clicked_items[0]):
            self.drag_data["item"]=clicked_items[0]
            print("clicking a line")
            self.add_point_to_line(event, clicked_items[0])
        else:
            self.drag_data["item"] = None

    def do_drag(self, event):
        if self.drag_data["item"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]

            # If the mouse has moved beyond the drag threshold, start dragging
            if abs(dx) > self.drag_threshold or abs(dy) > self.drag_threshold:
                self.is_dragging = True
                try:
                    index = self.dots.index(self.drag_data["item"])
                except ValueError:
                    return  # Skip dragging if the item is not found in the list

                self.canvas.move(self.drag_data["item"], dx, dy)
                old_x, old_y = self.points[index]
                new_x, new_y = old_x + dx, old_y + dy
                self.points[index] = (new_x, new_y)

                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y

                self.redraw_polygon() 
            else:
                self.is_dragging = False
        

    def on_mouse_up(self, event):
        if not self.is_dragging and self.drag_data["item"] is None:
            self.add_point(event)
        # self.drag_data["item"] = None

    def draw_point(self, x, y):
        dot = self.canvas.create_oval(x-self.dot_size, y-self.dot_size, x+self.dot_size, y+self.dot_size, fill=self.dotcolor, tags="dot")

        # Bind hover events to the dot
        self.canvas.tag_bind(dot, "<Enter>", lambda e, d=dot: self.on_hover_enter(e, d))
        self.canvas.tag_bind(dot, "<Leave>", lambda e, d=dot: self.on_hover_leave(e, d))

        # Bind drag events to the dot
        self.canvas.tag_bind(dot, "<ButtonPress-1>", self.on_mouse_down)
        self.canvas.tag_bind(dot, "<B1-Motion>", self.do_drag)
        self.canvas.tag_bind(dot, "<ButtonRelease-1>", self.on_mouse_up)

        return dot

    def on_hover_enter(self, event, dot):
        self.canvas.itemconfig(dot, fill=self.dothovercolor)
    
    def on_hover_leave(self, event, dot):
        self.canvas.itemconfig(dot, fill=self.dotcolor)

    def on_line_hover_enter(self, event, line):
        self.canvas.itemconfig(line, fill=self.linehovercolor)

    def on_line_hover_leave(self, event, line):
        self.canvas.itemconfig(line, fill=self.linecolor)

    def handle_right_click(self, event):
        clicked_items = self.canvas.find_withtag("current")

        if clicked_items and "dot" in self.canvas.gettags(clicked_items[0]):
                self.delete_point(event, clicked_items[0])
        else:
            self.show_context_menu(event)
    
    def add_point(self, event):
        x, y = event.x, event.y
        self.points.append((x, y))
        dot_size = 6

        # Draw the lines before the dots
        self.redraw_polygon()

        # Draw the point
        dot = self.draw_point(x,y)
        self.dots.append(dot)
        print(len(self.dots))
        self.redraw_points()

    def add_point_to_line(self, event, line):
        # Get the exact coordinates where the user clicked
        new_x, new_y = event.x, event.y
        
        # Get the coordinates of the line
        coords = self.canvas.coords(line)
        x1, y1, x2, y2 = coords
        
        # Find the index of the line in the list of lines
        line_index = self.lines.index(line)
        
        # Insert the new point into the points list at the correct position
        # The new point should be inserted right after the starting point of the line
        start_point_index = line_index
        end_point_index = (line_index + 1) % len(self.points)
        
        self.points.insert(end_point_index, (new_x, new_y))
        
        # Remove the old line since it will be replaced by two new lines
        self.canvas.delete(line)
        self.lines.pop(line_index)
        
        # Create two new lines: one from the first point to the new dot, and another from the new dot to the second point
        line1 = self.canvas.create_line(x1, y1, new_x, new_y, fill=self.linecolor, tags="line")
        line2 = self.canvas.create_line(new_x, new_y, x2, y2, fill=self.linecolor, tags="line")
        
        # Insert the new lines into the lines list at the correct positions
        self.lines.insert(line_index, line1)
        self.lines.insert(line_index + 1, line2)
        
        # Bind hover events to the new lines
        self.canvas.tag_bind(line1, "<Enter>", lambda e, l=line1: self.on_line_hover_enter(e, l))
        self.canvas.tag_bind(line1, "<Leave>", lambda e, l=line1: self.on_line_hover_leave(e, l))
        self.canvas.tag_bind(line2, "<Enter>", lambda e, l=line2: self.on_line_hover_enter(e, l))
        self.canvas.tag_bind(line2, "<Leave>", lambda e, l=line2: self.on_line_hover_leave(e, l))
        
        # Draw the new dot at the clicked position
        dot = self.draw_point(new_x, new_y)
        self.dots.insert(end_point_index, dot)
        
        # # Redraw the entire polygon with the new structure
        # self.redraw_polygon()
    def delete_point(self, event, dot):
        if dot in self.dots:
            index = self.dots.index(dot)
            point_to_delete = self.points[index]

            self.canvas.delete(dot)
            self.dots.pop(index)
            self.points.pop(index)

            # Delete lines connected to the point
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
        for line in self.canvas.find_withtag("line"):
            self.canvas.delete(line)
        if self.polygon:
            self.canvas.delete(self.polygon)    
        for dot in self.canvas.find_withtag("dot"):
            self.canvas.delete(dot)
        self.points.clear()
        self.dots.clear()
        self.lines.clear()
        self.polygon = None

    def PILdrawpoly(self):
        overlay = Image.new('RGBA', self.image.size, (255,255,255,0))
        draw = ImageDraw.Draw(overlay)

        #Draw the polygon on the image
        draw.polygon(self.points, fill = self.polygoncolor)

        # Display the result on the canvas
        self.polygon = ImageTk.PhotoImage(overlay)

    def redraw_polygon(self):
        # Clear existing lines and polygon
        for line in self.lines:
            self.canvas.delete(line)
        self.lines.clear()

        if self.polygon:
            self.canvas.delete(self.polygon)
        self.polygon = None
        
        # Draw lines between points
        if len(self.points) > 1:
            if len(self.points) > 2:
                self.PILdrawpoly()
                poly = self.canvas.create_image(0, 0, image=self.polygon, anchor=tk.NW)
                lowest_item_id = self.canvas.find_all()[1]
                self.canvas.tag_lower(poly, lowest_item_id)

            for i in range(len(self.points) - 1):
                line = self.canvas.create_line(self.points[i], self.points[i+1], fill=self.linecolor, tags="line")
                self.lines.append(line)
                # Bind hover events to the line
                self.canvas.tag_bind(line, "<Enter>", lambda e, l=line: self.on_line_hover_enter(e, l))
                self.canvas.tag_bind(line, "<Leave>", lambda e, l=line: self.on_line_hover_leave(e, l))

            if len(self.points) > 2 and self.points[0] != self.points[-1]:
                line = self.canvas.create_line(self.points[-1], self.points[0], fill=self.linecolor, tags="line")
                self.lines.append(line)
                self.canvas.tag_bind(line, "<Enter>", lambda e, l=line: self.on_line_hover_enter(e, l))
                self.canvas.tag_bind(line, "<Leave>", lambda e, l=line: self.on_line_hover_leave(e, l))
        for dot in self.dots:
            self.canvas.tag_raise(dot)

    def redraw_points(self):
        # Clear existing dots
        for dot in self.dots:
            self.canvas.delete(dot)
        self.dots.clear()

        # Draw the dots based on the points list
        for (x, y) in self.points:
            dot = self.draw_point(x, y)
            self.dots.append(dot)
        
        # Ensure that dots are always on top
        for dot in self.dots:
            self.canvas.tag_raise(dot)


if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonDrawer(root)
    root.mainloop()
