import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import webbrowser
import time
import os
import pygame
from gtts import gTTS
import arabic_reshaper
from bidi.algorithm import get_display
import pyaudio
import wave
import numpy as np
import markdown

from call_ai import ask_ai, explain_ai, translate_ai, chat_ai, notes_ai, search_ai
from helpers import load_icon

pygame.mixer.init()

class AIOverlay:
    def __init__(self, root, pdf_handler):
        self.root = root
        self.pdf_handler = pdf_handler
        # Set the selection callback so that when a region is selected, we can show our AI options
        self.pdf_handler.selection_callback = self.handle_selection
        self.selection_overlay_id = None
        self.selected_cropped_image = None
        self.setup_chat_panel()

        # Variables for response popup and TTS
        self.response_popup = None
        self.current_response_text = ""
        self.streaming_in_progress = False
        self.tts_streaming = False
        self.tts_read_index = 0
        self.current_audio_file = None

    def handle_selection(self, x, y, cropped_image):
        # When a selection is made in the PDF, show an overlay with AI options.
        self.selected_cropped_image = cropped_image
        canvas = self.pdf_handler.page_canvas
        if self.selection_overlay_id:
            canvas.delete(self.selection_overlay_id)
        overlay_frame = ttk.Frame(canvas, style="Overlay.TFrame")
        ask_icon_img = Image.open("assets/ask_icon.png").resize((20, 20), Image.LANCZOS)
        self.ask_icon = ImageTk.PhotoImage(ask_icon_img)
        explain_icon_img = Image.open("assets/explain_icon.png").resize((20, 20), Image.LANCZOS)
        self.explain_icon = ImageTk.PhotoImage(explain_icon_img)
        translate_icon_img = Image.open("assets/translate_icon.png").resize((20, 20), Image.LANCZOS)
        self.translate_icon = ImageTk.PhotoImage(translate_icon_img)
        search_icon_img = Image.open("assets/youtube_icon.png").resize((20, 20), Image.LANCZOS)
        self.search_icon = ImageTk.PhotoImage(search_icon_img)

        ask_btn = ttk.Button(overlay_frame, image=self.ask_icon, text="Ask AI", compound=tk.LEFT, command=self.ask_ai_overlay)
        explain_btn = ttk.Button(overlay_frame, image=self.explain_icon, text="Explain", compound=tk.LEFT, command=self.explain_ai_overlay)
        translate_btn = ttk.Button(overlay_frame, image=self.translate_icon, text="Translate", compound=tk.LEFT, command=self.translate_ai_popup)
        search_btn = ttk.Button(overlay_frame, image=self.search_icon, text="Youtube Search", compound=tk.LEFT, command=self.search_ai_overlay)

        ask_btn.grid(row=0, column=0, padx=2, pady=2)
        explain_btn.grid(row=0, column=1, padx=2, pady=2)
        translate_btn.grid(row=0, column=2, padx=2, pady=2)
        search_btn.grid(row=0, column=3, padx=2, pady=2)

        self.selection_overlay_id = canvas.create_window(x+5, y+5, window=overlay_frame, anchor="nw")

    def ask_ai_overlay(self):
        self.ask_popup = tk.Toplevel(self.root)
        self.ask_popup.title("💬 Ask AI")
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
            generator = ask_ai(question, self.pdf_handler.page_text, tmp_image_path)
            self.root.after(1, lambda: self.show_response_popup(generator, language_code="en"))
        threading.Thread(target=threaded_ask, daemon=True).start()

    def explain_ai_overlay(self):
        tmp_image_path = self.save_image_to_tmp(self.selected_cropped_image) if self.selected_cropped_image else None
        def threaded_explain():
            generator = explain_ai(self.pdf_handler.page_text, tmp_image_path)
            self.root.after(2, lambda: self.show_response_popup(generator, language_code="en"))
        threading.Thread(target=threaded_explain, daemon=True).start()

    def translate_ai_popup(self):
        self.translate_popup = tk.Toplevel(self.root)
        self.translate_popup.title("🌐 Translate")
        self.translate_popup.transient(self.root)
        self.translate_popup.grab_set()
        prompt_label = ttk.Label(self.translate_popup, text="Select target language:")
        prompt_label.pack(padx=10, pady=(10, 5))
        languages = ["English", "Arabic", "Spanish", "French", "German", "Chinese", "Japanese"]
        self.lang_var = tk.StringVar(value="English")
        lang_combo = ttk.Combobox(self.translate_popup, textvariable=self.lang_var, values=languages, state="readonly", width=15)
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
        lang_mapping = {"English": "en", "Arabic": "ar", "Spanish": "es", "French": "fr", "German": "de", "Chinese": "zh-cn", "Japanese": "ja"}
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
        self.search_popup.transient(self.root)
        self.search_popup.grab_set()
        waiting_label = ttk.Label(self.search_popup, text="Searching for YouTube videos, please wait...")
        waiting_label.pack(padx=10, pady=(10, 5))
        cancel_button = ttk.Button(self.search_popup, text="Cancel", command=self.search_popup.destroy)
        cancel_button.pack(pady=(0, 10))
        tmp_image_path = self.save_image_to_tmp(self.selected_cropped_image) if self.selected_cropped_image else None
        def threaded_search():
            youtube_results = search_ai(self.pdf_handler.page_text, tmp_image_path)
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
        popup.geometry("800x600")
        canvas = tk.Canvas(popup, bg="white")
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        container = tk.Frame(canvas, bg="white")
        canvas.create_window((0,0), window=container, anchor="nw")
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        container.bind("<Configure>", on_configure)
        NORMAL_BG = "white"
        HOVER_BG = "#e6f2ff"
        for result in results:
            row_frame = tk.Frame(container, bg=NORMAL_BG, bd=1, relief="ridge", padx=10, pady=10)
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
            title_label = tk.Label(row_frame, text=result["title"], font=("Arial", 14, "bold"), bg=NORMAL_BG, anchor="w")
            title_label.pack(side="top", fill="x")
            title_label.bind("<Button-1>", open_url)
            title_label.bind("<Enter>", on_enter)
            title_label.bind("<Leave>", on_leave)
            description_label = tk.Label(row_frame, text=result["description"], font=("Arial", 12), bg=NORMAL_BG, wraplength=750, justify="left", anchor="w")
            description_label.pack(side="top", fill="x", pady=(5,0))
            description_label.bind("<Button-1>", open_url)
            description_label.bind("<Enter>", on_enter)
            description_label.bind("<Leave>", on_leave)

    def show_response_popup(self, response_generator, language_code="en"):
        if self.response_popup and self.response_popup.winfo_exists():
            self.response_popup.destroy()
        self.response_popup = tk.Toplevel(self.root)
        self.response_popup.title("AI Response")
        response_label = ttk.Label(self.response_popup, text="AI Response:")
        response_label.pack(padx=10, pady=(10, 5))
        response_frame = ttk.Frame(self.response_popup)
        response_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.response_area = tk.Text(response_frame, wrap="word", width=60, height=15, font=("Arial", 12), bg="white")
        self.response_area.pack(side=tk.LEFT, fill="both", expand=True)
        response_scroll = ttk.Scrollbar(response_frame, orient="vertical", command=self.response_area.yview)
        response_scroll.pack(side=tk.RIGHT, fill="y")
        self.response_area.config(yscrollcommand=response_scroll.set)
        self.current_response_text = ""
        self.response_area.tag_config("arabic", font=("Arial", 12), justify="right")
        btn_frame = ttk.Frame(self.response_popup)
        btn_frame.pack(pady=(5,10))
        self.read_button = ttk.Button(btn_frame, text="🔊 Read Aloud", command=lambda: self.read_aloud_after_stream(language_code))
        self.read_button.pack(side=tk.LEFT, padx=5)
        close_button = ttk.Button(btn_frame, text="Close", command=self.close_response_popup)
        close_button.pack(side=tk.LEFT, padx=5)
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
        if "ar" in self.response_area.tag_names():
            reshaped_text = arabic_reshaper.reshape(self.current_response_text)
            display_text = "\u202E" + get_display(reshaped_text) + "\u202C"
            self.response_area.insert(tk.END, display_text, "arabic")
        else:
            self.response_area.insert(tk.END, self.current_response_text)
        self.response_area.config(state=tk.DISABLED)

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

    def save_image_to_tmp(self, image):
        tmp_dir = "tmp"
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        filename = "pdf_ai_tmp_image.png"
        tmp_path = os.path.join(tmp_dir, filename)
        image.save(tmp_path)
        return tmp_path

    def setup_chat_panel(self):
        self.chat_frame = ttk.Frame(self.root, width=350)
        self.chat_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_frame.pack_propagate(False)
        self.setup_ai_chat()

    def setup_ai_chat(self):
        top_bar = tk.Frame(self.chat_frame, bg="#F7F7F7")
        top_bar.pack(fill=tk.X, pady=(0, 5))
        title_label = tk.Label(top_bar, text="AI Chat", font=("Segoe UI", 12, "bold"), bg="#F7F7F7", fg="#0D47A1")
        title_label.pack(side=tk.LEFT, padx=5)
        close_btn = tk.Button(top_bar, text="X", font=("Segoe UI", 10, "bold"), bg="#F7F7F7", fg="red", bd=0, command=self.toggle_chat)
        close_btn.pack(side=tk.RIGHT, padx=5)
        self.chat_log_frame = ttk.Frame(self.chat_frame)
        self.chat_log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_log = tk.Text(self.chat_log_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Segoe UI", 11), bg="#F7F7F7", fg="#0D47A1", bd=0)
        self.chat_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_scroll = ttk.Scrollbar(self.chat_log_frame, orient=tk.VERTICAL, command=self.chat_log.yview)
        self.chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_log.configure(yscrollcommand=self.chat_scroll.set)
        chat_input_frame = ttk.Frame(self.chat_frame)
        chat_input_frame.pack(fill=tk.X, padx=5, pady=5)
        self.chat_input = tk.Text(chat_input_frame, height=3, wrap="word", font=("Segoe UI", 11), bd=1, relief="solid", padx=5, pady=5)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chat_input.bind("<Return>", self.on_enter_pressed)
        send_button = ttk.Button(chat_input_frame, text="Send ➤", command=self.process_ai_chat_message)
        send_button.pack(side=tk.LEFT, padx=(5,0))
        self.chat_open = True

    def toggle_chat(self):
        if self.chat_open:
            self.chat_frame.pack_forget()
            self.chat_open = False
        else:
            self.chat_frame.pack(side=tk.RIGHT, fill=tk.Y)
            self.chat_open = True

    def on_enter_pressed(self, event):
        if event.state & 0x0001:
            return None
        else:
            self.process_ai_chat_message()
            return "break"

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
        bubble_frame = tk.Frame(self.chat_log, bg=bubble_color, bd=0)
        bubble_label = tk.Label(bubble_frame, text=message, bg=bubble_color, fg="black", font=("Segoe UI", 10), wraplength=260, justify="left")
        bubble_label.pack(padx=10, pady=2)
        self.chat_log.insert(tk.END, "\n")
        self.chat_log.window_create(tk.END, window=bubble_frame, padx=10, pady=2)
        self.chat_log.insert(tk.END, "\n")
        self.chat_log.see(tk.END)
        self.chat_log.config(state=tk.DISABLED)
        return bubble_label

    def start_voice_command(self):
        if not hasattr(self, "record_count"):
            self.record_count = 1
        else:
            self.record_count += 1
        self.voice_command_popup = tk.Toplevel(self.root)
        self.voice_command_popup.title("Voice Recorder")
        win_width, win_height = 300, 500
        parent_x = self.root.winfo_rootx()
        parent_y = self.root.winfo_rooty()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        x = parent_x + (parent_width // 2) - (win_width // 2)
        y = parent_y + (parent_height // 2) - (win_height // 2)
        self.voice_command_popup.geometry(f"{win_width}x{win_height}+{x}+{y}")
        self.voice_command_popup.configure(bg="#E3F2FD")
        self.voice_command_popup.transient(self.root)
        self.voice_command_popup.grab_set()
        try:
            mic_icon = load_icon("record_icon.png", size=(64, 64))
            self.mic_label = tk.Label(self.voice_command_popup, image=mic_icon, bg="#E3F2FD")
            self.mic_label.image = mic_icon
            self.mic_label.pack(pady=(20,10))
        except:
            self.mic_label = tk.Label(self.voice_command_popup, text="🎤", font=("Helvetica",40), bg="#E3F2FD")
            self.mic_label.pack(pady=(20,10))
        recording_title = f"Recording {self.record_count:03d}"
        self.recording_label = tk.Label(self.voice_command_popup, text=recording_title, font=("Helvetica",14,"bold"), fg="#0D47A1", bg="#E3F2FD")
        self.recording_label.pack()
        self.record_time_label = tk.Label(self.voice_command_popup, text="0:00", font=("Helvetica",12), fg="#0D47A1", bg="#E3F2FD")
        self.record_time_label.pack(pady=(0,20))
        self.wave_canvas_width = 250
        self.wave_canvas_height = 100
        self.wave_canvas = tk.Canvas(self.voice_command_popup, width=self.wave_canvas_width, height=self.wave_canvas_height, bg="#E3F2FD", highlightthickness=0)
        self.wave_canvas.pack(pady=10)
        self.stop_button = ttk.Button(self.voice_command_popup, text="Stop", command=self.stop_voice_recording)
        self.stop_button.pack(pady=20)
        self.recording = True
        self.audio_frames = []
        self.current_amplitude = 0
        self.wave_data = [0]*50
        self.record_start_time = time.time()
        threading.Thread(target=self.record_audio, daemon=True).start()
        self.update_waveform()
        self.update_record_time()

    def record_audio(self):
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
            audio_data = np.frombuffer(data, dtype=np.int16)
            max_amp = abs(audio_data).max()
            self.current_amplitude = max_amp / 32768.0
        stream.stop_stream()
        stream.close()
        p.terminate()

    def update_waveform(self):
        if self.recording:
            self.wave_data.pop(0)
            self.wave_data.append(self.current_amplitude)
        self.wave_canvas.delete("all")
        bar_width = self.wave_canvas_width / len(self.wave_data)
        center_y = self.wave_canvas_height // 2
        for i, amp in enumerate(self.wave_data):
            bar_height = int(amp * (self.wave_canvas_height // 2))
            x1 = i * bar_width
            x2 = x1 + (bar_width * 0.8)
            y1 = center_y - bar_height
            y2 = center_y + bar_height
            self.wave_canvas.create_rectangle(x1, y1, x2, y2, fill="#2196F3", outline="")
        if self.recording:
            self.voice_command_popup.after(100, self.update_waveform)

    def update_record_time(self):
        if self.recording:
            elapsed = int(time.time() - self.record_start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.record_time_label.config(text=f"{minutes}:{seconds:02d}")
            self.voice_command_popup.after(1000, self.update_record_time)

    def stop_voice_recording(self):
        if self.recording:
            self.recording = False
            self.recording_label.config(text="Stopping...")
            self.stop_button.config(state=tk.DISABLED)
            self.root.after(1000, self.process_voice_command)

    def process_voice_command(self):
        filename_wav = "tmp/recorded_audio_.wav"
        p = self.pyaudio_instance
        wf = wave.open(filename_wav, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()
        result = self.dummy_voice_ai(None)
        messagebox.showinfo("Voice Command Result", result)
        self.voice_command_popup.destroy()

    def dummy_voice_ai(self, audio_path):
        return "hello from AI"
