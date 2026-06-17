import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
import cv2
import os

from backend_morph import MorphoBackend

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class MorphoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MorfoMed")
        self.geometry("1200x850")
        
        # Pornire automată maximizată pe tot ecranul
        self.after(0, lambda: self.state('zoomed'))

        self.backend = MorphoBackend()
        self.active_batch_folder = None
        self.processed_batch_folder = None
        self.slice_files_list = [] 
        self.base_data={}
        self.operator_var = []
        self.grid_columnconfigure(0, weight=0)  # sidebar fixed width
        self.grid_columnconfigure(1, weight=1)  # main image expands
        self.grid_columnconfigure(2, weight=0)  # history fixed width
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()
        
        # --- PENTRU PANOUL DIN STÂNGA ---
        self.btn_show_left = ctk.CTkButton(self, text="▶", width=30, height=40, font=("Arial", 16, "bold"), command=self.show_left_panel)
        
        self.btn_hide_left = ctk.CTkButton(self.sidebar_frame, text="◀", fg_color="transparent", border_width=1, width=30, height=30, command=self.hide_left_panel)

        # --- PENTRU PANOUL DIN DREAPTA ---
        
        self.btn_show_right = ctk.CTkButton(self, text="◀", width=30, height=40, font=("Arial", 16, "bold"), command=self.show_right_panel)
        
    def _build_sidebar(self):
        # --- SIDEBAR FRAME ---
        self.sidebar_frame = ctk.CTkFrame(self, width=290, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=10, sticky="nsew")
        self.sidebar_frame.grid_propagate(False) 
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        # --- HEADER SIDEBAR (Titlu + Buton Ascunde) ---
        header_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(25, 15))
        header_frame.grid_columnconfigure(0, weight=1) # Titlul ia tot spațiul rămas

        ctk.CTkLabel(header_frame, text="Meniu Principal", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, sticky="w")
        
        # Butonul de ascundere stânga (aici este eroarea ta - trebuie să fie definit/creat)
        self.btn_hide_left = ctk.CTkButton(header_frame, text="◀", width=30, height=30, 
                                           fg_color="transparent", border_width=1, 
                                           command=self.hide_left_panel)
        self.btn_hide_left.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # --- RESTUL TAB-URILOR ---
        self.tabview = ctk.CTkTabview(self.sidebar_frame, command=self.on_tab_change)
        self.tabview.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        self.tabview.add("Single Image")
        self.tabview.add("Pipeline Medical")
        
        # TAB: SINGLE
        ctk.CTkButton(self.tabview.tab("Single Image"), text="Încărcare Imagine", height=35, command=self.gui_load_image).pack(pady=(15, 10), fill="x", padx=10)
        ctk.CTkButton(self.tabview.tab("Single Image"), text="Salvare Rezultat", height=35, fg_color="#28a745", hover_color="#218838", command=self.gui_save_image).pack(pady=10, fill="x", padx=10)

        # TAB: PIPELINE
        ctk.CTkButton(self.tabview.tab("Pipeline Medical"), text="Conversie Nouă (.nii)", height=35, fg_color="#1f538d", hover_color="#14395e", command=self.gui_convert_nii).pack(pady=(15, 10), fill="x", padx=10)
        ctk.CTkButton(self.tabview.tab("Pipeline Medical"), text="Încarcă Set Existent", height=35, fg_color="#b35900", hover_color="#8c4600", command=self.gui_load_dataset).pack(pady=10, fill="x", padx=10)
        
        self.btn_save_batch = ctk.CTkButton(self.tabview.tab("Pipeline Medical"), text="SALVEAZĂ LOTUL", height=40, font=ctk.CTkFont(weight="bold"), fg_color="#28a745", hover_color="#218838", state="disabled", command=self.gui_save_batch)
        self.btn_save_batch.pack(pady=(25, 10), fill="x", padx=10)

        # --- SETĂRI PROCESARE ---
        ctk.CTkLabel(self.sidebar_frame, text="Setări Procesare:", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").grid(row=2, column=0, padx=20, pady=(25, 10), sticky="w")
        
        self.operator_dropdown = ctk.CTkOptionMenu(
            self.sidebar_frame, 
            values=["Filtrare Zgomot de Fond", "Solidificare Structuri", "Evidențiere Micro-leziuni", "Conturare Tumorală", "Amplificare Regiuni Întunecate"], 
            height=35
        )
        self.operator_dropdown.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.intensity_dropdown = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Fină", "Medie", "Puternică"],
            height=35
        )
        self.intensity_dropdown.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.btn_apply = ctk.CTkButton(self.sidebar_frame, text="EXECUȚIE OPERATOR", height=45, font=ctk.CTkFont(size=14, weight="bold"), command=self.gui_apply_processing)
        self.btn_apply.grid(row=6, column=0, padx=20, pady=35, sticky="ew")

        # --- PANOUL DE SESIUNE (ISTORIC) ---
        # Creăm un cadru dedicat pentru istoric, pe care îl punem în interfață (ex: în partea dreaptă)
        self.session_panel = ctk.CTkFrame(self, width=290, corner_radius=10)
        self.session_panel.grid(row=0, column=2, rowspan=10, sticky="nsew", padx=(0, 10), pady=10)
        self.session_panel.grid_propagate(False)
        self.session_panel.grid_columnconfigure(0, weight=1)

        # Header frame cu titlu și buton de ascundere
        header_frame = ctk.CTkFrame(self.session_panel, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(10, 5), padx=10)
        header_frame.grid_columnconfigure(0, weight=1)
        
        self.session_title = ctk.CTkLabel(header_frame, text="Istoric Sesiune", font=("Arial", 16, "bold"))
        self.session_title.grid(row=0, column=0, sticky="w")
        
        self.btn_hide_right = ctk.CTkButton(header_frame, text="▶", fg_color="transparent", border_width=1, width=30, height=30, command=self.hide_right_panel)
        self.btn_hide_right.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Zona scrollabilă (AICI vor apărea operațiile)
        self.session_panel.grid_rowconfigure(1, weight=1)
        self.session_scrollable_frame = ctk.CTkScrollableFrame(self.session_panel, width=300)
        self.session_scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))

        # Butoane de control global al sesiunii
        self.btn_undo = ctk.CTkButton(self.session_panel, text="↩ Anulează", command=self.undo_operation)
        self.btn_undo.grid(row=2, column=0, pady=(5, 3), padx=10, sticky="ew")

        self.btn_reset = ctk.CTkButton(self.session_panel, text="🗑 Resetare Sesiune", command=self.reset_session, fg_color="#8B0000", hover_color="#5A0000")
        self.btn_reset.grid(row=3, column=0, pady=(0, 10), padx=10, sticky="ew")
    def _build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, rowspan=10, sticky="nsew")
        self.main_frame.grid_columnconfigure((0, 1), weight=1, uniform="equal")
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        frame_orig = ctk.CTkFrame(self.main_frame, corner_radius=10)
        frame_orig.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(frame_orig, text="Imagine Originală / Sursă", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        self.lbl_orig_img = ctk.CTkLabel(frame_orig, text="Așteptare input...", text_color="gray")
        self.lbl_orig_img.pack(expand=True, fill="both", padx=15, pady=15)

        frame_proc = ctk.CTkFrame(self.main_frame, corner_radius=10)
        frame_proc.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(frame_proc, text="Rezultat Procesare (Previzualizare)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        self.lbl_proc_img = ctk.CTkLabel(frame_proc, text="Așteptare prelucrare...", text_color="gray")
        self.lbl_proc_img.pack(expand=True, fill="both", padx=15, pady=15)

        self.nav_frame = ctk.CTkFrame(self.main_frame, height=80, corner_radius=10)
        self.nav_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        
        self.lbl_slice_info = ctk.CTkLabel(self.nav_frame, text="Navigare Felii: - / -", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_slice_info.pack(pady=(10, 0))
        
        self.slice_slider = ctk.CTkSlider(self.nav_frame, from_=0, to=100, number_of_steps=100, button_color="#b35900", button_hover_color="#8c4600", command=self.on_slice_slider_move)
        self.slice_slider.set(0)
        self.slice_slider.pack(fill="x", padx=30, pady=(5, 15))
        self.nav_frame.grid_remove() 

        self.btn_focus = ctk.CTkButton(self.main_frame, text="⤢ Mod Focus", height=40, width=100, font=ctk.CTkFont(size=14, weight="bold"), 
                                       fg_color="#1f538d", hover_color="#14395e",
                                       command=self.toggle_focus_mode)
        self.btn_focus.grid(row=2, column=0, columnspan=2, padx=100, pady=(0, 15))

        self.status_bar = ctk.CTkLabel(self.main_frame, text="Stare: Așteptare date de intrare.", anchor="w", font=ctk.CTkFont(size=13), text_color="#a3a3a3")
        self.status_bar.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
    def show_custom_message(self, title, message, msg_type="info"):
        """Afișează un popup de informare sau eroare premium, centrat și aliniat cu tema aplicației."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog_width = 420
        dialog_height = 200
        
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (dialog_width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (dialog_height // 2)
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        theme_color = "#28a745" if msg_type == "info" else "#d9534f"

        lbl_title = ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=theme_color)
        lbl_title.pack(pady=(25, 5))

        lbl_msg = ctk.CTkLabel(dialog, text=message, font=ctk.CTkFont(size=13), justify="center", wraplength=360)
        lbl_msg.pack(pady=10, padx=20)

        btn_ok = ctk.CTkButton(dialog, text="Am înțeles", width=120, height=35, font=ctk.CTkFont(weight="bold"), 
                               fg_color=theme_color, hover_color="#218838" if msg_type == "info" else "#c9302c", 
                               command=dialog.destroy)
        btn_ok.pack(pady=(10, 20))

        self.wait_window(dialog)

    def ask_custom_folder_name(self, title, prompt, initial_value):
        """Design premium pentru popup-ul de introducere text, aliniat cu tema Dark Mode"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog_width = 450
        dialog_height = 220
        
        self.update_idletasks()
        pos_x = self.winfo_rootx() + (self.winfo_width() // 2) - (dialog_width // 2)
        pos_y = self.winfo_rooty() + (self.winfo_height() // 2) - (dialog_height // 2)
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        lbl = ctk.CTkLabel(dialog, text=prompt, font=ctk.CTkFont(size=15, weight="bold"))
        lbl.pack(pady=(25, 10), padx=20)

        entry = ctk.CTkEntry(dialog, width=350, height=35, font=ctk.CTkFont(size=14))
        entry.insert(0, initial_value)
        entry.pack(pady=10)

        result = [None]
        def on_submit():
            result[0] = entry.get()
            dialog.destroy()
        def on_cancel():
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)

        btn_ok = ctk.CTkButton(btn_frame, text="Confirmă", width=120, height=35, font=ctk.CTkFont(weight="bold"), command=on_submit)
        btn_ok.pack(side="left", padx=10)

        btn_cancel = ctk.CTkButton(btn_frame, text="Anulează", width=120, height=35, fg_color="gray", hover_color="#555555", command=on_cancel)
        btn_cancel.pack(side="left", padx=10)

        self.wait_window(dialog)
        return result[0]

    def on_slice_slider_move(self, value):
        if not self.slice_files_list: return
        
        idx = int(value)
        file_name = self.slice_files_list[idx]
        self.lbl_slice_info.configure(text=f"Navigare Felii: {idx + 1} / {len(self.slice_files_list)}  —  [{file_name}]")
        
        orig_path = os.path.join(self.active_batch_folder, file_name)
        self.backend.load_image(orig_path)
        
        # Display the original image
        if self.backend.get_original_image() is not None:
            self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
        
        if hasattr(self.backend, 'batch_cache') and file_name in self.backend.batch_cache:
            self.display_image(self.backend.batch_cache[file_name], self.lbl_proc_img)
        else:
            from PIL import Image
            import customtkinter as ctk
            
            # Creăm o imagine transparentă de 1x1 pixel (invizibilă)
            blank_pil = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            blank_img = ctk.CTkImage(light_image=blank_pil, size=(1, 1))
            
            # O punem pe ecran în loc de 'None'
            self.lbl_proc_img.configure(image=blank_img, text="Apasă 'PREVIZUALIZEAZĂ LOT' pentru rezultat.")
            self.lbl_proc_img.image = blank_img

    def on_tab_change(self): # (sau cum se numește funcția ta)
        tab_activ = self.tabview.get()
        
        self.reset_session()
        
        if tab_activ == "Pipeline Medical":
            self.status_bar.configure(text="Stare: Mod Pipeline activat. Încărcați un director.")
            
        elif tab_activ == "Single Image":
            # Logica pentru imagine unică
            self.status_bar.configure(text="Stare: Mod Imagine Unică activat.")

    def _init_slider(self, folder_path):
        self.slice_files_list = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
        if self.slice_files_list:
            count = len(self.slice_files_list)
            self.slice_slider.configure(from_=0, to=count-1, number_of_steps=count-1)
            self.slice_slider.set(count // 2)
            self.nav_frame.grid()
            self.btn_save_batch.configure(state="disabled") 
            
            # Load all original images into base_data
            self.backend.base_data = {}
            for file_name in self.slice_files_list:
                img_path = os.path.join(folder_path, file_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    self.backend.base_data[file_name] = img
            
            if hasattr(self.backend, 'batch_cache'):
                self.backend.batch_cache.clear() 
            self.on_slice_slider_move(count // 2)

    def gui_load_image(self):
        p = filedialog.askopenfilename()
        
        if p and self.backend.load_image(p):
            
            self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
            
            self.reset_session() 
            
            if hasattr(self.backend, 'processed_image'):
                self.backend.processed_image = None
                
            try:
                self.lbl_proc_img.configure(image="", text="Așteptare prelucrare...")
            except Exception:
                self.lbl_proc_img.configure(image=None, text="Așteptare prelucrare...")
                
            self.status_bar.configure(text="Stare: Imagine nouă încărcată. Așteptare prelucrare.")
            
        elif p:
            self.show_custom_message("Eroare Încărcare", "Nu s-a putut citi fișierul selectat.", "error")
    def gui_save_image(self):
        p = filedialog.asksaveasfilename(defaultextension=".png")
        if p: 
            if self.backend.save_image(p):
                self.show_custom_message("Salvare Reușită", f"Imaginea curentă a fost salvată individual pe disc.", "info")

    def gui_load_dataset(self):
        d = filedialog.askdirectory(initialdir="datasets/converted_2d")
        if d:
            files = [f for f in os.listdir(d) if f.endswith('.png')]
            
            if not files:
                self.show_custom_message(
                    "Folder Incorect", 
                    f"Folderul '{os.path.basename(d)}' nu conține imagini!\n"
                    "Dă dublu-click pe folder ca să intri în el înainte să apeși 'Select Folder'.", 
                    "error"
                )
                return

            self.backend.operation_stack.clear()
            
            if hasattr(self.backend, 'base_data'):
                self.backend.base_data = {}
            if hasattr(self.backend, 'batch_cache'):
                self.backend.batch_cache = {}
                
            self.render_session_timeline()

            self.active_batch_folder = d  
            self._init_slider(d)          
            self.status_bar.configure(text=f"Stare: Set date încărcat '{os.path.basename(d)}'.")
    def hide_left_panel(self):
        self.sidebar_frame.grid_remove()  # Ascunde panoul din stânga
        # Arată butonul mic de deschidere în locul lui
        self.btn_show_left.grid(row=0, column=0, sticky="w", padx=5, pady=20)

    def show_left_panel(self):
        self.btn_show_left.grid_remove()  # Ascunde butonul mic
        self.sidebar_frame.grid()         # Reface panoul complet

    def hide_right_panel(self):
        self.session_panel.grid_remove()  # Ascunde panoul din dreapta
        # Arată butonul mic de deschidere în locul lui
        self.btn_show_right.grid(row=0, column=2, sticky="e", padx=5, pady=20)

    def show_right_panel(self):
        self.btn_show_right.grid_remove() # Ascunde butonul mic
        self.session_panel.grid()         # Reface panoul complet
    def gui_convert_nii(self):
        p = filedialog.askopenfilename(filetypes=[("NIfTI", "*.nii *.nii.gz")])
        if not p: return
        name = self.ask_custom_folder_name("Configurare Export NIfTI", "Introduceți un nume pentru setul 2D rezultat:", os.path.basename(p).split('.')[0])
        if name:
            out = os.path.join("datasets", "converted_2d", name)
            self.status_bar.configure(text=f"Stare: Inițializare decodificare volum NIfTI...")
            self.update_idletasks()
            suc, info = self.backend.convert_nii_volume(p, out)
            if suc:
                self.active_batch_folder = out
                self._init_slider(out)
                self.status_bar.configure(text=f"Stare: Pipeline finalizat cu succes. Navigare activă.")
                self.show_custom_message("Succes Conversie", f"Volumul medical 3D a fost tăiat în {info} felii 2D cu succes.", "info")
            else:
                self.status_bar.configure(text="Stare: Eroare la conversie.")
                self.show_custom_message("Eroare Critică", f"Nu s-a putut converti volumul NIfTI:\n{info}", "error")

    def gui_apply_processing(self):
        # 1. Preluăm alegerile clinice din interfață
        val_obiectiv = self.operator_dropdown.get()
        val_intensitate = self.intensity_dropdown.get()

        # 2. Traducem termenii clinici în parametri tehnici
        harta_operatori = {
            "Filtrare Zgomot de Fond": "Deschidere",
            "Solidificare Structuri": "Închidere",
            "Evidențiere Micro-leziuni": "Top-Hat",
            "Conturare Tumorală": "Gradient",
            "Amplificare Regiuni Întunecate": "Black-Hat"
        }
        harta_intensitate = {
            "Fină": 3,
            "Medie": 5,
            "Puternică": 7
        }

        op = harta_operatori.get(val_obiectiv, "Deschidere")
        ks = harta_intensitate.get(val_intensitate, 3)

        # --- NOUA LOGICĂ UNIFICATĂ ---
        
        # PASUL A: Adăugăm direct în stiva backend-ului
        noua_operatie = {
            "nume_clinic": val_obiectiv,
            "intensitate_text": val_intensitate,
            "nume": op, 
            "kernel": ks
        }
        self.backend.operation_stack.append(noua_operatie)

        # PASUL B: Actualizăm lista vizuală (Timeline-ul din dreapta)
        self.render_session_timeline()
        
        # PASUL C: Cerem backend-ului să recalculeze TOT (inclusiv noul operator adăugat)
        self.backend.recalculate_pipeline()

        # PASUL D: Afișăm rezultatul corect în funcție de tab-ul activ
        if self.tabview.get() == "Pipeline Medical":
            if not getattr(self, 'active_batch_folder', None): 
                self.show_custom_message("Avertisment", "Încărcați un set de date mai întâi.", "error")
                self.backend.operation_stack.pop() # Anulăm adăugarea dacă nu există date
                self.render_session_timeline()
                return
            
            self.status_bar.configure(text=f"Stare: Pipeline actualizat cu {val_obiectiv}.")
            self.btn_save_batch.configure(state="normal") 
            self.on_slice_slider_move(self.slice_slider.get()) 
            
        else:
            # Modul Single Image
            img = self.backend.get_processed_image()
            if img is not None:
                self.display_image(img, self.lbl_proc_img)
                self.status_bar.configure(text=f"Stare: Filtru aplicat pe imaginea curentă.")
            else:
                self.show_custom_message("Avertisment", "Încărcați o imagine înainte de procesare.", "error")
                self.backend.operation_stack.pop() # Anulăm adăugarea dacă nu există imagine
                self.render_session_timeline()
            # 1. Preluăm alegerile clinice din interfață (noile meniuri)
      
    def gui_save_batch(self):
        op = self.operator_var.get()
        ks = int(self.kernel_slider.get())
        sugestie = f"{os.path.basename(self.active_batch_folder)}_{op}_{ks}x{ks}"
        
        name = self.ask_custom_folder_name("Salvare Definitivă", "Introduceți numele directorului de export:", sugestie)
        if name:
            out = os.path.join("datasets", "processed_2d", name)
            suc, count = self.backend.save_batch_from_memory(out)
            if suc:
                self.status_bar.configure(text=f"Stare: Lot de {count} imagini salvat cu succes.")
                self.show_custom_message("Lot Salvat", f"S-au salvat definitiv {count} felii procesate în folderul:\nprocessed_2d/{name}", "info")

    def update_slider_label(self, v):
        val = int(v); 
        if val % 2 == 0: val += 1
        self.sidebar_frame.focus() 
        self.slider_label.configure(text=f"Dimensiune Kernel ({val}x{val}):")

    def display_image(self, cv_img, lbl):
        if cv_img is None:
            return
        
        import cv2
        from PIL import Image
        import customtkinter as ctk
        
        # Logica ta impecabilă de dinainte care făcea conversia din matrice în RGB
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB) if len(cv_img.shape) == 2 else cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        img = ctk.CTkImage(Image.fromarray(rgb), size=(700, 700))
        
        lbl.configure(image=img, text="")
        lbl.image = img

    def update_image_display(self):
        """Update the displayed images (for use when stack is modified)."""
        if self.tabview.get() == "Pipeline Medical" and self.active_batch_folder:
            self.on_slice_slider_move(self.slice_slider.get())
        elif self.backend.get_original_image() is not None:
            self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
            if self.backend.get_processed_image() is not None:
                self.display_image(self.backend.get_processed_image(), self.lbl_proc_img)


    def render_session_timeline(self):
            # Curățăm panoul înainte de fiecare redesenare
            for widget in self.session_scrollable_frame.winfo_children():
                widget.destroy()

            # Parcurgem stiva de operații din backend
            for index, op in enumerate(self.backend.operation_stack):
                
                # Creăm rândul pentru o operație
                row_frame = ctk.CTkFrame(self.session_scrollable_frame, height=60)
                row_frame.pack(fill="x", padx=5, pady=4)
                row_frame.pack_propagate(False) # Păstrăm înălțimea fixă
                
                # 1. Mânerul pentru Drag & Drop (simbolul ☰)
                drag_handle = ctk.CTkLabel(row_frame, text="☰", cursor="hand2", width=20)
                drag_handle.pack(side="left", padx=5)
                
                # Evenimentele pentru Drag & Drop pe mâner
                drag_handle.bind("<ButtonPress-1>", lambda e, idx=index: self.on_drag_start(e, idx))
                drag_handle.bind("<ButtonRelease-1>", lambda e, idx=index: self.on_drag_release(e, idx))
                
                # 2. Textul operației pe două rânduri, cu detaliu de intensitate
                nume_afisat = op.get("nume_clinic", op["nume"])
                intensitate_afisata = op.get("intensitate_text", f"{op['kernel']}x{op['kernel']}")
                text_clar = f"{nume_afisat}\n↳ Intensitate: {intensitate_afisata}"
                
                op_label = ctk.CTkLabel(row_frame, text=text_clar, justify="left", font=("Arial", 12), wraplength=190, anchor="w")
                op_label.pack(side="left", padx=(10, 5), fill="x", expand=True)
                
                # 3. Butonul "X" pentru ștergere specifică
                btn_delete = ctk.CTkButton(row_frame, text="❌", width=32, height=32, fg_color="#581a1a", 
                                        hover_color="#8B0000", text_color="white", border_width=1, border_color="#8B0000",
                                        command=lambda idx=index: self.delete_operation_ui(idx))
                btn_delete.pack(side="right", padx=5, pady=8)
    # --- Logica de Drag & Drop ---

    def on_drag_start(self, event, index):
        # Salvăm coordonata Y de unde începe tragerea
        self.drag_start_y = event.y_root
        self.drag_start_index = index

    def on_drag_release(self, event, start_index):
        # Calculăm diferența de pixeli (cât de mult am tras cu mouse-ul în jos sau în sus)
        delta_y = event.y_root - self.drag_start_y
        
        # Presupunem că un rând are aprox. 40 pixeli înălțime (35 inaltime + 5 padding)
        row_height = 40 
        
        # Calculăm cu câte poziții s-a mutat (pozitiv = în jos, negativ = în sus)
        shift_amount = round(delta_y / row_height)
        
        if shift_amount != 0:
            new_index = start_index + shift_amount
            
            # Trimitem comanda la Backend
            self.backend.move_operation(start_index, new_index)
            
            # Redesenăm interfața și actualizăm imaginea principală
            self.render_session_timeline()
            self.display_image(self.backend.get_processed_image(), self.lbl_proc_img)

    

    def delete_operation_ui(self, index):
        # Verificăm dacă indexul este valid în cadrul stivei de operații
        if 0 <= index < len(self.backend.operation_stack):
            self.backend.operation_stack.pop(index) # Ștergem operația de la indexul respectiv
            self.backend.recalculate_pipeline()     # Cerem backend-ului să recalculeze fără acea operație
            self.render_session_timeline()          # Actualizăm lista vizuală din interfață
            self.update_image_display()
            
            if self.tabview.get() == "Pipeline Medical":
                self.on_slice_slider_move(self.slice_slider.get())
            else:
                img = self.backend.get_processed_image()
                if img is not None:
                    self.display_image(img, self.lbl_proc_img)
                    self.status_bar.configure(text="Stare: Operație ștearsă. Imagine recalculată.")
                else:
                    self.lbl_proc_img.configure(image=None, text="Așteptare prelucrare...")
                    self.status_bar.configure(text="Stare: Istoric gol. Se afișează imaginea originală.")
    
    def reset_session(self):
        self.backend.operation_stack.clear() # Curățăm tot istoricul
        self.backend.recalculate_pipeline()
        self.render_session_timeline()
        self.update_image_display()
        
        # --- NOU: Verificăm în ce mod suntem ---
        if self.tabview.get() == "Pipeline Medical":
            self.on_slice_slider_move(self.slice_slider.get())
        else:
            # În modul Single Image, pur și simplu forțăm reafișarea imaginii curente (care acum e goală/resetată)
            # Presupunem că backend-ul returnează imaginea originală dacă stack-ul e gol
            img = self.backend.get_processed_image() 
            if img is not None:
                self.display_image(img, self.lbl_proc_img)
            else:
                 self.lbl_proc_img.configure(image=None, text="Așteptare prelucrare...")

    def undo_operation(self):
        if len(self.backend.operation_stack) > 0:
            self.backend.operation_stack.pop() # Scoatem ultimul element
            self.backend.recalculate_pipeline()
            self.render_session_timeline()
            self.update_image_display()
            
            # --- NOU: Verificăm în ce mod suntem ---
            if self.tabview.get() == "Pipeline Medical":
                self.on_slice_slider_move(self.slice_slider.get())
            else:
                # Actualizăm eticheta cu noua imagine (calculată fără ultimul operator)
                img = self.backend.get_processed_image()
                if img is not None:
                    self.display_image(img, self.lbl_proc_img)
                else:
                    self.lbl_proc_img.configure(image=None, text="Așteptare prelucrare...")

    def toggle_focus_mode(self):
        # Verificăm dacă suntem în modul Focus (folosind starea vizibilă a sidebar-ului)
        is_focus = not self.sidebar_frame.winfo_viewable()
        
        if is_focus:
            # Revenim la modul de editare
            self.show_left_panel()
            self.show_right_panel()
            self.btn_focus.configure(text="⤢ Mod Focus")
        else:
            # Trecem în modul Focus
            self.hide_left_panel()
            self.hide_right_panel()
            self.btn_focus.configure(text="⤡ Mod Editare")
    