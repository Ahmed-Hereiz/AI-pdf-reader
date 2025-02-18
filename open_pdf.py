import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io
from gtts import gTTS
import os
import pygame
import uuid

import arabic_reshaper
from bidi.algorithm import get_display
from call_ai import ask_ai, explain_ai, translate_ai, chat_ai

pygame.mixer.init()


class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Viewer with AI")
        self.root.configure(bg="#E3F2FD")

        self.doc = None
        self.current_page = 0
        self.num_pages = 0

        # Variables to store the rendered image and full page text
        self.current_pil_image = None
        self.page_text = ""
        self.page_image_tk = None

        # Popups
        self.ai_popup = None
        self.response_popup = None

        # Selection variables
        self.sel_rect = None
        self.sel_start = None
        self.selection_overlay = None
        self.selected_cropped_image = None

        # Audio playback variables
        self.current_audio_file = None

        # Zoom factor
        self.zoom = 1.5

        # Chat panel state
        self.chat_open = False
        self.chat_target_width = 350  # Extended chat width
        self.current_chat_width = 0

        # Emoji icons for open/close toggle
        self.chat_open_icon = "Chat with AI"
        self.chat_close_icon = "❌"

        # For TTS and partial streaming
        self.current_response_text = ""
        self.response_language = "en"

        # Flag to track if streaming is in progress
        self.streaming_in_progress = False

        # Reference to the "Read Aloud" button for updating text while waiting
        self.read_button = None

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # General blue-themed styles
        style.configure("TFrame", background="#E3F2FD")
        style.configure("TLabel", background="#E3F2FD", foreground="#0D47A1", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10, "bold"), padding=4)
        style.map(
            "TButton",
            background=[("active", "#1976D2"), ("!active", "#2196F3")],
            foreground=[("active", "white"), ("!active", "white")]
        )

        # Scrollbars
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

        # Selection overlay frame
        style.configure("Overlay.TFrame", background="#BBDEFB", relief="raised", borderwidth=1)

        # Chat panel
        style.configure("Chat.TFrame", background="#F7F7F7")

    def create_widgets(self):
        # Toolbar
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        open_btn = ttk.Button(toolbar, text="Open PDF", command=self.open_pdf)
        open_btn.pack(side=tk.LEFT, padx=4)

        self.prev_btn = ttk.Button(
            toolbar,
            text="Previous Page",
            command=lambda: self.change_page("prev", "bottom"),
            state=tk.DISABLED
        )
        self.prev_btn.pack(side=tk.LEFT, padx=4)

        self.next_btn = ttk.Button(
            toolbar,
            text="Next Page",
            command=lambda: self.change_page("next", "top"),
            state=tk.DISABLED
        )
        self.next_btn.pack(side=tk.LEFT, padx=4)

        self.page_label = ttk.Label(toolbar, text="Page: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)

        # Main container frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame: PDF viewer
        self.viewer_frame = ttk.Frame(self.main_frame)
        self.viewer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Canvas and scrollbars for PDF viewer
        self.canvas_frame = ttk.Frame(self.viewer_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.page_canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.page_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.page_canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 2))

        self.h_scroll = ttk.Scrollbar(self.viewer_frame, orient=tk.HORIZONTAL, command=self.page_canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))

        self.page_canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        # Global mouse wheel bindings
        self.root.bind_all("<MouseWheel>", self.on_mouse_wheel)   # Windows/macOS
        self.root.bind_all("<Button-4>", self.on_mouse_wheel)     # Linux scroll up
        self.root.bind_all("<Button-5>", self.on_mouse_wheel)     # Linux scroll down
        self.page_canvas.bind("<Enter>", lambda e: self.page_canvas.focus_set())

        # Bind selection events
        self.page_canvas.bind("<Button-1>", self.on_canvas_mouse_down)
        self.page_canvas.bind("<B1-Motion>", self.on_canvas_mouse_drag)
        self.page_canvas.bind("<ButtonRelease-1>", self.on_canvas_mouse_up)

        # Right frame: AI Chat panel (initially hidden with width=0)
        self.chat_frame = ttk.Frame(self.main_frame, style="Chat.TFrame", width=0)
        self.chat_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_frame.pack_propagate(False)  # Prevent auto resizing
        self.setup_ai_chat()

        # Toggle chat button at top right
        self.toggle_button = ttk.Button(
            self.main_frame,
            text=self.chat_open_icon,
            command=self.toggle_chat
        )
        self.toggle_button.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)

    def setup_ai_chat(self):
        """Configure the chat panel UI: title, chat log area, multiline input."""
        self.chat_frame.configure(padding=10)

        # Title bar
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

        # Chat log area
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

        # Input row for multiline text + send button
        chat_input_frame = ttk.Frame(self.chat_frame)
        chat_input_frame.pack(fill=tk.X, padx=5, pady=(5, 5))

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
        """
        Pressing Enter sends the message.
        Pressing Shift+Enter inserts a newline.
        """
        if event.state & 0x0001:  # Shift key pressed
            return None
        else:
            self.process_ai_chat_message()
            return "break"

    # --- Chat Toggle & Animation ---
    def toggle_chat(self):
        if self.chat_open:
            self.animate_chat_close()
            self.toggle_button.config(text=self.chat_open_icon)
            self.chat_open = False
        else:
            self.animate_chat_open()
            self.toggle_button.config(text=self.chat_close_icon)
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

    # --- PDF Functions ---
    def open_pdf(self):
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if pdf_path:
            try:
                self.doc = fitz.open(pdf_path)
                self.num_pages = self.doc.page_count
                self.current_page = 0
                self.update_navigation_buttons()
                self.display_page(self.current_page, scroll_position="top")
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
            # Linux scroll
            delta = -1 if event.num == 4 else 1 if event.num == 5 else 0
        else:
            # Windows/macOS scroll
            delta = -int(event.delta / 120)
        first, last = self.page_canvas.yview()
        if delta > 0 and last >= 0.999:
            if self.current_page < self.num_pages - 1:
                self.change_page("next", scroll_position="top")
                return "break"
        elif delta < 0 and first <= 0.001:
            if self.current_page > 0:
                self.change_page("prev", scroll_position="bottom")
                return "break"
        self.page_canvas.yview_scroll(delta, "units")
        return "break"

    # --- Selection & Overlay ---
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
        crop_left = x0 - ox
        crop_top = y0 - oy
        crop_right = x1 - ox
        crop_bottom = y1 - oy
        img_width, img_height = self.current_pil_image.size

        crop_left = max(0, min(img_width, crop_left))
        crop_right = max(0, min(img_width, crop_right))
        crop_top = max(0, min(img_height, crop_top))
        crop_bottom = max(0, min(img_height, crop_bottom))
        if crop_right <= crop_left or crop_bottom <= crop_top:
            return None
        return self.current_pil_image.crop((crop_left, crop_top, crop_right, crop_bottom))

    def show_selection_overlay(self, x, y, cropped_image):
        self.selected_cropped_image = cropped_image
        if self.selection_overlay is not None:
            self.page_canvas.delete(self.selection_overlay)
            self.selection_overlay = None
        overlay_frame = ttk.Frame(self.page_canvas, style="Overlay.TFrame")

        ask_btn = ttk.Button(overlay_frame, text="💬 Ask AI", command=self.ask_ai_overlay)
        explain_btn = ttk.Button(overlay_frame, text="💡 Explain", command=self.explain_ai_overlay)
        translate_btn = ttk.Button(overlay_frame, text="🌐 Translate", command=self.translate_ai_popup)

        ask_btn.grid(row=0, column=0, padx=2, pady=2)
        explain_btn.grid(row=0, column=1, padx=2, pady=2)
        translate_btn.grid(row=0, column=2, padx=2, pady=2)

        self.selection_overlay = self.page_canvas.create_window(x + 5, y + 5, window=overlay_frame, anchor="nw")

    # --- Helper: Save image to tmp dir ---
    def save_image_to_tmp(self, image):
        tmp_dir = "tmp"
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        filename = "pdf_ai_tmp_image_" + str(uuid.uuid4()) + ".png"
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

        if self.selected_cropped_image:
            tmp_image_path = self.save_image_to_tmp(self.selected_cropped_image)
        else:
            tmp_image_path = None

        generator = ask_ai(question, self.page_text, tmp_image_path)
        self.show_response_popup(generator, language_code="en")

    def explain_ai_overlay(self):
        if self.selected_cropped_image:
            tmp_image_path = self.save_image_to_tmp(self.selected_cropped_image)
        else:
            tmp_image_path = None

        generator = explain_ai(self.page_text, tmp_image_path)
        self.show_response_popup(generator, language_code="en")

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

        if self.selected_cropped_image:
            tmp_image_path = self.save_image_to_tmp(self.selected_cropped_image)
        else:
            tmp_image_path = None

        generator = translate_ai(target_lang, tmp_image_path)
        self.show_response_popup(generator, language_code=language_code)

    def show_response_popup(self, response_generator, language_code="en"):
        """
        Display streaming response in a popup.
        'response_generator' is a generator that yields text chunks.
        """
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

        # Use Arial (or any Arabic-capable font) to handle Arabic scripts better
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

        # We'll store the accumulated text so "Read Aloud" can speak the entire text
        self.current_response_text = ""
        self.response_language = language_code

        # Tag for Arabic: right aligned, using a font that supports Arabic
        self.response_area.tag_config(
            "arabic",
            font=("Arial", 12),
            justify="right",
            foreground="#0D47A1"
        )

        # Buttons (Read Aloud, Close)
        btn_frame = ttk.Frame(self.response_popup)
        btn_frame.pack(pady=(5, 10))

        # Create and store the read_button reference
        self.read_button = ttk.Button(
            btn_frame,
            text="🔊 Read Aloud",
            command=lambda: self.read_aloud_after_stream(self.current_response_text, language_code)
        )
        self.read_button.pack(side=tk.LEFT, padx=5)

        close_button = ttk.Button(btn_frame, text="Close", command=self.close_response_popup)
        close_button.pack(side=tk.LEFT, padx=5)

        # Mouse wheel scrolling
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

        # Set flag to indicate streaming is starting
        self.streaming_in_progress = True
        # Start streaming
        self.stream_response(response_generator)

    def stream_response(self, generator):
        """
        Reads the next chunk from 'generator' and appends it to the response_area.
        Schedules itself via after() until generator is exhausted.
        """
        try:
            chunk = next(generator)
            self.current_response_text += chunk

            # Clear the text area and re-insert the updated text
            self.response_area.config(state=tk.NORMAL)
            self.response_area.delete("1.0", tk.END)

            if self.response_language == "ar":
                # Reshape and apply bidi conversion
                reshaped_text = arabic_reshaper.reshape(self.current_response_text)
                # Use RTL override marker instead of embedding/reversing lines
                display_text = "\u202E" + get_display(reshaped_text) + "\u202C"
                self.response_area.insert(tk.END, display_text, "arabic")
            else:
                self.response_area.insert(tk.END, self.current_response_text)

            self.response_area.config(state=tk.DISABLED)

            # Schedule next chunk
            self.response_popup.after(1, lambda: self.stream_response(generator))
        except StopIteration:
            # Streaming is complete; unset the flag.
            self.streaming_in_progress = False


    # --- TTS ---
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

    def read_aloud_after_stream(self, text, language_code):
        """
        If streaming is still in progress, update the button to show a loading message.
        Once streaming is complete, revert the button and play the audio.
        """
        if self.streaming_in_progress:
            if self.read_button:
                self.read_button.config(text="Generating...")
            self.response_popup.after(100, lambda: self.read_aloud_after_stream(text, language_code))
        else:
            if self.read_button:
                self.read_button.config(text="🔊 Read Aloud")
            self.read_aloud(text, language_code)

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

    # --- AI Chat Functions ---
    def process_ai_chat_message(self):
        """
        Takes the user's input, displays it, then streams the AI response chunk-by-chunk.
        """
        message = self.chat_input.get("1.0", tk.END).strip()
        if message:
            # 1) Show user's message
            self.append_chat_message("You", message)
            # 2) Clear the input
            self.chat_input.delete("1.0", tk.END)
            # 3) Stream from chat_ai
            generator = chat_ai(message)
            # 4) Create an empty bubble for AI
            ai_label = self.append_chat_message("AI", "")
            # 5) Stream the AI response into that bubble
            self.stream_chat_response(generator, ai_label)

    def append_chat_message(self, sender, message):
        self.chat_log.config(state=tk.NORMAL)

        if sender == "You":
            bubble_color = "#DCEFFF"
        else:
            bubble_color = "#EAEAEA"

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
        self.chat_log.window_create(
            tk.END,
            window=bubble_frame,
            padx=10,
            pady=2
        )
        self.chat_log.insert(tk.END, "\n")

        self.chat_log.see(tk.END)
        self.chat_log.config(state=tk.DISABLED)

        return bubble_label

    def stream_chat_response(self, generator, bubble_label, partial_text=""):
        try:
            chunk = next(generator)
            partial_text += chunk
            bubble_label.config(text=partial_text)
            self.chat_log.see(tk.END)
            self.root.after(1, self.stream_chat_response, generator, bubble_label, partial_text)
        except StopIteration:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1024x768")
    viewer = PDFViewer(root)
    root.mainloop()
