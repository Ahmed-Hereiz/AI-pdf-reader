import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import fitz  # PyMuPDF
import random
import markdown
from tkhtmlview import HTMLScrolledText
import threading
import time
import os

class PDFHandler:
    def __init__(self, parent, file_manager):
        self.parent = parent
        self.file_manager = file_manager
        self.doc = None
        self.current_page = 0
        self.num_pages = 0
        self.zoom = 1.5
        self.page_text = ""
        self.current_pil_image = None
        self.img_offset = (0, 0)
        self.selection_callback = None  # to be set by AIOverlay
        self.sel_start = None
        self.sel_rect = None
        self.page_notes = {}
        self.create_widgets()

    def create_widgets(self):
        # Toolbar frame
        self.toolbar = ttk.Frame(self.parent, padding=5)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Buttons for open, previous, next
        from helpers import load_icon
        open_icon = load_icon("open_pdf.png", size=(32, 32))
        prev_icon = load_icon("prev_page.png", size=(32, 32))
        next_icon = load_icon("next_page.png", size=(32, 32))

        self.open_btn = ttk.Button(
            self.toolbar, text="Open PDF",
            image=open_icon, compound=tk.LEFT, command=self.open_pdf
        )
        self.open_btn.image = open_icon
        self.open_btn.pack(side=tk.LEFT, padx=4)

        self.prev_btn = ttk.Button(
            self.toolbar, text="Previous Page",
            image=prev_icon, compound=tk.LEFT, command=lambda: self.change_page("prev"), state=tk.DISABLED
        )
        self.prev_btn.image = prev_icon
        self.prev_btn.pack(side=tk.LEFT, padx=4)

        self.next_btn = ttk.Button(
            self.toolbar, text="Next Page",
            image=next_icon, compound=tk.LEFT, command=lambda: self.change_page("next"), state=tk.DISABLED
        )
        self.next_btn.image = next_icon
        self.next_btn.pack(side=tk.LEFT, padx=4)

        self.page_label = ttk.Label(self.toolbar, text="Page: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)

        # Canvas for PDF display
        self.canvas_frame = ttk.Frame(self.parent)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.page_canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.page_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.page_canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll = ttk.Scrollbar(self.parent, orient=tk.HORIZONTAL, command=self.page_canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.page_canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        # Bind mouse events for selection and scrolling
        self.page_canvas.bind("<Button-1>", self.on_canvas_mouse_down)
        self.page_canvas.bind("<B1-Motion>", self.on_canvas_mouse_drag)
        self.page_canvas.bind("<ButtonRelease-1>", self.on_canvas_mouse_up)
        self.parent.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.parent.bind_all("<Button-4>", self.on_mouse_wheel)
        self.parent.bind_all("<Button-5>", self.on_mouse_wheel)

        # Sticky note button
        from helpers import load_icon
        note_icon = load_icon("note_icon.png", size=(32, 32))
        self.add_note_btn = ttk.Button(
            self.parent,
            text="Take page's notes with AI",
            image=note_icon, compound=tk.LEFT,
            command=self.add_sticky_note, state=tk.DISABLED
        )
        self.add_note_btn.image = note_icon
        self.add_note_btn.place(x=10, rely=1.0, anchor="sw", y=-10)

    def open_pdf(self):
        pdf_path = self.file_manager.open_pdf_dialog()
        if pdf_path:
            self.doc = self.file_manager.load_pdf_document(pdf_path)
            if self.doc:
                self.num_pages = self.doc.page_count
                self.current_page = 0
                self.update_navigation_buttons()
                self.display_page(self.current_page)
                self.add_note_btn.config(state=tk.NORMAL)

    def display_page(self, page_number, scroll_position="top"):
        if not self.doc or not (0 <= page_number < self.num_pages):
            return
        page = self.doc.load_page(page_number)
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        from PIL import Image
        pil_img = Image.open(io.BytesIO(img_data))
        self.current_pil_image = pil_img
        self.page_image_tk = ImageTk.PhotoImage(pil_img)
        self.page_text = page.get_text("text")

        self.page_canvas.delete("all")
        img_width, img_height = pil_img.size
        self.page_canvas.config(scrollregion=(0, 0, img_width, img_height))
        canvas_width = self.page_canvas.winfo_width() or img_width
        canvas_height = self.page_canvas.winfo_height() or img_height
        x_offset = (canvas_width - img_width) // 2 if canvas_width > img_width else 0
        y_offset = (canvas_height - img_height) // 2 if canvas_height > img_height else 0
        self.page_canvas.create_image(x_offset, y_offset, anchor="nw", image=self.page_image_tk)
        self.img_offset = (x_offset, y_offset)
        if scroll_position == "top":
            self.page_canvas.yview_moveto(0)
        elif scroll_position == "bottom":
            self.page_canvas.yview_moveto(1)
        self.page_label.config(text=f"Page: {page_number+1}/{self.num_pages}")
        self.show_sticky_note_for_page(page_number)

    def change_page(self, direction):
        if direction == "next" and self.current_page < self.num_pages - 1:
            self.current_page += 1
            self.display_page(self.current_page)
        elif direction == "prev" and self.current_page > 0:
            self.current_page -= 1
            self.display_page(self.current_page)
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        if not self.doc:
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)
            self.page_label.config(text="Page: 0/0")
        else:
            self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if self.current_page < self.num_pages - 1 else tk.DISABLED)
            self.page_label.config(text=f"Page: {self.current_page+1}/{self.num_pages}")

    def on_mouse_wheel(self, event):
        if self.sel_start is not None:
            return "break"
        if hasattr(event, 'num'):
            delta = -1 if event.num == 4 else 1 if event.num == 5 else 0
        else:
            delta = -int(event.delta / 120)
        first, last = self.page_canvas.yview()
        if delta > 0 and last >= 0.999 and self.current_page < self.num_pages - 1:
            self.change_page("next")
            return "break"
        elif delta < 0 and first <= 0.001 and self.current_page > 0:
            self.change_page("prev")
            return "break"
        self.page_canvas.yview_scroll(delta, "units")
        return "break"

    def on_canvas_mouse_down(self, event):
        if self.sel_rect:
            self.page_canvas.delete(self.sel_rect)
            self.sel_rect = None
        self.sel_start = (self.page_canvas.canvasx(event.x), self.page_canvas.canvasy(event.y))

    def on_canvas_mouse_drag(self, event):
        if not self.sel_start:
            return
        x0, y0 = self.sel_start
        x1, y1 = self.page_canvas.canvasx(event.x), self.page_canvas.canvasy(event.y)
        if self.sel_rect:
            self.page_canvas.delete(self.sel_rect)
        self.sel_rect = self.draw_rounded_rectangle(x0, y0, x1, y1, r=10, fill="", outline="#1E90FF", width=3)

    def on_canvas_mouse_up(self, event):
        if not self.sel_start:
            return
        x0, y0 = self.sel_start
        x1, y1 = self.page_canvas.canvasx(event.x), self.page_canvas.canvasy(event.y)
        self.sel_start = None
        rx0, ry0 = min(x0, x1), min(y0, y1)
        rx1, ry1 = max(x0, x1), max(y0, y1)
        cropped_image = self.get_cropped_region(rx0, ry0, rx1, ry1)
        if cropped_image and self.selection_callback:
            self.selection_callback(rx0, ry0, cropped_image)
        if self.sel_rect:
            self.page_canvas.delete(self.sel_rect)
            self.sel_rect = None

    def draw_rounded_rectangle(self, x1, y1, x2, y2, r=10, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        ]
        return self.page_canvas.create_polygon(points, smooth=True, **kwargs)

    def get_cropped_region(self, x0, y0, x1, y1):
        if not self.current_pil_image:
            return None
        ox, oy = self.img_offset
        crop_left = max(0, min(self.current_pil_image.width, x0 - ox))
        crop_top = max(0, min(self.current_pil_image.height, y0 - oy))
        crop_right = max(0, min(self.current_pil_image.width, x1 - ox))
        crop_bottom = max(0, min(self.current_pil_image.height, y1 - oy))
        if crop_right <= crop_left or crop_bottom <= crop_top:
            return None
        return self.current_pil_image.crop((crop_left, crop_top, crop_right, crop_bottom))

    def add_sticky_note(self):
        # Immediately show a placeholder note
        self.page_notes[self.current_page] = "<p><em>Generating note...</em></p>"
        self.show_sticky_note_for_page(self.current_page)
        # In background, generate note using AI
        def threaded_note():
            from call_ai import notes_ai
            md_text = notes_ai(self.page_text, self.current_pil_image)
            html_text = markdown.markdown(md_text)
            self.page_notes[self.current_page] = html_text
            self.parent.after(0, lambda: self.show_sticky_note_for_page(self.current_page))
        threading.Thread(target=threaded_note, daemon=True).start()

    def show_sticky_note_for_page(self, page_number):
        # Remove any existing note
        existing = self.page_canvas.find_withtag("sticky_note")
        for item in existing:
            self.page_canvas.delete(item)
        if page_number not in self.page_notes:
            return
        html_text = self.page_notes[page_number]
        note_width = 400
        max_note_height = 700
        if self.current_pil_image:
            pdf_width, pdf_height = self.current_pil_image.width, self.current_pil_image.height
            x_left = 15
            y_center = self.img_offset[1] + (pdf_height // 2)
        else:
            x_left = 15
            y_center = 100
        note_frame = tk.Frame(self.page_canvas, bg="#F0F8FF", highlightthickness=1, highlightbackground="#888")
        note_frame.pack_propagate(True)
        top_bar = tk.Frame(note_frame, bg="#F0F8FF")
        top_bar.pack(fill="x", side="top")
        def delete_current_note():
            if page_number in self.page_notes:
                del self.page_notes[page_number]
            self.page_canvas.delete(window_id)
        from tkinter import ttk
        del_btn = ttk.Button(top_bar, text="Remove Note", command=delete_current_note)
        del_btn.pack(side="right", padx=5, pady=5)
        scroll_label = HTMLScrolledText(note_frame, html=html_text, background="#F0F8FF", padx=5, pady=5)
        scroll_label.pack(fill="both", expand=True)
        window_id = self.page_canvas.create_window(x_left, y_center, anchor="center", window=note_frame, tags="sticky_note")
        scroll_label.update_idletasks()
        required_height = scroll_label.winfo_reqheight()
        final_height = min(required_height, max_note_height)
        note_frame.config(width=note_width, height=final_height)
        note_frame.pack_propagate(False)
        final_y = y_center - (final_height // 2)
        self.page_canvas.coords(window_id, x_left, final_y)
        self.page_canvas.itemconfig(window_id, anchor="nw")
