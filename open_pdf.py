import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io
from gtts import gTTS
import os
import pygame

pygame.mixer.init()


def dummy_ask_ai(question, full_page_text, region_image):
    return f"Dummy AI Answer: Your question '{question}' was processed."

def dummy_explain_ai(full_page_text, region_image):
    return "Dummy Explanation: This region appears to show sample content for explanation."

def dummy_translate_ai(full_page_text, region_image, target_language):
    return f"Dummy Translation: The content has been translated into {target_language}."

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Blue PDF Viewer with AI")
        self.root.configure(bg="#E3F2FD")
        self.doc = None
        self.current_page = 0
        self.num_pages = 0

        # Variables to store the rendered image and full page text.
        self.current_pil_image = None
        self.page_text = ""
        self.page_image_tk = None

        # Popups.
        self.ai_popup = None
        self.response_popup = None

        # Selection variables.
        self.sel_rect = None
        self.sel_start = None
        self.selection_overlay = None  # Overlay for action buttons.
        self.selected_cropped_image = None  # The cropped image from selection.

        # Audio playback variables.
        self.current_audio_file = None

        # Zoom factor.
        self.zoom = 1.5

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        # General blue-themed styles.
        style.configure("TFrame", background="#E3F2FD")
        style.configure("TLabel", background="#E3F2FD", foreground="#0D47A1", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10, "bold"), padding=4)
        style.map("TButton",
                  background=[("active", "#1976D2"), ("!active", "#2196F3")],
                  foreground=[("active", "white"), ("!active", "white")])
        # Scrollbars.
        style.configure("Vertical.TScrollbar", gripcount=0,
                        background="#BBDEFB", darkcolor="#90CAF9", lightcolor="#E3F2FD",
                        troughcolor="#E3F2FD", bordercolor="#E3F2FD", arrowcolor="#0D47A1")
        style.configure("Horizontal.TScrollbar", gripcount=0,
                        background="#BBDEFB", darkcolor="#90CAF9", lightcolor="#E3F2FD",
                        troughcolor="#E3F2FD", bordercolor="#E3F2FD", arrowcolor="#0D47A1")
        # Style for the selection overlay frame.
        style.configure("Overlay.TFrame", background="#BBDEFB", relief="raised", borderwidth=1)

    def create_widgets(self):
        # Toolbar.
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        open_btn = ttk.Button(toolbar, text="Open PDF", command=self.open_pdf)
        open_btn.pack(side=tk.LEFT, padx=4)

        self.prev_btn = ttk.Button(toolbar, text="Previous Page", 
                                   command=lambda: self.change_page("prev", "bottom"), state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=4)
        self.next_btn = ttk.Button(toolbar, text="Next Page", 
                                   command=lambda: self.change_page("next", "top"), state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=4)
        self.page_label = ttk.Label(toolbar, text="Page: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)

        # Canvas and scrollbars.
        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.page_canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.page_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.page_canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,2))
        self.h_scroll = ttk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.page_canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0,5))
        self.page_canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        # Global mouse wheel bindings.
        self.root.bind_all("<MouseWheel>", self.on_mouse_wheel)   # Windows/macOS.
        self.root.bind_all("<Button-4>", self.on_mouse_wheel)     # Linux scroll up.
        self.root.bind_all("<Button-5>", self.on_mouse_wheel)     # Linux scroll down.
        self.page_canvas.bind("<Enter>", lambda e: self.page_canvas.focus_set())

        # Bind selection events.
        self.page_canvas.bind("<Button-1>", self.on_canvas_mouse_down)
        self.page_canvas.bind("<B1-Motion>", self.on_canvas_mouse_drag)
        self.page_canvas.bind("<ButtonRelease-1>", self.on_canvas_mouse_up)

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
            delta = -1 if event.num == 4 else 1 if event.num == 5 else 0
        else:
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
        # Use fill="" to keep the selection transparent.
        self.sel_rect = self.draw_rounded_rectangle(x0, y0, x1, y1, r=10,
                                                      fill="", outline="#1E90FF", width=3)

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
            # Leave the selection box transparent (only an outline) and show overlay.
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
        result = dummy_ask_ai(question, self.page_text, self.selected_cropped_image)
        self.show_response_popup(result, language_code="en")

    def explain_ai_overlay(self):
        result = dummy_explain_ai(self.page_text, self.selected_cropped_image)
        self.show_response_popup(result, language_code="en")

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
        lang_combo = ttk.Combobox(self.translate_popup, textvariable=self.lang_var, 
                                  values=languages, state="readonly", width=15)
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
        result = dummy_translate_ai(self.page_text, self.selected_cropped_image, target_lang)
        self.show_response_popup(result, language_code=language_code)

    def show_response_popup(self, response, language_code="en"):
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
        response_area = tk.Text(response_frame, wrap=tk.WORD, width=60, height=15,
                                font=("Helvetica", 12), background="white", foreground="#0D47A1", relief="flat")
        response_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        response_scroll = ttk.Scrollbar(response_frame, orient=tk.VERTICAL, command=response_area.yview)
        response_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        response_area.config(yscrollcommand=response_scroll.set)
        response_area.insert(tk.END, response)
        response_area.config(state=tk.DISABLED)
        # Create a horizontal button frame for Read Aloud and Close.
        btn_frame = ttk.Frame(self.response_popup)
        btn_frame.pack(pady=(5,10))
        read_button = ttk.Button(btn_frame, text="🔊 Read Aloud", 
                                  command=lambda: self.read_aloud(response, language_code))
        close_button = ttk.Button(btn_frame, text="Close", command=self.close_response_popup)
        read_button.pack(side=tk.LEFT, padx=5)
        close_button.pack(side=tk.LEFT, padx=5)
        # Bind mouse wheel events for the text widget.
        def on_text_mousewheel(event):
            if event.delta:
                event.widget.yview_scroll(-int(event.delta/120), "units")
            else:
                if event.num == 4:
                    event.widget.yview_scroll(-1, "units")
                elif event.num == 5:
                    event.widget.yview_scroll(1, "units")
            return "break"
        response_area.bind("<MouseWheel>", on_text_mousewheel)
        response_area.bind("<Button-4>", on_text_mousewheel)
        response_area.bind("<Button-5>", on_text_mousewheel)
        self.response_popup.protocol("WM_DELETE_WINDOW", self.close_response_popup)

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
        except Exception as e:
            pass
        self.response_popup.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1024x768")
    viewer = PDFViewer(root)
    root.mainloop()
