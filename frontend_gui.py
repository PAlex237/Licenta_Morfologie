"""
MorfoMed – Frontend (CustomTkinter)
Responsabil exclusiv pentru UI. Nu conține logică de procesare.
"""

import os
import cv2
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
from typing import List, Optional
import tkinter as tk

from backend_morph import MorphoBackend, Operatie

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class MorphoApp(ctk.CTk):

    # ------------------------------------------------------------------
    # Hărți clinice → tehnice (definite o singură dată, la nivel de clasă)
    # ------------------------------------------------------------------

    HARTA_OPERATORI = {
        "Filtrare Zgomot de Fond":       "Deschidere",
        "Solidificare Structuri":        "Închidere",
        "Evidențiere Micro-leziuni":     "Top-Hat",
        "Conturare Tumorală":            "Gradient",
        "Amplificare Regiuni Întunecate": "Black-Hat",
    }

    HARTA_INTENSITATE = {
        "Fină":      3,
        "Medie":     5,
        "Puternică": 7,
    }

    # ------------------------------------------------------------------
    # Inițializare
    # ------------------------------------------------------------------

    def __init__(self):
        super().__init__()

        self.title("MorfoMed")
        self.geometry("1200x850")
        self.after(0, lambda: self.state("zoomed"))

        self.backend = MorphoBackend()
        self.active_batch_folder: Optional[str] = None
        self.slice_files_list: List[str] = []
        self._focus_mode: bool = False          # Flag explicit – nu mai citim vizibilitatea widget-ului
        self._drag_start_y: int = 0
        self._drag_start_index: int = 0

        # Variabile pentru Zoom 
        self.zoom_scale: float = 1.0
        self.pan_x: int = 0
        self.pan_y: int = 0
        self._pan_start_x: int = 0
        self._pan_start_y: int = 0
        self.pil_image_orig: Optional[Image.Image] = None
        self.pil_image_proc: Optional[Image.Image] = None

        # --- Variabile pentru Labeling (Adnotări) ---
        # Format așteptat: {"slice_001.png": [{"nume": "Tumoare", "x1": 10, "y1": 10, "x2": 50, "y2": 50}], ...}
        self.labels_memory = {} 
        self.is_drawing_mode = False
        self.temp_rect_id = None
        self._draw_start_x = 0
        self._draw_start_y = 0
        
        self._build_context_menu()


        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()
        self._build_panel_toggle_buttons()

    # ------------------------------------------------------------------
    # Construire UI
    # ------------------------------------------------------------------

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=290, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=10, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(25, 15))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Meniu Principal",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(header, text="◀", width=30, height=30,
                      fg_color="transparent", border_width=1,
                      command=self.hide_left_panel).grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Tab-uri
        self.tabview = ctk.CTkTabview(self.sidebar_frame, command=self.on_tab_change)
        self.tabview.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        self.tabview.add("Single Image")
        self.tabview.add("Pipeline Medical")

        tab_single = self.tabview.tab("Single Image")
        ctk.CTkButton(tab_single, text="Încărcare Imagine", height=35,
                      command=self.gui_load_image).pack(pady=(15, 10), fill="x", padx=10)
        ctk.CTkButton(tab_single, text="Salvare Rezultat", height=35,
                      fg_color="#28a745", hover_color="#218838",
                      command=self.gui_save_image).pack(pady=10, fill="x", padx=10)

        tab_pipeline = self.tabview.tab("Pipeline Medical")
        ctk.CTkButton(tab_pipeline, text="Conversie Nouă (.nii)", height=35,
                      fg_color="#1f538d", hover_color="#14395e",
                      command=self.gui_convert_nii).pack(pady=(15, 10), fill="x", padx=10)
        ctk.CTkButton(tab_pipeline, text="Încarcă Set Existent", height=35,
                      fg_color="#b35900", hover_color="#8c4600",
                      command=self.gui_load_dataset).pack(pady=10, fill="x", padx=10)

        self.btn_save_batch = ctk.CTkButton(
            tab_pipeline, text="SALVEAZĂ LOTUL", height=40,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#28a745", hover_color="#218838",
            state="disabled", command=self.gui_save_batch)
        self.btn_save_batch.pack(pady=(25, 10), fill="x", padx=10)

        # Setări procesare
        ctk.CTkLabel(self.sidebar_frame, text="Setări Procesare:",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     anchor="w").grid(row=2, column=0, padx=20, pady=(25, 10), sticky="w")

        self.operator_dropdown = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=list(self.HARTA_OPERATORI.keys()),
            height=35)
        self.operator_dropdown.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.intensity_dropdown = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=list(self.HARTA_INTENSITATE.keys()),
            height=35)
        self.intensity_dropdown.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkButton(self.sidebar_frame, text="EXECUȚIE OPERATOR", height=45,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.gui_apply_processing).grid(
            row=6, column=0, padx=20, pady=35, sticky="ew")

        # Panou sesiune (dreapta)
        self.session_panel = ctk.CTkFrame(self, width=290, corner_radius=10)
        self.session_panel.grid(row=0, column=2, rowspan=10, sticky="nsew",
                                padx=(0, 10), pady=10)
        self.session_panel.grid_propagate(False)
        self.session_panel.grid_columnconfigure(0, weight=1)

        sess_header = ctk.CTkFrame(self.session_panel, fg_color="transparent")
        sess_header.grid(row=0, column=0, sticky="ew", pady=(10, 5), padx=10)
        sess_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sess_header, text="Istoric Sesiune",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(sess_header, text="▶", fg_color="transparent", border_width=1,
                      width=30, height=30,
                      command=self.hide_right_panel).grid(row=0, column=1, sticky="e", padx=(10, 0))

        self.session_panel.grid_rowconfigure(1, weight=1)
        self.session_scrollable_frame = ctk.CTkScrollableFrame(self.session_panel, width=300)
        self.session_scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))

        ctk.CTkButton(self.session_panel, text="↩ Anulează",
                      command=self.undo_operation).grid(
            row=2, column=0, pady=(5, 3), padx=10, sticky="ew")

        ctk.CTkButton(self.session_panel, text="🗑 Resetare Sesiune",
                      command=self.reset_session,
                      fg_color="#8B0000", hover_color="#5A0000").grid(
            row=3, column=0, pady=(0, 10), padx=10, sticky="ew")

    def _build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, rowspan=10, sticky="nsew")
        self.main_frame.grid_columnconfigure((0, 1), weight=1, uniform="equal")
        self.main_frame.grid_rowconfigure(0, weight=1)

        frame_orig = ctk.CTkFrame(self.main_frame, corner_radius=10)
        frame_orig.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(frame_orig, text="Imagine Originală / Sursă",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
                     
        self.canvas_orig = ctk.CTkCanvas(frame_orig, bg="#1e1e1e", highlightthickness=0)
        self.canvas_orig.pack(expand=True, fill="both", padx=15, pady=15)

        frame_proc = ctk.CTkFrame(self.main_frame, corner_radius=10)
        frame_proc.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(frame_proc, text="Rezultat Procesare (Previzualizare)",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
                     
        self.canvas_proc = ctk.CTkCanvas(frame_proc, bg="#1e1e1e", highlightthickness=0)
        self.canvas_proc.pack(expand=True, fill="both", padx=15, pady=15)

        for canvas in (self.canvas_orig, self.canvas_proc):
            canvas.bind("<MouseWheel>", self._on_zoom)
            canvas.bind("<ButtonPress-1>", self._on_pan_start)
            canvas.bind("<B1-Motion>", self._on_pan_drag)
        self.canvas_proc.bind("<Button-3>", self._show_context_menu)
        self.nav_frame = ctk.CTkFrame(self.main_frame, height=80, corner_radius=10)
        self.nav_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")

        self.lbl_slice_info = ctk.CTkLabel(self.nav_frame, text="Navigare Felii: - / -",
                                           font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_slice_info.pack(pady=(10, 0))

        self.slice_slider = ctk.CTkSlider(
            self.nav_frame, from_=0, to=100, number_of_steps=100,
            button_color="#b35900", button_hover_color="#8c4600",
            command=self.on_slice_slider_move)
        self.slice_slider.set(0)
        self.slice_slider.pack(fill="x", padx=30, pady=(5, 15))
        self.nav_frame.grid_remove()

        self.btn_focus = ctk.CTkButton(
            self.main_frame, text="⤢ Mod Focus", height=40, width=100,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f538d", hover_color="#14395e",
            command=self.toggle_focus_mode)
        self.btn_focus.grid(row=2, column=0, columnspan=2, padx=100, pady=(0, 15))

        self.status_bar = ctk.CTkLabel(
            self.main_frame, text="Stare: Așteptare date de intrare.",
            anchor="w", font=ctk.CTkFont(size=13), text_color="#a3a3a3")
        self.status_bar.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")

    def _build_panel_toggle_buttons(self):
        """Butoanele mici de redeschidere a panourilor, create după ce toate frame-urile există."""
        self.btn_show_left = ctk.CTkButton(
            self, text="▶", width=30, height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.show_left_panel)

        self.btn_show_right = ctk.CTkButton(
            self, text="◀", width=30, height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.show_right_panel)
    def _build_context_menu(self):
        """Construiește meniul nativ care va apărea la click dreapta."""
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", font=("Arial", 11))
        self.context_menu.add_command(label="➕ Adaugă Label...", command=self._activate_drawing_mode)
        self.context_menu.add_command(label="🗑 Șterge toate Label-urile", command=self._clear_current_labels)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="💾 Salvează imaginea", command=self._save_slice_with_labels)
    
    # ------------------------------------------------------------------
    # Panouri laterale
    # ------------------------------------------------------------------

    def hide_left_panel(self):
        self.sidebar_frame.grid_remove()
        self.btn_show_left.grid(row=0, column=0, sticky="w", padx=5, pady=20)

    def show_left_panel(self):
        self.btn_show_left.grid_remove()
        self.sidebar_frame.grid()

    def hide_right_panel(self):
        self.session_panel.grid_remove()
        self.btn_show_right.grid(row=0, column=2, sticky="e", padx=5, pady=20)

    def show_right_panel(self):
        self.btn_show_right.grid_remove()
        self.session_panel.grid()

    def toggle_focus_mode(self):
        if self._focus_mode:
            self.show_left_panel()
            self.show_right_panel()
            self.btn_focus.configure(text="⤢ Mod Focus")
        else:
            self.hide_left_panel()
            self.hide_right_panel()
            self.btn_focus.configure(text="⤡ Mod Editare")
        self._focus_mode = not self._focus_mode

    # ------------------------------------------------------------------
    # Dialoguri personalizate
    # ------------------------------------------------------------------

    def show_custom_message(self, title: str, message: str, msg_type: str = "info"):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        w, h = 420, 200
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - w // 2
        y = self.winfo_rooty() + self.winfo_height() // 2 - h // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        color = "#28a745" if msg_type == "info" else "#d9534f"
        hover = "#218838" if msg_type == "info" else "#c9302c"

        ctk.CTkLabel(dialog, text=title,
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=color).pack(pady=(25, 5))
        ctk.CTkLabel(dialog, text=message,
                     font=ctk.CTkFont(size=13),
                     justify="center", wraplength=360).pack(pady=10, padx=20)
        ctk.CTkButton(dialog, text="Am înțeles", width=120, height=35,
                      font=ctk.CTkFont(weight="bold"),
                      fg_color=color, hover_color=hover,
                      command=dialog.destroy).pack(pady=(10, 20))
        self.wait_window(dialog)

    def ask_custom_folder_name(self, title: str, prompt: str, initial_value: str) -> Optional[str]:
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        w, h = 450, 220
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - w // 2
        y = self.winfo_rooty() + self.winfo_height() // 2 - h // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=prompt,
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(25, 10), padx=20)

        entry = ctk.CTkEntry(dialog, width=350, height=35, font=ctk.CTkFont(size=14))
        entry.insert(0, initial_value)
        entry.pack(pady=10)

        result: List[Optional[str]] = [None]

        def on_submit():
            result[0] = entry.get()
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Confirmă", width=120, height=35,
                      font=ctk.CTkFont(weight="bold"),
                      command=on_submit).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Anulează", width=120, height=35,
                      fg_color="gray", hover_color="#555555",
                      command=dialog.destroy).pack(side="left", padx=10)

        self.wait_window(dialog)
        return result[0]

    # ------------------------------------------------------------------
    # Acțiuni UI principale
    # ------------------------------------------------------------------

    def on_tab_change(self):
        self.reset_session()
        tab = self.tabview.get()
        if tab == "Pipeline Medical":
            self.status_bar.configure(text="Stare: Mod Pipeline activat. Încărcați un director.")
        else:
            self.status_bar.configure(text="Stare: Mod Imagine Unică activat.")

    def gui_load_image(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        self.backend.reset()                
        self.render_session_timeline()     
  
        if self.backend.load_image(path):
            self.nav_frame.grid_remove()          
            self.slice_files_list = []            
            self.active_batch_folder = None       
            self.btn_save_batch.configure(state="disabled") 

            self.display_image(self.backend.get_original_image(), self.canvas_orig)
            
            self._clear_processed_label()       
            
            self.status_bar.configure(text="Stare: Imagine nouă încărcată. Sesiunea a fost resetată de la 0.")
        else:
            self.show_custom_message("Eroare Încărcare",
                                     "Nu s-a putut citi fișierul selectat.", "error")

    def gui_save_image(self):
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path and self.backend.save_image(path):
            self.show_custom_message("Salvare Reușită",
                                     "Imaginea a fost salvată pe disc.", "info")

    def gui_load_dataset(self):
        folder = filedialog.askdirectory(initialdir="datasets/converted_2d")
        if not folder:
            return

        self.reset_session()

        ok, info = self.backend.load_batch_from_folder(folder)
        if not ok:
            self.show_custom_message("Folder Incorect", str(info), "error")
            return

        self.active_batch_folder = folder
        self._init_slider(folder)
        self.status_bar.configure(text=f"Stare: Set date încărcat '{os.path.basename(folder)}'.")

    def gui_convert_nii(self):
        path = filedialog.askopenfilename(filetypes=[("NIfTI", "*.nii *.nii.gz")])
        if not path:
            return

        sugestie = os.path.basename(path).split(".")[0]
        name = self.ask_custom_folder_name(
            "Configurare Export NIfTI",
            "Introduceți un nume pentru setul 2D rezultat:", sugestie)
        if not name:
            return

        out = os.path.join("datasets", "converted_2d", name)
        self.status_bar.configure(text="Stare: Inițializare decodificare volum NIfTI...")
        self.update_idletasks()

        self.reset_session()

        ok, info = self.backend.convert_nii_volume(path, out)
        if ok:
            self.active_batch_folder = out
            self._init_slider(out)
            self.status_bar.configure(text="Stare: Pipeline finalizat cu succes. Navigare activă.")
            self.show_custom_message("Succes Conversie",
                                     f"Volumul 3D a fost tăiat în {info} felii 2D.", "info")
        else:
            self.status_bar.configure(text="Stare: Eroare la conversie.")
            self.show_custom_message("Eroare Critică",
                                     f"Nu s-a putut converti volumul NIfTI:\n{info}", "error")

    def gui_apply_processing(self):
        val_obiectiv = self.operator_dropdown.get()
        val_intensitate = self.intensity_dropdown.get()

        op_tehnic = self.HARTA_OPERATORI.get(val_obiectiv, "Deschidere")
        kernel = self.HARTA_INTENSITATE.get(val_intensitate, 3)

        if self.tabview.get() == "Pipeline Medical" and not self.active_batch_folder:
            self.show_custom_message("Avertisment",
                                     "Încărcați un set de date mai întâi.", "error")
            return

        if self.tabview.get() == "Single Image" and self.backend.get_original_image() is None:
            self.show_custom_message("Avertisment",
                                     "Încărcați o imagine înainte de procesare.", "error")
            return

        operatie = Operatie(
            nume_clinic=val_obiectiv,
            intensitate_text=val_intensitate,
            nume=op_tehnic,
            kernel=kernel,
        )
        self.backend.adauga_operatie(operatie)
        self.render_session_timeline()

        if self.tabview.get() == "Pipeline Medical":
            self.btn_save_batch.configure(state="normal")
            self.on_slice_slider_move(self.slice_slider.get())
            self.status_bar.configure(text=f"Stare: Pipeline actualizat cu '{val_obiectiv}'.")
        else:
            self._refresh_processed_display()
            self.status_bar.configure(text=f"Stare: Filtru '{val_obiectiv}' aplicat.")

    def gui_save_batch(self):
        if not self.active_batch_folder:
            return

        # Propunem un nume bazat pe numărul de operații din stivă
        ops_text = "_".join(op.nume[:3] for op in self.backend.operation_stack) or "original"
        sugestie = f"{os.path.basename(self.active_batch_folder)}_{ops_text}"

        name = self.ask_custom_folder_name(
            "Salvare Definitivă",
            "Introduceți numele directorului de export:", sugestie)
        if not name:
            return

        out = os.path.join("datasets", "processed_2d", name)
        ok, info = self.backend.save_batch_from_memory(out)
        if ok:
            self.status_bar.configure(text=f"Stare: Lot de {info} imagini salvat.")
            self.show_custom_message("Lot Salvat",
                                     f"S-au salvat {info} felii procesate în:\nprocessed_2d/{name}",
                                     "info")
        else:
            self.show_custom_message("Eroare Salvare", str(info), "error")

    # ------------------------------------------------------------------
    # Navigare felii batch
    # ------------------------------------------------------------------

    def _init_slider(self, folder: str):
        self.slice_files_list = sorted(
            f for f in os.listdir(folder) if f.endswith(".png"))

        if not self.slice_files_list:
            return

        count = len(self.slice_files_list)
        self.slice_slider.configure(from_=0, to=count - 1, number_of_steps=count - 1)
        mid = count // 2
        self.slice_slider.set(mid)
        self.nav_frame.grid()
        self.btn_save_batch.configure(state="disabled")
        self.on_slice_slider_move(mid)

    def on_slice_slider_move(self, value):
        if not self.slice_files_list:
            return

        idx = int(value)
        file_name = self.slice_files_list[idx]
        self.lbl_slice_info.configure(
            text=f"Navigare Felii: {idx + 1} / {len(self.slice_files_list)}  —  [{file_name}]")

        orig = self.backend.base_data.get(file_name)
        if orig is not None:
            self.display_image(orig, self.canvas_orig)

        proc = self.backend.batch_cache.get(file_name)
        if proc is not None:
            self.display_image(proc, self.canvas_proc)
        else:
            self._clear_processed_label()

    # ------------------------------------------------------------------
    # Afișare imagini pe Canvas
    # ------------------------------------------------------------------

    def display_image(self, cv_img, target_canvas):
        """Preia matricea OpenCV, o salvează ca PIL și o randează pe Canvas."""
        if cv_img is None:
            return
            
        if cv_img.ndim == 2:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(rgb)
        
        # Memorăm imaginea brută în funcție de canvas-ul destinație
        if target_canvas == self.canvas_orig:
            self.pil_image_orig = pil_img
        else:
            self.pil_image_proc = pil_img
            
        self._redraw_canvas(target_canvas)

    def _redraw_canvas(self, canvas):
        """Desenează imaginea pe canvas aplicând calculele de Zoom și Panning."""
        canvas.delete("all")  # Curățăm desenul anterior
        
        # Alegem sursa corectă
        pil_img = self.pil_image_orig if canvas == self.canvas_orig else self.pil_image_proc
        
        # Calculăm centrul planșei (aici ne asigurăm că nu e lățime 0 la start)
        w, h = max(canvas.winfo_width(), 400), max(canvas.winfo_height(), 400)
        center_x = (w // 2) + self.pan_x
        center_y = (h // 2) + self.pan_y

        if pil_img is None:
            # Afișăm textul dacă nu există imagine
            text = "Așteptare input..." if canvas == self.canvas_orig else "Așteptare prelucrare..."
            canvas.create_text(w//2, h//2, text=text, fill="gray", font=("Arial", 14))
            return

        # Redimensionare (Image.Resampling.NEAREST e perfect pentru imagini medicale 
        # fiindcă păstrează contururile clare ale pixelilor originali când dai zoom)
        new_width = int(pil_img.width * self.zoom_scale)
        new_height = int(pil_img.height * self.zoom_scale)
        
        if new_width <= 0 or new_height <= 0:
            return
            
        resized_pil = pil_img.resize((new_width, new_height), Image.Resampling.NEAREST)
        tk_image = ImageTk.PhotoImage(resized_pil)
        
        # Păstrăm referința pentru Garbage Collector și desenăm!
        canvas.image = tk_image 
        canvas.create_image(center_x, center_y, anchor="center", image=tk_image)

    def _clear_canvas(self, canvas):
        """Golește canvas-ul complet, readucând starea la zero."""
        if canvas == self.canvas_orig:
            self.pil_image_orig = None
        else:
            self.pil_image_proc = None
            
        # Resetăm zoom-ul la normal când se șterge imaginea
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._redraw_canvas(canvas)

    def _clear_processed_label(self):
        self._clear_canvas(self.canvas_proc)

    def _refresh_processed_display(self):
        """Actualizează panoul cu rezultatul procesării (mod Single Image)."""
        img = self.backend.get_processed_image()
        if img is not None:
            self.display_image(img, self.canvas_proc)
        else:
            self._clear_processed_label()

    # ------------------------------------------------------------------
    # Timeline sesiune
    # ------------------------------------------------------------------

    def render_session_timeline(self):
        for w in self.session_scrollable_frame.winfo_children():
            w.destroy()

        for index, op in enumerate(self.backend.operation_stack):
            row = ctk.CTkFrame(self.session_scrollable_frame, height=60)
            row.pack(fill="x", padx=5, pady=4)
            row.pack_propagate(False)

            handle = ctk.CTkLabel(row, text="☰", cursor="hand2", width=20)
            handle.pack(side="left", padx=5)
            handle.bind("<ButtonPress-1>",   lambda e, i=index: self._on_drag_start(e, i))
            handle.bind("<ButtonRelease-1>", lambda e, i=index: self._on_drag_release(e, i))

            text = f"{op.nume_clinic}\n↳ Intensitate: {op.intensitate_text}"
            ctk.CTkLabel(row, text=text, justify="left",
                         font=("Arial", 12), wraplength=190, anchor="w").pack(
                side="left", padx=(10, 5), fill="x", expand=True)

            ctk.CTkButton(row, text="❌", width=32, height=32,
                          fg_color="#581a1a", hover_color="#8B0000",
                          text_color="white", border_width=1, border_color="#8B0000",
                          command=lambda i=index: self._delete_operation(i)).pack(
                side="right", padx=5, pady=8)

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------

    def _on_drag_start(self, event, index: int):
        self._drag_start_y = event.y_root
        self._drag_start_index = index

    def _on_drag_release(self, event, start_index: int):
        delta_y = event.y_root - self._drag_start_y
        shift = round(delta_y / 40)  # ~40px per rând

        if shift != 0:
            moved = self.backend.muta_operatie(start_index, start_index + shift)
            if moved:
                self.render_session_timeline()
                self._update_display_after_stack_change()
    # ------------------------------------------------------------------
    # Interacțiune pe Canvas (Zoom & Panning)
    # ------------------------------------------------------------------

    def _on_zoom(self, event):
        if event.delta > 0:
            self.zoom_scale *= 1.15  # Zoom In 15%
        elif event.delta < 0:
            self.zoom_scale /= 1.15  # Zoom Out 15%
        
        # Limităm zoom-ul între 10% și 1000%
        self.zoom_scale = max(0.1, min(self.zoom_scale, 10.0))
        
        # Redesenăm pe ecran ambele imagini
        self._redraw_canvas(self.canvas_orig)
        self._redraw_canvas(self.canvas_proc)

    def _on_pan_start(self, event):
        self._pan_start_x = event.x
        self._pan_start_y = event.y

    def _on_pan_drag(self, event):
        dx = event.x - self._pan_start_x
        dy = event.y - self._pan_start_y
        
        self.pan_x += dx
        self.pan_y += dy
        
        # Actualizăm punctul de start pentru următorul frame de mișcare
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        
        # Redesenăm
        self._redraw_canvas(self.canvas_orig)
        self._redraw_canvas(self.canvas_proc)

    # ------------------------------------------------------------------
    # Operații pe stivă (acționate din UI)
    # ------------------------------------------------------------------

    def _delete_operation(self, index: int):
        if self.backend.sterge_operatie(index):
            self.render_session_timeline()
            self._update_display_after_stack_change()

    def undo_operation(self):
        if self.backend.undo():
            self.render_session_timeline()
            self._update_display_after_stack_change()
            self.status_bar.configure(text="Stare: Ultima operație anulată.")

    def reset_session(self):
        # 1. Resetăm stiva de operatori
        self.backend.reset()
        
        # 2. Golire completă din memorie
        self.backend.image_original = None
        self.backend.image_processed = None
        self.backend.base_data = {}
        self.backend.batch_cache = {}

        # 3. Resetare elemente de navigare UI
        self.active_batch_folder = None
        self.slice_files_list = []
        self.nav_frame.grid_remove()
        self.btn_save_batch.configure(state="disabled")

        self._clear_canvas(self.canvas_orig)
        self._clear_canvas(self.canvas_proc)

        # 4. Re-randăm UI-ul
        self.render_session_timeline()
        self.status_bar.configure(text="Stare: Sesiune resetată.")

    def _update_display_after_stack_change(self):
        """Punct unic de actualizare a imaginilor după orice modificare a stivei."""
        if self.tabview.get() == "Pipeline Medical" and self.slice_files_list:
            self.on_slice_slider_move(self.slice_slider.get())
        else:
            self._refresh_processed_display()
            
    # ------------------------------------------------------------------
    # Funcționalitate Adnotări (Labeling)
    # ------------------------------------------------------------------

    def _show_context_menu(self, event):
        """Afișează meniul doar dacă avem o imagine procesată pe ecran."""
        if self.pil_image_proc is not None:
            # Afișăm meniul exact la coordonatele cursorului
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def _activate_drawing_mode(self):
        print("DEBUG: Modul de desenare va fi activat în Pasul 2.")
        
    def _clear_current_labels(self):
        print("DEBUG: Label-urile vor fi șterse.")

    def _save_slice_with_labels(self):
        print("DEBUG: Imaginea va fi salvată cu OpenCV în Pasul 4.")