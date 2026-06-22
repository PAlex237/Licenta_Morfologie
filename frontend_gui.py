"""
MorfoMed – Frontend (CustomTkinter)
Responsabil exclusiv pentru UI. Nu conține logică de procesare.
"""

import os
import cv2
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
from typing import List, Optional

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
        self.lbl_orig_img = ctk.CTkLabel(frame_orig, text="Așteptare input...", text_color="gray")
        self.lbl_orig_img.pack(expand=True, fill="both", padx=15, pady=15)

        frame_proc = ctk.CTkFrame(self.main_frame, corner_radius=10)
        frame_proc.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(frame_proc, text="Rezultat Procesare (Previzualizare)",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        self.lbl_proc_img = ctk.CTkLabel(frame_proc, text="Așteptare prelucrare...", text_color="gray")
        self.lbl_proc_img.pack(expand=True, fill="both", padx=15, pady=15)

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

        if self.backend.load_image(path):
            self.nav_frame.grid_remove()          # Ascundem slider-ul
            self.slice_files_list = []            # Golim lista de felii
            self.active_batch_folder = None       # Anulăm folderul activ
            self.btn_save_batch.configure(state="disabled") # Dezactivăm salvarea lotului
            # ------------------------------------------------------------

            self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
            # Recalculăm pipeline-ul pe noua imagine (stiva rămâne)
            self._refresh_processed_display()
            self.status_bar.configure(text="Stare: Imagine nouă încărcată.")
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

        ok, info = self.backend.load_batch_from_folder(folder)
        if not ok:
            self.show_custom_message("Folder Incorect", str(info), "error")
            return

        self.backend.operation_stack.clear()
        self.render_session_timeline()
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

        ok, info = self.backend.convert_nii_volume(path, out)
        if ok:
            self.reset_session()
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
            self.display_image(orig, self.lbl_orig_img)

        proc = self.backend.batch_cache.get(file_name)
        if proc is not None:
            self.display_image(proc, self.lbl_proc_img)
        else:
            self._clear_processed_label()

    # ------------------------------------------------------------------
    # Afișare imagini
    # ------------------------------------------------------------------

    def display_image(self, cv_img, lbl):
        """Convertește o matrice OpenCV (grayscale sau BGR) și o afișează."""
        if cv_img is None:
            return
        if cv_img.ndim == 2:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(rgb)
        ctk_img = ctk.CTkImage(pil_img, size=(700, 700))
        lbl.configure(image=ctk_img, text="")
        lbl.image = ctk_img  # Prevenim garbage collection

    def _clear_processed_label(self):
        self.lbl_proc_img.configure(image=None, text="Așteptare prelucrare...")

    def _refresh_processed_display(self):
        """Actualizează panoul cu rezultatul procesării (mod Single Image)."""
        img = self.backend.get_processed_image()
        if img is not None:
            self.display_image(img, self.lbl_proc_img)
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
        # 1. Resetăm stiva de operatori din backend
        self.backend.reset()
        
        # 2. Golim complet datele din memorie (Backend)
        self.backend.image_original = None
        self.backend.image_processed = None
        self.backend.base_data = {}
        self.backend.batch_cache = {}

        # 3. Golim datele de navigare (Frontend)
        self.active_batch_folder = None
        self.slice_files_list = []
        self.nav_frame.grid_remove()
        self.btn_save_batch.configure(state="disabled")

        # 4. Resetăm etichetele UI la starea inițială (sloturi goale cu text)
        self.lbl_orig_img.configure(image=None, text="Așteptare input...")
        self.lbl_proc_img.configure(image=None, text="Așteptare prelucrare...")
        # ------------------------------------------------------------------

        # 5. Randăm UI-ul actualizat
        self.render_session_timeline()
        self.status_bar.configure(text="Stare: Sesiune resetată.")

    def _update_display_after_stack_change(self):
        """Punct unic de actualizare a imaginilor după orice modificare a stivei."""
        if self.tabview.get() == "Pipeline Medical" and self.slice_files_list:
            self.on_slice_slider_move(self.slice_slider.get())
        else:
            self._refresh_processed_display()