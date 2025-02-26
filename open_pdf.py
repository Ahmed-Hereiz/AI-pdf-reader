import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io
from gtts import gTTS
import os
import pygame
import threading
import random
import webbrowser
import time
import pyaudio
import wave
import numpy as np

import arabic_reshaper
from bidi.algorithm import get_display
import markdown
from tkhtmlview import HTMLScrolledText, HTMLLabel

from call_ai import ask_ai, explain_ai, translate_ai, chat_ai, notes_ai, search_ai
from helpers import load_icon

pygame.mixer.init()

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Viewer with AI")
        self.root.configure(bg="#E3F2FD")

        self.doc = None
        self.current_page = 0
        self.num_pages = 0

        # For rendering PDF pages
        self.current_pil_image = None
        self.page_text = ""
        self.page_image_tk = None
        self.img_offset = (0, 0)

        # For selection overlays
        self.ai_popup = None
        self.response_popup = None
        self.sel_rect = None
        self.sel_start = None
        self.selection_overlay = None
        self.selected_cropped_image = None

        # Audio playback variables
        self.current_audio_file = None

        # Zoom factor for PDF pages
        self.zoom = 1.5

        # Chat panel state
        self.chat_open = False
        self.chat_target_width = 350
        self.current_chat_width = 0

        # Chat icons
        self.chat_open_icon_img = load_icon("chat-open.png", size=(24, 24))
        self.chat_close_icon_img = load_icon("chat-close.png", size=(24, 24))
        self.chat_open_icon_text = "Chat with AI"
        self.chat_close_icon_text = "❌"

        # For streaming responses and TTS
        self.current_response_text = ""
        self.response_language = "en"
        self.streaming_in_progress = False

        # TTS streaming
        self.tts_streaming = False
        self.tts_read_index = 0
        self.read_button = None

        # We'll keep a reference to any sticky notes we create
        # keyed by page number: page_notes[page_number] = (widget, or data)
        self.page_notes = {}

        # For voice commands
        self.recording = False
        self.voice_command_popup = None

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Main frames
        style.configure("TFrame", background="#E3F2FD")

        # Toolbar
        style.configure("Toolbar.TFrame", background="#E1F5FE")

        style.configure(
            "RoundedButton.TButton",
            padding=6,
            relief="flat",
            background="#2196F3",
            foreground="white",
            borderwidth=0,
            font=("Helvetica", 11, "bold")
        )
        style.map(
            "RoundedButton.TButton",
            background=[("active", "#1976D2"), ("!active", "#2196F3")],
            foreground=[("active", "white"), ("!active", "white")]
        )

        style.configure(
            "Toolbar.TLabel",
            background="#E1F5FE",
            foreground="#0D47A1",
            font=("Helvetica", 12, "bold")
        )

        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background="#BBDEFB",
            darkcolor="#90CAF9",
            lightcolor="#E3F2FD",
            troughcolor="#E3F2FD",
            bordercolor="#E3F2FD",
            arrowcolor="#0D47A1"
        )
        style.configure(
            "Horizontal.TScrollbar",
            gripcount=0,
            background="#BBDEFB",
            darkcolor="#90CAF9",
            lightcolor="#E3F2FD",
            troughcolor="#E3F2FD",
            bordercolor="#E3F2FD",
            arrowcolor="#0D47A1"
        )

        style.configure("Overlay.TFrame", background="#BBDEFB", relief="raised", borderwidth=1)
        style.configure("Chat.TFrame", background="#F7F7F7")

    def create_widgets(self):
        # Top toolbar
        toolbar = ttk.Frame(self.root, style="Toolbar.TFrame", padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        open_icon = load_icon("open_pdf.png", size=(32, 32))
        prev_icon = load_icon("prev_page.png", size=(32, 32))
        next_icon = load_icon("next_page.png", size=(32, 32))

        open_btn = ttk.Button(
            toolbar,
            text="Open PDF",
            style="RoundedButton.TButton",
            image=open_icon,
            compound=tk.LEFT,
            command=self.open_pdf
        )
        open_btn.image = open_icon
        open_btn.pack(side=tk.LEFT, padx=4)

        self.prev_btn = ttk.Button(
            toolbar,
            text="Previous Page",
            style="RoundedButton.TButton",
            image=prev_icon,
            compound=tk.LEFT,
            command=lambda: self.change_page("prev", "bottom"),
            state=tk.DISABLED
        )
        self.prev_btn.image = prev_icon
        self.prev_btn.pack(side=tk.LEFT, padx=4)

        self.next_btn = ttk.Button(
            toolbar,
            text="Next Page",
            style="RoundedButton.TButton",
            image=next_icon,
            compound=tk.LEFT,
            command=lambda: self.change_page("next", "top"),
            state=tk.DISABLED
        )
        self.next_btn.image = next_icon
        self.next_btn.pack(side=tk.LEFT, padx=4)

        self.page_label = ttk.Label(toolbar, text="Page: 0/0", style="Toolbar.TLabel")
        self.page_label.pack(side=tk.LEFT, padx=10)

        # Main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Left side for PDF
        self.viewer_frame = ttk.Frame(self.main_frame)
        self.viewer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Canvas + scrollbars
        self.canvas_frame = ttk.Frame(self.viewer_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.page_canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.page_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.page_canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 2))
        self.h_scroll = ttk.Scrollbar(self.viewer_frame, orient=tk.HORIZONTAL, command=self.page_canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
        self.page_canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        # "Take page's notes with AI" button
        note_icon = load_icon("note_icon.png", size=(32, 32))
        self.add_note_btn = ttk.Button(
            self.viewer_frame,
            text="Take page's notes with AI",
            image=note_icon,
            style="RoundedButton.TButton",
            compound=tk.LEFT,
            command=self.add_sticky_note
        )
        self.add_note_btn.image = note_icon
        self.add_note_btn.place(x=10, rely=1.0, anchor="sw", y=-10)
        self.add_note_btn.config(state=tk.DISABLED)

        self.root.update_idletasks()
        notes_button_width = self.add_note_btn.winfo_width()

        voice_icon = load_icon("record_icon.png", size=(32, 32))
        self.voice_command_btn = ttk.Button(
            self.viewer_frame,
            text="Voice Commands",
            image=voice_icon,
            style="RoundedButton.TButton",
            compound=tk.LEFT,
            command=self.start_voice_command
        )
        self.voice_command_btn.image = voice_icon
        self.voice_command_btn.place(x=10 + notes_button_width + 10, rely=1.0, anchor="sw", y=-10)

        self.root.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.root.bind_all("<Button-4>", self.on_mouse_wheel)
        self.root.bind_all("<Button-5>", self.on_mouse_wheel)
        self.page_canvas.bind("<Enter>", lambda e: self.page_canvas.focus_set())

        self.page_canvas.bind("<Button-1>", self.on_canvas_mouse_down)
        self.page_canvas.bind("<B1-Motion>", self.on_canvas_mouse_drag)
        self.page_canvas.bind("<ButtonRelease-1>", self.on_canvas_mouse_up)

        self.chat_frame = ttk.Frame(self.main_frame, style="Chat.TFrame", width=0)
        self.chat_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_frame.pack_propagate(False)
        self.setup_ai_chat()

        self.toggle_button = ttk.Button(
            self.main_frame,
            style="RoundedButton.TButton",
            command=self.toggle_chat,
            image=self.chat_open_icon_img if self.chat_open_icon_img else None,
            text="" if self.chat_open_icon_img else self.chat_open_icon_text,
            compound=tk.LEFT
        )
        self.toggle_button.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)


        # ===============================================================================

        # Mouse wheel
        self.root.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.root.bind_all("<Button-4>", self.on_mouse_wheel)
        self.root.bind_all("<Button-5>", self.on_mouse_wheel)
        self.page_canvas.bind("<Enter>", lambda e: self.page_canvas.focus_set())

        # Selection
        self.page_canvas.bind("<Button-1>", self.on_canvas_mouse_down)
        self.page_canvas.bind("<B1-Motion>", self.on_canvas_mouse_drag)
        self.page_canvas.bind("<ButtonRelease-1>", self.on_canvas_mouse_up)

        # Right frame: AI Chat
        self.chat_frame = ttk.Frame(self.main_frame, style="Chat.TFrame", width=0)
        self.chat_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_frame.pack_propagate(False)
        self.setup_ai_chat()

        self.toggle_button = ttk.Button(
            self.main_frame,
            style="RoundedButton.TButton",
            command=self.toggle_chat,
            image=self.chat_open_icon_img if self.chat_open_icon_img else None,
            text="" if self.chat_open_icon_img else self.chat_open_icon_text,
            compound=tk.LEFT
        )
        self.toggle_button.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)

    def add_sticky_note(self):
        """
        1) Immediately show a 'Generating...' note so the user knows it's in progress.
        2) In a background thread, call notes_ai(...) to get Markdown text.
        3) Convert to HTML and replace the placeholder in self.page_notes.
        4) Show the final note in show_sticky_note_for_page.
        """

        self.page_notes[self.current_page] = "<p><em>Generating note...</em></p>"
        self.show_sticky_note_for_page(self.current_page)

        def threaded_note():
            md_text = notes_ai(self.page_text, self.current_pil_image)
            html_text = markdown.markdown(md_text)
            self.page_notes[self.current_page] = html_text
            self.root.after(0, lambda: self.show_sticky_note_for_page(self.current_page))

        # Run in background so UI remains responsive
        threading.Thread(target=threaded_note, daemon=True).start()

    def show_sticky_note_for_page(self, page_number):
        """
        Display the stored HTML note for 'page_number' on the left side of the page,
        with a vertical scrollbar if needed. Also includes a 'Remove Note' button.
        """

        # Remove any existing note from the canvas
        existing = self.page_canvas.find_withtag("sticky_note")
        for item in existing:
            self.page_canvas.delete(item)

        if page_number not in self.page_notes:
            return

        html_text = self.page_notes[page_number]

        # Choose a random background color
        note_colors = [
            "#F0F8FF"   # AliceBlue
        ]
        bg_color = random.choice(note_colors)

        # We'll allow a fixed width and a maximum height
        note_width = 400
        max_note_height = 700

        # Compute where to place the note on the PDF
        if self.current_pil_image:
            pdf_width, pdf_height = self.current_pil_image.width, self.current_pil_image.height
            x_left = 15
            y_center = self.img_offset[1] + (pdf_height // 2)
        else:
            x_left = 15
            y_center = 100

        # Create a frame for the note
        note_frame = tk.Frame(
            self.page_canvas,
            bg=bg_color,
            highlightthickness=1,
            highlightbackground="#888"
        )
        # Let the frame expand to content initially
        note_frame.pack_propagate(True)

        # --- Top bar with "Remove Note" button ---
        top_bar = tk.Frame(note_frame, bg=bg_color)
        top_bar.pack(fill="x", side="top")

        def delete_current_note():
            """Remove the note from this page and from the canvas."""
            if page_number in self.page_notes:
                del self.page_notes[page_number]
            self.page_canvas.delete(window_id)

        del_btn = ttk.Button(top_bar, text="Remove Note", command=delete_current_note)
        del_btn.pack(side="right", padx=5, pady=5)

        # --- Main content area: HTMLScrolledText with vertical scrollbar ---
        scroll_label = HTMLScrolledText(
            note_frame,
            html=html_text,
            background=bg_color,
            padx=5,
            pady=5
        )
        scroll_label.pack(fill="both", expand=True)

        # Place the note on the canvas (temporary) so we can measure size
        window_id = self.page_canvas.create_window(
            x_left, y_center,
            anchor="center",
            window=note_frame,
            tags="sticky_note"
        )

        # Force geometry calculation
        scroll_label.update_idletasks()

        required_width = scroll_label.winfo_reqwidth()
        required_height = scroll_label.winfo_reqheight()

        # Clamp the height
        final_height = min(required_height, max_note_height)

        # Fix the frame to final size; no more auto-shrinking
        note_frame.config(width=note_width, height=final_height)
        note_frame.pack_propagate(False)

        # Recompute the Y coordinate to center vertically
        final_y = y_center - (final_height // 2)

        # Move the note to that position, anchored top-left
        self.page_canvas.coords(window_id, x_left, final_y)
        self.page_canvas.itemconfig(window_id, anchor="nw")

    def setup_ai_chat(self):
        self.chat_frame.configure(padding=10)
        top_bar = tk.Frame(self.chat_frame, bg="#F7F7F7")
        top_bar.pack(fill=tk.X, pady=(0, 5))

        title_label = tk.Label(
            top_bar,
            text="AI Chat",
            font=("Segoe UI", 12, "bold"),
            bg="#F7F7F7",
            fg="#0D47A1"
        )
        title_label.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(
            top_bar,
            text="X",
            font=("Segoe UI", 10, "bold"),
            bg="#F7F7F7",
            fg="red",
            bd=0,
            command=self.toggle_chat
        )
        close_btn.pack(side=tk.RIGHT, padx=5)

        self.chat_log_frame = ttk.Frame(self.chat_frame)
        self.chat_log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.chat_log = tk.Text(
            self.chat_log_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Segoe UI", 11),
            background="#F7F7F7",
            foreground="#0D47A1",
            bd=0,
            relief="flat",
            highlightthickness=0
        )
        self.chat_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_scroll = ttk.Scrollbar(self.chat_log_frame, orient=tk.VERTICAL, command=self.chat_log.yview)
        self.chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_log.configure(yscrollcommand=self.chat_scroll.set)

        chat_input_frame = ttk.Frame(self.chat_frame)
        chat_input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.chat_input = tk.Text(
            chat_input_frame,
            height=3,
            wrap="word",
            font=("Segoe UI", 11),
            bd=1,
            relief="solid",
            padx=5,
            pady=5
        )
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chat_input.bind("<Return>", self.on_enter_pressed)

        send_button = ttk.Button(chat_input_frame, text="Send ➤", command=self.process_ai_chat_message)
        send_button.pack(side=tk.LEFT, padx=(5, 0))

    def on_enter_pressed(self, event):
        if event.state & 0x0001:
            return None
        else:
            self.process_ai_chat_message()
            return "break"

    def toggle_chat(self):
        if self.chat_open:
            self.animate_chat_close()
            self.toggle_button.config(
                image=self.chat_open_icon_img if self.chat_open_icon_img else "",
                text="" if self.chat_open_icon_img else self.chat_open_icon_text
            )
            self.chat_open = False
        else:
            self.animate_chat_open()
            self.toggle_button.config(
                image=self.chat_close_icon_img if self.chat_close_icon_img else "",
                text="" if self.chat_close_icon_img else self.chat_close_icon_text
            )
            self.chat_open = True

    def animate_chat_open(self):
        if self.current_chat_width < self.chat_target_width:
            self.current_chat_width += 10
            if self.current_chat_width > self.chat_target_width:
                self.current_chat_width = self.chat_target_width
            self.chat_frame.config(width=self.current_chat_width)
            self.root.after(10, self.animate_chat_open)

    def animate_chat_close(self):
        if self.current_chat_width > 0:
            self.current_chat_width -= 10
            if self.current_chat_width < 0:
                self.current_chat_width = 0
            self.chat_frame.config(width=self.current_chat_width)
            self.root.after(10, self.animate_chat_close)

    def open_pdf(self):
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if pdf_path:
            try:
                self.doc = fitz.open(pdf_path)
                self.num_pages = self.doc.page_count
                self.current_page = 0
                self.update_navigation_buttons()
                self.display_page(self.current_page, scroll_position="top")
                # Enable the "Add Note" button now that PDF is open
                self.add_note_btn.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF:\n{e}")

    def display_page(self, page_number, scroll_position="top"):
        if not self.doc or not (0 <= page_number < self.num_pages):
            return
        page = self.doc.load_page(page_number)
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
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

        # If this page has a note, show it
        self.show_sticky_note_for_page(page_number)

    def change_page(self, direction, scroll_position="top"):
        if direction == "next" and self.current_page < self.num_pages - 1:
            self.current_page += 1
            self.display_page(self.current_page, scroll_position=scroll_position)
        elif direction == "prev" and self.current_page > 0:
            self.current_page -= 1
            self.display_page(self.current_page, scroll_position=scroll_position)
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
            self.change_page("next", scroll_position="top")
            return "break"
        elif delta < 0 and first <= 0.001 and self.current_page > 0:
            self.change_page("prev", scroll_position="bottom")
            return "break"
        self.page_canvas.yview_scroll(delta, "units")
        return "break"

    def on_canvas_mouse_down(self, event):
        if self.selection_overlay is not None:
            self.page_canvas.delete(self.selection_overlay)
            self.selection_overlay = None
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
        if cropped_image is not None:
            self.show_selection_overlay(rx0, ry0, cropped_image)

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

    def show_selection_overlay(self, x, y, cropped_image):
        self.selected_cropped_image = cropped_image
        if self.selection_overlay is not None:
            self.page_canvas.delete(self.selection_overlay)
            self.selection_overlay = None
        overlay_frame = ttk.Frame(self.page_canvas, style="Overlay.TFrame")

        ask_img = Image.open("assets/ask_icon.png").resize((20, 20), Image.LANCZOS)
        self.ask_icon = ImageTk.PhotoImage(ask_img)
        explain_img = Image.open("assets/explain_icon.png").resize((20, 20), Image.LANCZOS)
        self.explain_icon = ImageTk.PhotoImage(explain_img)
        translate_img = Image.open("assets/translate_icon.png").resize((20, 20), Image.LANCZOS)
        self.translate_icon = ImageTk.PhotoImage(translate_img)
        search_img = Image.open("assets/youtube_icon.png").resize((20, 20), Image.LANCZOS)
        self.search_icon = ImageTk.PhotoImage(search_img)

        ask_btn = ttk.Button(overlay_frame, image=self.ask_icon, text="Ask AI", compound=tk.LEFT, command=self.ask_ai_overlay)
        explain_btn = ttk.Button(overlay_frame, image=self.explain_icon, text="Explain", compound=tk.LEFT, command=self.explain_ai_overlay)
        translate_btn = ttk.Button(overlay_frame, image=self.translate_icon, text="Translate", compound=tk.LEFT, command=self.translate_ai_popup)
        search_btn = ttk.Button(overlay_frame, image=self.search_icon, text="Youtube Search", compound=tk.LEFT, command=self.search_ai_overlay)

        ask_btn.grid(row=0, column=0, padx=2, pady=2)
        explain_btn.grid(row=0, column=1, padx=2, pady=2)
        translate_btn.grid(row=0, column=2, padx=2, pady=2)
        search_btn.grid(row=0, column=3, padx=2, pady=2)

        self.selection_overlay = self.page_canvas.create_window(x + 5, y + 5, window=overlay_frame, anchor="nw")

    def save_image_to_tmp(self, image):
        tmp_dir = "tmp"
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        filename = "pdf_ai_tmp_image_" + ".png"
        tmp_path = os.path.join(tmp_dir, filename)
        image.save(tmp_path)
        return tmp_path

    # --- AI Overlay Functions ---
    def ask_ai_overlay(self):
        self.ask_popup = tk.Toplevel(self.root)
        self.ask_popup.title("💬 Ask AI")
        self.ask_popup.configure(bg="#E3F2FD")
        self.ask_popup.transient(self.root)
        self.ask_popup.grab_set()

        prompt_label = ttk.Label(self.ask_popup, text="Enter your question:")
        prompt_label.pack(padx=10, pady=(10, 5))

        self.ask_entry = ttk.Entry(self.ask_popup, width=50)
        self.ask_entry.pack(padx=10, pady=5)
        self.ask_entry.focus_set()

        btn_frame = ttk.Frame(self.ask_popup)
        btn_frame.pack(padx=10, pady=(5, 10))

        ask_button = ttk.Button(btn_frame, text="Submit", command=self.process_ask_ai)
        ask_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(btn_frame, text="Cancel", command=self.ask_popup.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        self.ask_popup.protocol("WM_DELETE_WINDOW", self.ask_popup.destroy)

    def process_ask_ai(self):
        question = self.ask_entry.get().strip()
        self.ask_popup.destroy()
        tmp_image_path = self.save_image_to_tmp(self.selected_cropped_image) if self.selected_cropped_image else None

        def threaded_ask():
            generator = ask_ai(question, self.page_text, tmp_image_path)
            self.root.after(1, lambda: self.show_response_popup(generator, language_code="en"))

        threading.Thread(target=threaded_ask, daemon=True).start()

    def explain_ai_overlay(self):
        tmp_image_path = self.save_image_to_tmp(self.selected_cropped_image) if self.selected_cropped_image else None

        def threaded_explain():
            generator = explain_ai(self.page_text, tmp_image_path)
            self.root.after(2, lambda: self.show_response_popup(generator, language_code="en"))

        threading.Thread(target=threaded_explain, daemon=True).start()

    def translate_ai_popup(self):
        self.translate_popup = tk.Toplevel(self.root)
        self.translate_popup.title("🌐 Translate")
        self.translate_popup.configure(bg="#E3F2FD")
        self.translate_popup.transient(self.root)
        self.translate_popup.grab_set()

        prompt_label = ttk.Label(self.translate_popup, text="Select target language:")
        prompt_label.pack(padx=10, pady=(10, 5))

        languages = ["English", "Arabic", "Spanish", "French", "German", "Chinese", "Japanese"]
        self.lang_var = tk.StringVar(value="English")
        lang_combo = ttk.Combobox(
            self.translate_popup,
            textvariable=self.lang_var,
            values=languages,
            state="readonly",
            width=15
        )
        lang_combo.pack(padx=10, pady=5)

        btn_frame = ttk.Frame(self.translate_popup)
        btn_frame.pack(padx=10, pady=(5, 10))

        submit_btn = ttk.Button(btn_frame, text="Submit", command=self.process_translate_ai)
        submit_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.translate_popup.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        self.translate_popup.protocol("WM_DELETE_WINDOW", self.translate_popup.destroy)

    def process_translate_ai(self):
        target_lang = self.lang_var.get()
        lang_mapping = {
            "English": "en",
            "Arabic": "ar",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Chinese": "zh-cn",
            "Japanese": "ja"
        }
        language_code = lang_mapping.get(target_lang, "en")
        self.translate_popup.destroy()
        tmp_image_path = self.save_image_to_tmp(self.selected_cropped_image) if self.selected_cropped_image else None

        def threaded_translate():
            generator = translate_ai(target_lang, tmp_image_path)
            self.root.after(0, lambda: self.show_response_popup(generator, language_code=language_code))

        threading.Thread(target=threaded_translate, daemon=True).start()

    def search_ai_overlay(self):
        self.search_popup = tk.Toplevel(self.root)
        self.search_popup.title("🔎 Searching YouTube")
        self.search_popup.configure(bg="#E3F2FD")
        self.search_popup.transient(self.root)
        self.search_popup.grab_set()

        waiting_label = ttk.Label(self.search_popup, text="Searching for YouTube videos, please wait...")
        waiting_label.pack(padx=10, pady=(10, 5))

        cancel_button = ttk.Button(self.search_popup, text="Cancel", command=self.search_popup.destroy)
        cancel_button.pack(pady=(0, 10))

        tmp_image_path = self.save_image_to_tmp(self.selected_cropped_image) if self.selected_cropped_image else None

        def threaded_search():
            youtube_results = search_ai(self.page_text, tmp_image_path)
            self.root.after(0, lambda: self.search_popup.destroy())
            if youtube_results:
                self.root.after(0, lambda: self.show_youtube_results_popup(youtube_results))
            else:
                response_text = "No results found."
                self.root.after(0, lambda: self.show_response_popup(iter([response_text]), language_code="en"))

        threading.Thread(target=threaded_search, daemon=True).start()

    def show_youtube_results_popup(self, results):
        popup = tk.Toplevel(self.root)
        popup.title("YouTube Search Results")
        popup.configure(bg="#F0F4FB")
        popup.geometry("800x600")  
        
        heading_label = tk.Label(
            popup,
            text="YouTube Search Results",
            font=("Arial", 16, "bold"),
            bg="#F0F4FB",
            fg="#0D47A1"
        )
        heading_label.pack(pady=10)
        
        canvas = tk.Canvas(popup, bg="#F0F4FB", highlightthickness=0)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        container = tk.Frame(canvas, bg="#F0F4FB")
        canvas.create_window((0, 0), window=container, anchor="nw")
        
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        container.bind("<Configure>", on_configure)
        
        NORMAL_BG = "white"
        HOVER_BG = "#e6f2ff"  
        
        for idx, result in enumerate(results):
            row_frame = tk.Frame(
                container,
                bg=NORMAL_BG,
                bd=1,
                relief="ridge",
                padx=10,
                pady=10
            )
            row_frame.pack(fill="x", padx=10, pady=5)
            
            def open_url(event, url=result["video_url"]):
                webbrowser.open(url)
            
            row_frame.bind("<Button-1>", open_url)
            
            def on_enter(event, frame=row_frame):
                frame.configure(bg=HOVER_BG)
                for child in frame.winfo_children():
                    child.configure(bg=HOVER_BG)
            def on_leave(event, frame=row_frame):
                frame.configure(bg=NORMAL_BG)
                for child in frame.winfo_children():
                    child.configure(bg=NORMAL_BG)
            
            row_frame.bind("<Enter>", on_enter)
            row_frame.bind("<Leave>", on_leave)
            
            title_label = tk.Label(
                row_frame,
                text=result["title"],
                font=("Arial", 14, "bold"),
                bg=NORMAL_BG,
                fg="#0D47A1",
                anchor="w"
            )
            title_label.pack(side="top", fill="x")
            
            title_label.bind("<Button-1>", open_url)
            title_label.bind("<Enter>", on_enter)
            title_label.bind("<Leave>", on_leave)

            description_label = tk.Label(
                row_frame,
                text=result["description"],
                font=("Arial", 12),
                bg=NORMAL_BG,
                fg="#0D47A1",
                wraplength=750,
                justify="left",
                anchor="w"
            )
            description_label.pack(side="top", fill="x", pady=(5, 0))
            description_label.bind("<Button-1>", open_url)
            description_label.bind("<Enter>", on_enter)
            description_label.bind("<Leave>", on_leave)

    def show_response_popup(self, response_generator, language_code="en"):
        if self.response_popup is not None and self.response_popup.winfo_exists():
            self.response_popup.destroy()

        self.response_popup = tk.Toplevel(self.root)
        self.response_popup.title("AI Response")
        self.response_popup.configure(bg="#F0F4FB")
        self.response_popup.transient(self.root)
        self.response_popup.grab_set()

        response_label = ttk.Label(self.response_popup, text="AI Response:")
        response_label.pack(padx=10, pady=(10, 5))

        response_frame = ttk.Frame(self.response_popup)
        response_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.response_area = tk.Text(
            response_frame,
            wrap=tk.WORD,
            width=60,
            height=15,
            font=("Arial", 12),
            background="white",
            foreground="#0D47A1",
            relief="flat"
        )
        self.response_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        response_scroll = ttk.Scrollbar(response_frame, orient=tk.VERTICAL, command=self.response_area.yview)
        response_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.response_area.config(yscrollcommand=response_scroll.set)

        self.current_response_text = ""
        self.response_language = language_code
        self.response_area.tag_config("arabic", font=("Arial", 12), justify="right", foreground="#0D47A1")

        btn_frame = ttk.Frame(self.response_popup)
        btn_frame.pack(pady=(5, 10))

        self.read_button = ttk.Button(btn_frame, text="🔊 Read Aloud", command=lambda: self.read_aloud_after_stream(language_code))
        self.read_button.pack(side=tk.LEFT, padx=5)

        close_button = ttk.Button(btn_frame, text="Close", command=self.close_response_popup)
        close_button.pack(side=tk.LEFT, padx=5)

        def on_text_mousewheel(event):
            if event.delta:
                event.widget.yview_scroll(-int(event.delta / 120), "units")
            else:
                if event.num == 4:
                    event.widget.yview_scroll(-1, "units")
                elif event.num == 5:
                    event.widget.yview_scroll(1, "units")
            return "break"

        self.response_area.bind("<MouseWheel>", on_text_mousewheel)
        self.response_area.bind("<Button-4>", on_text_mousewheel)
        self.response_area.bind("<Button-5>", on_text_mousewheel)

        self.response_popup.protocol("WM_DELETE_WINDOW", self.close_response_popup)

        self.streaming_in_progress = True
        threading.Thread(target=self._stream_response_thread, args=(response_generator,), daemon=True).start()

    def _stream_response_thread(self, generator):
        try:
            for chunk in generator:
                self.current_response_text += chunk
                self.root.after(0, self._update_response_area)
        except StopIteration:
            pass
        finally:
            self.streaming_in_progress = False

    def _update_response_area(self):
        self.response_area.config(state=tk.NORMAL)
        self.response_area.delete("1.0", tk.END)

        if self.response_language == "ar":
            reshaped_text = arabic_reshaper.reshape(self.current_response_text)
            display_text = "\u202E" + get_display(reshaped_text) + "\u202C"
            self.response_area.insert(tk.END, display_text, "arabic")
        else:
            self.response_area.insert(tk.END, self.current_response_text)

        self.response_area.config(state=tk.DISABLED)

    # --- Streaming TTS for Read Aloud ---
    def read_aloud_after_stream(self, language_code):
        if self.tts_streaming:
            return
        self.tts_streaming = True
        self.read_button.config(text="Generating Audio...")
        self.tts_read_index = 0
        threading.Thread(target=self.stream_read_aloud, args=(language_code,), daemon=True).start()

    def stream_read_aloud(self, language_code):
        while True:
            new_text = self.current_response_text[self.tts_read_index:]
            if new_text:
                try:
                    tts = gTTS(text=new_text, lang=language_code)
                    temp_file = f"temp_audio_{self.tts_read_index}.mp3"
                    tts.save(temp_file)
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                    pygame.mixer.music.load(temp_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                    os.remove(temp_file)
                    self.tts_read_index = len(self.current_response_text)
                except Exception as e:
                    print("TTS error:", e)
                    break
            else:
                if not self.streaming_in_progress:
                    break
                pygame.time.wait(200)

        self.tts_streaming = False
        self.read_button.config(text="🔊 Read Aloud")

    def read_aloud(self, text, language_code):
        try:
            tts = gTTS(text=text, lang=language_code)
            temp_file = "temp_audio.mp3"
            tts.save(temp_file)
            self.current_audio_file = temp_file
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play audio:\n{e}")

    def close_response_popup(self):
        try:
            pygame.mixer.music.stop()
            if self.current_audio_file and os.path.exists(self.current_audio_file):
                os.remove(self.current_audio_file)
                self.current_audio_file = None
        except Exception:
            pass

        if self.response_popup and self.response_popup.winfo_exists():
            self.response_popup.destroy()

    def process_ai_chat_message(self):
        message = self.chat_input.get("1.0", tk.END).strip()
        if message:
            self.append_chat_message("You", message)
            self.chat_input.delete("1.0", tk.END)
            ai_label = self.append_chat_message("AI", "")
            threading.Thread(target=self._process_chat_ai, args=(message, ai_label), daemon=True).start()

    def _process_chat_ai(self, message, ai_label):
        try:
            generator = chat_ai(message)
            partial_text = ""
            for chunk in generator:
                partial_text += chunk
                self.root.after(0, lambda pt=partial_text: ai_label.config(text=pt))
        except Exception as e:
            self.root.after(1, lambda: ai_label.config(text="Error: " + str(e)))

    def append_chat_message(self, sender, message):
        self.chat_log.config(state=tk.NORMAL)
        bubble_color = "#DCEFFF" if sender == "You" else "#EAEAEA"
        bubble_frame = tk.Frame(self.chat_log, bg=bubble_color, bd=0, highlightthickness=0)
        bubble_label = tk.Label(
            bubble_frame,
            text=message,
            bg=bubble_color,
            fg="black",
            font=("Segoe UI", 10),
            wraplength=260,
            justify="left"
        )
        bubble_label.pack(padx=10, pady=2)

        self.chat_log.insert(tk.END, "\n")
        self.chat_log.window_create(tk.END, window=bubble_frame, padx=10, pady=2)
        self.chat_log.insert(tk.END, "\n")
        self.chat_log.see(tk.END)
        self.chat_log.config(state=tk.DISABLED)
        return bubble_label

    def start_voice_command(self):
        """
        Opens a 300×500 popup over the current window (useful for multi-monitor setups).
        Displays:
        - A microphone icon (optional) at the top.
        - "Recording XXX" label & a timer label.
        - A waveform canvas in the middle that reflects actual mic amplitude.
        - A 'Stop' button styled like the rest of your app.
        """
        # Keep track of how many recordings the user has made (optional).
        if not hasattr(self, "record_count"):
            self.record_count = 1
        else:
            self.record_count += 1

        # Create the popup
        self.voice_command_popup = tk.Toplevel(self.root)
        self.voice_command_popup.title("Voice Recorder")
        # We'll set a fixed size of 300x500 for demonstration:
        win_width, win_height = 300, 500

        # Center it over the main window, rather than the entire screen
        parent_x = self.root.winfo_rootx()
        parent_y = self.root.winfo_rooty()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()

        # Calculate center coordinates relative to the parent window
        x = parent_x + (parent_width // 2) - (win_width // 2)
        y = parent_y + (parent_height // 2) - (win_height // 2)
        self.voice_command_popup.geometry(f"{win_width}x{win_height}+{x}+{y}")

        # Match your existing color scheme
        self.voice_command_popup.configure(bg="#E3F2FD")
        self.voice_command_popup.transient(self.root)
        self.voice_command_popup.grab_set()

        # Optional: load a microphone icon (pink or any color you like).
        # Make sure you have an image file "mic_icon.png" in your assets folder.
        # If not found, it will just skip and show text fallback.
        try:
            mic_icon = load_icon("record_icon.png", size=(64, 64))
            self.mic_label = tk.Label(self.voice_command_popup, image=mic_icon, bg="#E3F2FD")
            self.mic_label.image = mic_icon  # keep a reference
            self.mic_label.pack(pady=(20, 10))
        except:
            self.mic_label = tk.Label(self.voice_command_popup, text="🎤", font=("Helvetica", 40), bg="#E3F2FD")
            self.mic_label.pack(pady=(20, 10))

        # "Recording XXX" label
        recording_title = f"Recording {self.record_count:03d}"
        self.recording_label = tk.Label(
            self.voice_command_popup, 
            text=recording_title,
            font=("Helvetica", 14, "bold"),
            fg="#0D47A1",
            bg="#E3F2FD"
        )
        self.recording_label.pack()

        # Timer label
        self.record_time_label = tk.Label(
            self.voice_command_popup, 
            text="0:00", 
            font=("Helvetica", 12),
            fg="#0D47A1",
            bg="#E3F2FD"
        )
        self.record_time_label.pack(pady=(0, 20))

        # Waveform canvas
        self.wave_canvas_width = 250
        self.wave_canvas_height = 100
        self.wave_canvas = tk.Canvas(
            self.voice_command_popup, 
            width=self.wave_canvas_width,
            height=self.wave_canvas_height,
            bg="#E3F2FD",       # match your app background
            highlightthickness=0
        )
        self.wave_canvas.pack(pady=10)

        # "Stop" button in your style
        # If you have a ttk style named "RoundedButton.TButton", use that.
        # Otherwise, just use a normal tk.Button with your color scheme.
        self.stop_button = ttk.Button(
            self.voice_command_popup,
            text="Stop",
            style="RoundedButton.TButton",  # if your style is defined
            command=self.stop_voice_recording
        )
        self.stop_button.pack(pady=20)

        # Initialize recording variables
        self.recording = True
        self.audio_frames = []
        self.current_amplitude = 0
        self.wave_data = [0]*50  # keep 50 amplitude values for scrolling
        self.record_start_time = time.time()

        # Start audio capture in a background thread
        threading.Thread(target=self.record_audio, daemon=True).start()

        # Start periodic UI updates: waveform + timer
        self.update_waveform()
        self.update_record_time()

    def record_audio(self):
        """Capture real audio from the mic, compute amplitude, and store frames."""
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024

        p = pyaudio.PyAudio()
        self.pyaudio_instance = p

        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        while self.recording:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
            except:
                continue
            self.audio_frames.append(data)

            # Convert raw bytes to NumPy array for amplitude analysis
            audio_data = np.frombuffer(data, dtype=np.int16)
            max_amp = np.abs(audio_data).max()
            # Normalize amplitude between 0.0 and 1.0
            self.current_amplitude = max_amp / 32768.0

        # Cleanup once recording stops
        stream.stop_stream()
        stream.close()
        p.terminate()

    def update_waveform(self):
        """Periodically update the waveform by adding the latest amplitude
        and re-drawing it as vertical bars on the canvas."""
        if self.recording:
            # Shift old values left, append new amplitude
            self.wave_data.pop(0)
            self.wave_data.append(self.current_amplitude)

        # Clear the canvas
        self.wave_canvas.delete("all")

        # Draw each amplitude as a vertical bar
        bar_width = self.wave_canvas_width / len(self.wave_data)
        center_y = self.wave_canvas_height // 2
        for i, amp in enumerate(self.wave_data):
            # Scale amplitude to half the canvas height
            bar_height = int(amp * (self.wave_canvas_height // 2))
            x1 = i * bar_width
            x2 = x1 + (bar_width * 0.8)  # small gap
            y1 = center_y - bar_height
            y2 = center_y + bar_height
            # Use your brand color (e.g., #2196F3 or #1976D2) for the bars
            self.wave_canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="#2196F3",  # Blue color
                outline=""
            )

        # Schedule next update in 100 ms
        if self.recording:
            self.voice_command_popup.after(100, self.update_waveform)

    def update_record_time(self):
        """Update the recording timer (MM:SS) every second."""
        if self.recording:
            elapsed = int(time.time() - self.record_start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.record_time_label.config(text=f"{minutes}:{seconds:02d}")
            self.voice_command_popup.after(1000, self.update_record_time)

    def stop_voice_recording(self):
        """Stop the recording and schedule the 'processing' step."""
        if self.recording:
            self.recording = False
            self.recording_label.config(text="Stopping...")
            self.stop_button.config(state=tk.DISABLED)

            # Give a moment for record_audio loop to exit
            self.root.after(1000, self.process_voice_command)

    def process_voice_command(self):
        """
        For now, DO NOT SAVE the audio (commented out).
        Just show a messagebox with a dummy result.
        Uncomment the lines if/when you install ffmpeg and want to save audio.
        """

        

        filename_wav = f"tmp/recorded_audio_.wav"
        p = self.pyaudio_instance
        wf = wave.open(filename_wav, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()

        result = self.dummy_voice_ai(None)
        messagebox.showinfo("Voice Command Result", result)

        # Close the popup
        self.voice_command_popup.destroy()

    def dummy_voice_ai(self, audio_path):
        """Dummy AI function that just returns a fixed message for now."""
        return "hello from AI"



if __name__ == "__main__":
    root = tk.Tk()
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    
    viewer = PDFViewer(root)
    root.mainloop()
