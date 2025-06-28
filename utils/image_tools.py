# utils/image_tools.py
from PIL import ImageDraw

def highlight_click(image, x, y, radius=20, color="red", width=4):
    draw = ImageDraw.Draw(image)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=color, width=width)
    return image
