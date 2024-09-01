import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from tkinter import filedialog

class PolygonDrawer:
    def __init__(self, root):
        self.root = root
        self.root.title("Polygon Drawer")

        # Load image
        self.image_path = filedialog.askopenfilename(title="Select an Image")
        self.original_image = Image.open(self.image_path)
        self.original_width, self.original_height = self.original_image.size

        # Create Canvas
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind resize event
        self.canvas.bind("<Configure>", self.on_resize)
        
        # Initialize variables
        self.points = []
        self.dots = []
        self.lines = []
        self.polygon = None

        # Create a context menu
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Delete Polygon", command=self.delete_polygon)
        
        # Initialize dragging variables
        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.drag_threshold = 5
        self.is_dragging = False
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Button-3>", self.handle_right_click)

    def on_resize(self, event):
        # Resize the image and canvas to maintain aspect ratio
        self.resize_image_and_canvas(event.width, event.height)
        self.redraw_polygon()
        
    def resize_image_and_canvas(self, new_width, new_height):
        # Calculate scaling factor to maintain aspect ratio
        scale_width = new_width / self.original_width
        scale_height = new_height / self.original_height
        scale = min(scale_width, scale_height)
        
        # Resize image
        resized_image = self.original_image.resize(
            (int(self.original_width * scale), int(self.original_height * scale)),
            Image.Resampling.LANCZOS
        )
        
        # Update image and canvas size
        self.photo = ImageTk.PhotoImage(resized_image)
        self.canvas.config(width=new_width, height=new_height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        
        # Adjust the canvas scrollregion to match the new image size
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def on_mouse_down(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        clicked_items = self.canvas.find_withtag("current")

        if clicked_items and "dot" in self.canvas.gettags(clicked_items[0]):
            self.drag_data["item"] = clicked_items[0]
            self.is_dragging = False
        else:
            self.drag_data["item"] = None

    def do_drag(self, event):
        if self.drag_data["item"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]

            if abs(dx) > self.drag_threshold or abs(dy) > self.drag_threshold:
                self.is_dragging = True
                try:
                    index = self.dots.index(self.drag_data["item"])
                except ValueError:
                    return

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

    def draw_point(self, x, y):
        dot_size = 6
        dot = self.canvas.create_oval(x-dot_size, y-dot_size, x+dot_size, y+dot_size, fill="red", tags="dot")
        self.canvas.tag_bind(dot, "<Enter>", lambda e, d=dot: self.on_hover_enter(e, d))
        self.canvas.tag_bind(dot, "<Leave>", lambda e, d=dot: self.on_hover_leave(e, d))
        self.canvas.tag_bind(dot, "<ButtonPress-1>", self.on_mouse_down)
        self.canvas.tag_bind(dot, "<B1-Motion>", self.do_drag)
        self.canvas.tag_bind(dot, "<ButtonRelease-1>", self.on_mouse_up)
        return dot

    def on_hover_enter(self, event, dot):
        self.canvas.itemconfig(dot, fill="yellow")
    
    def on_hover_leave(self, event, dot):
        self.canvas.itemconfig(dot, fill="red")

    def on_line_hover_enter(self, event, line):
        self.canvas.itemconfig(line, fill="yellow")

    def on_line_hover_leave(self, event, line):
        self.canvas.itemconfig(line, fill="blue")

    def handle_right_click(self, event):
        clicked_items = self.canvas.find_withtag("current")

        if clicked_items:
            if "dot" in self.canvas.gettags(clicked_items[0]):
                self.delete_point(event, clicked_items[0])
            elif "line" in self.canvas.gettags(clicked_items[0]):
                self.add_point_to_line(event, clicked_items[0])
        else:
            self.show_context_menu(event)
    
    def add_point(self, event):
        x, y = event.x, event.y
        self.points.append((x, y))
        dot = self.draw_point(x, y)
        self.dots.append(dot)
        self.redraw_polygon()
    
    def add_point_to_line(self, event, line):
        new_x, new_y = event.x, event.y
        coords = self.canvas.coords(line)
        x1, y1, x2, y2 = coords
        
        line_index = self.lines.index(line)
        self.points.insert(line_index + 1, (new_x, new_y))
        
        self.canvas.delete(line)
        self.lines.pop(line_index)
        
        line1 = self.canvas.create_line(x1, y1, new_x, new_y, fill="blue", tags="line")
        line2 = self.canvas.create_line(new_x, new_y, x2, y2, fill="blue", tags="line")
        
        self.lines.insert(line_index, line1)
        self.lines.insert(line_index + 1, line2)
        
        dot = self.draw_point(new_x, new_y)
        self.dots.insert(line_index + 1, dot)
        
        self.redraw_polygon()

    def delete_point(self, event, dot):
        if dot in self.dots:
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

        draw.polygon(self.points, fill=(0,0,255,int(0.2*255)))

        combined = Image.alpha_composite(self.image.convert('RGBA'), overlay)
        self.polygon = ImageTk.PhotoImage(combined)

    def redraw_polygon(self):
        for line in self.lines:
            self.canvas.delete(line)
        self.lines.clear()
        if self.polygon:
            self.canvas.delete(self.polygon)
        self.polygon = None
        
        if len(self.points) > 1:
            if len(self.points) > 2:
                for i in range(len(self.points) - 1):
                    line = self.canvas.create_line(self.points[i], self.points[i+1], fill="blue", tags="line")
                    self.lines.append(line)
                    self.canvas.tag_bind(line, "<Enter>", lambda e, l=line: self.on_line_hover_enter(e, l))
                    self.canvas.tag_bind(line, "<Leave>", lambda e, l=line: self.on_line_hover_leave(e, l))

                if len(self.points) > 2 and self.points[0] != self.points[-1]:
                    line = self.canvas.create_line(self.points[-1], self.points[0], fill="blue", tags="line")
                    self.lines.append(line)
                    self.canvas.tag_bind(line, "<Enter>", lambda e, l=line: self.on_line_hover_enter(e, l))
                    self.canvas.tag_bind(line, "<Leave>", lambda e, l=line: self.on_line_hover_leave(e, l))
                    
            self.PILdrawpoly()
            poly = self.canvas.create_image(0, 0, image=self.polygon, anchor=tk.NW)
            self.canvas.tag_lower(poly, self.canvas.find_all()[1])

        self.redraw_points()

    def redraw_points(self):
        for i, (x, y) in enumerate(self.points):
            dot = self.dots[i]
            dot_size = 6
            self.canvas.coords(dot, x-dot_size, y-dot_size, x+dot_size, y+dot_size)
            self.canvas.tag_bind(dot, "<Enter>", lambda e, d=dot: self.on_hover_enter(e, d))
            self.canvas.tag_bind(dot, "<Leave>", lambda e, d=dot: self.on_hover_leave(e, d))

if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonDrawer(root)
    root.mainloop()
