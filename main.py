import tkinter as tk
from tkinter import ttk
from fileai.file_manager import FileManager
from fileai.pdf_handler import PDFHandler
from fileai.ai_overlay import AIOverlay

def main():
    root = tk.Tk()
    root.title("PDF Viewer with AI")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")

    # Create a frame to hold PDFHandler and AIOverlay
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Initialize FileManager
    file_manager = FileManager(root)
    
    # PDF Handler on the left
    pdf_frame = ttk.Frame(main_frame)
    pdf_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    pdf_handler = PDFHandler(pdf_frame, file_manager)

    # AI Overlay handles AI popups, chat panel, and voice commands on the right
    ai_overlay = AIOverlay(root, pdf_handler)

    root.mainloop()

if __name__ == "__main__":
    main()
