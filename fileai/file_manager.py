import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF

class FileManager:
    def __init__(self, root):
        self.root = root

    def open_pdf_dialog(self):
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        return pdf_path

    def load_pdf_document(self, pdf_path):
        try:
            doc = fitz.open(pdf_path)
            return doc
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF:\n{e}")
            return None
