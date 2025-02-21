import os
from PIL import Image, ImageTk


def load_icon(filename, size=(50, 50)):
    """Helper to load an image icon from assets (with fallback to text if not found)."""
    ASSETS_DIR = "assets"
    path = os.path.join(ASSETS_DIR, filename)
    try:
        img = Image.open(path)
        img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None
