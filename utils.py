import cv2
import numpy as np
import os
import re
import ast
from PIL import Image, ImageDraw, ImageTk

def hextocomp(hex):
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
    
def masktopoints(numpoints, scale_factor, maskpath):
    # Load the PNG image as a grayscale image (0 means grayscale mode)
    binary_mask = cv2.imread(maskpath, cv2.IMREAD_GRAYSCALE)
    myocard_mask = binary_mask.copy()
    myocard_mask[myocard_mask==127] = 0 
    contours, _ = cv2.findContours(myocard_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Get the first contour (assuming you only have one object)
    boundary_points = contours[0]  # (N, 1, 2) array representing x, y coordinates

    numpoints = numpoints
    step = len(boundary_points)//numpoints
    boundary_points = boundary_points[::step]
    points = [tuple(arr.flatten()) for arr, in boundary_points]
    if len(points) != 0:
        scaledpoints = [(a * scale_factor, b * scale_factor) for a, b in points] #Scale all the original points to match the current scale
    currentdottags = [("dot",)] * len(points)

    def check_cavity_around_point(center, radius,image=binary_mask):
        # Create a mask with the same size as the image, initialized to zeros
        mask = np.zeros(image.shape[:2], dtype=np.uint8)

        # Draw a filled circle on the mask
        cv2.circle(mask, center, radius, 255, thickness=-1)

        # Use the mask to get the region of interest from the image
        circular_patch = cv2.bitwise_and(image, image, mask=mask)

        # Check if any pixel in the circular patch has the value of 127
        return np.any(circular_patch == 127)

    for i in range(len(points)):
        if check_cavity_around_point(points[i], 4):
            #Set the tag to be "dot","cavity"
            currentdottags[i] = ("dot","cavity")
    return points, scaledpoints, currentdottags

def load_images(base_path):
    """Load time folders and slice files."""
    # Regular expression to match time folders in the format time001, time002, etc.
    if os.path.exists(base_path):
        time_pattern = re.compile(r'^time\d{3}$')
        image_pattern = re.compile(r'^slice\d{3}time\d{3}.png$')

        # Get all time folders matching the format
        time_folders = sorted([d for d in os.listdir(base_path) 
                                    if os.path.isdir(os.path.join(base_path, d)) and time_pattern.match(d)])
        # print(f"Time folders found: {len(self.time_folders)}")  # Debugging line

        # Get all slice files for each time folder
        slice_files = [sorted([f for f in os.listdir(os.path.join(base_path, t)) 
                            if os.path.isfile(os.path.join(base_path, t, f)) and image_pattern.match(f)])
                    for t in time_folders]
        # print(f"Slice files found: {len(self.slice_files[0])}")  # Debugging line
        return slice_files, time_folders

    else:
        return [], []
    
def PILdrawpoly(currentdottags, scaledpoints, dims, polygoncolor):
        current_width, current_height = dims
        cavidx = [index for index, tup in enumerate(currentdottags) if "cavity" in tup]
        cavitypoints = [scaledpoints[i] for i in cavidx]

        overlay = Image.new('RGBA', (current_width, current_height), (255,255,255,0))
        draw = ImageDraw.Draw(overlay)
        #Draw the polygon on the image
        draw.polygon(scaledpoints, fill = polygoncolor)
        if len(cavitypoints)>2:
            draw.polygon(cavitypoints, fill=hextocomp(polygoncolor))

        # Display the result on the canvas
        polygon = ImageTk.PhotoImage(overlay)

        return polygon

def set_aspect(content_frame, pad_frame, aspect_ratio):
        """Implemented from user Bryan Oakley : https://stackoverflow.com/a/16548607
        # a function which places a frame within a containing frame, and
        # then forces the inner frame to keep a specific aspect ratio"""
        def enforce_aspect_ratio(event):
            desired_width = event.width
            desired_height = int(event.width / aspect_ratio)

            if desired_height > event.height:
                desired_height = event.height
                desired_width = int(event.height * aspect_ratio)

            x_center = (event.width - desired_width) // 2
            y_center = (event.height - desired_height) // 2

            content_frame.place(in_=pad_frame, x=x_center, y=y_center, anchor="nw",
                width=desired_width, height=desired_height)

        pad_frame.bind("<Configure>", enforce_aspect_ratio)

def extract_and_draw_contours(mask_path):
    """
    Extract contours from a multiclass mask (0, 1, 2) and draw them on a new array.

    Parameters:
    - mask: A NumPy array representing the mask (shape: [H, W]) with values 0, 1, or 2.

    Returns:
    - overlay: A NumPy array with contours drawn on a black background.
    """
    # Create an empty black image to draw contours
    mask = Image.open(mask_path).convert("L")
    mask = np.array(mask)
    mask[mask == 127] = 1
    mask[mask == 255] = 2
    overlay = np.zeros((*mask.shape, 4), dtype=np.uint8)

    # Define colors for each class
    colors = {
        1: (0, 0, 255, 255),    # Red for class 1 (RGBA)
        2: (0, 255, 255, 255)   # Yellow for class 2 (RGBA)
    }

    # Iterate over the classes (1 and 2) to find and draw contours
    for class_value in [1, 2]:
        # Create a binary mask for the current class
        binary_mask = np.zeros(mask.shape, dtype=np.uint8)
        binary_mask[mask == class_value] = 255  # Set pixels of the current class to 255

        # Find contours
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw contours for the current class
        for contour in contours:
            # Create a temporary image to draw the contour in RGBA
            temp_overlay = np.zeros((*mask.shape, 4), dtype=np.uint8)
            cv2.drawContours(temp_overlay, [contour], -1, colors[class_value], thickness=1)  # Draw the contour with the correct RGBA color

            # Add the contour to the main overlay
            overlay = np.maximum(overlay, temp_overlay)  # Ensure that contours do not overwrite each other

    return overlay

def overlay_images(base_image, overlay_image):
    """
    Overlay an RGBA mask onto a grayscale base image, converting it to RGB first.

    Parameters:
    - base_image: The base NumPy array image (grayscale).
    - overlay_image: The overlay NumPy array image (RGBA).

    Returns:
    - result: The NumPy array image with the overlay applied.
    """
    # Convert the grayscale base image to RGB by stacking the single channel
    base_rgb = cv2.cvtColor(base_image, cv2.COLOR_GRAY2RGB)

    # Extract the RGB and alpha channel from the overlay
    overlay_rgb = overlay_image[:, :, :3]  # RGB channels
    alpha_channel = overlay_image[:, :, 3] / 255.0  # Alpha channel normalized to [0, 1]

    # Create a mask where alpha is greater than 0 (i.e., overlay pixels to apply)
    alpha_mask = alpha_channel > 0

    # Blend or replace the base image with the overlay based on alpha
    for c in range(3):  # Loop over RGB channels
        base_rgb[:, :, c] = np.where(alpha_mask, overlay_rgb[:, :, c], base_rgb[:, :, c])

    return base_rgb