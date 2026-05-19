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
        
        # Pornire automată maximizată pe tout ecranul
        self.after(0, lambda: self.state('zoomed'))

        self.backend = MorphoBackend()
        self.active_batch_folder = None
        self.processed_batch_folder = None
        self.slice_files_list = [] 

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar_frame, text="Meniu Principal", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(25, 15))

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
        
        # BUTON SALVARE LOT
        self.btn_save_batch = ctk.CTkButton(self.tabview.tab("Pipeline Medical"), text="SALVEAZĂ LOTUL", height=40, font=ctk.CTkFont(weight="bold"), fg_color="#28a745", hover_color="#218838", state="disabled", command=self.gui_save_batch)
        self.btn_save_batch.pack(pady=(25, 10), fill="x", padx=10)

        # SETARI GLOBALE
        ctk.CTkLabel(self.sidebar_frame, text="Setări Processare:", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").grid(row=2, column=0, padx=20, pady=(25, 10), sticky="w")
        
        self.operator_var = ctk.StringVar(value="Deschidere")
        ctk.CTkOptionMenu(self.sidebar_frame, variable=self.operator_var, values=["Eroziune", "Dilatare", "Deschidere", "Închidere", "Top-Hat", "Black-Hat"], height=35).grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.slider_label = ctk.CTkLabel(self.sidebar_frame, text="Dimensiune Kernel (3x3):", anchor="w")
        self.slider_label.grid(row=4, column=0, padx=20, pady=(20, 5), sticky="w")
        self.kernel_slider = ctk.CTkSlider(self.sidebar_frame, from_=3, to=15, number_of_steps=6, command=self.update_slider_label)
        self.kernel_slider.set(3)
        self.kernel_slider.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        self.btn_apply = ctk.CTkButton(self.sidebar_frame, text="EXECUȚIE OPERATOR", height=45, font=ctk.CTkFont(size=14, weight="bold"), command=self.gui_apply_processing)
        self.btn_apply.grid(row=6, column=0, padx=20, pady=35, sticky="ew")

    def _build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure((0, 1), weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # IMAGINI
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

        # SLIDER NAVIGARE
        self.nav_frame = ctk.CTkFrame(self.main_frame, height=80, corner_radius=10)
        self.nav_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        
        self.lbl_slice_info = ctk.CTkLabel(self.nav_frame, text="Navigare Felii: - / -", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_slice_info.pack(pady=(10, 0))
        
        self.slice_slider = ctk.CTkSlider(self.nav_frame, from_=0, to=100, number_of_steps=100, button_color="#b35900", button_hover_color="#8c4600", command=self.on_slice_slider_move)
        self.slice_slider.set(0)
        self.slice_slider.pack(fill="x", padx=30, pady=(5, 15))
        self.nav_frame.grid_remove() 

        self.status_bar = ctk.CTkLabel(self.main_frame, text="Stare: Așteptare date de intrare.", anchor="w", font=ctk.CTkFont(size=13), text_color="#a3a3a3")
        self.status_bar.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")

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
        self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
        
        if hasattr(self.backend, 'batch_cache') and file_name in self.backend.batch_cache:
            img_proc = self.backend.batch_cache[file_name]
            self.display_image(img_proc, self.lbl_proc_img)
        else:
            self.lbl_proc_img.configure(image="", text="Apasă 'PREVIZUALIZEAZĂ LOT' pentru rezultat.")
            self.lbl_proc_img.image = None

    def on_tab_change(self):
        tab = self.tabview.get()
        if tab == "Pipeline Medical":
            self.btn_apply.configure(text="PREVIZUALIZEAZĂ LOT", fg_color="#b35900", hover_color="#8c4600")
            if self.active_batch_folder: self.nav_frame.grid()
        else:
            self.btn_apply.configure(text="EXECUȚIE OPERATOR", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#3269a0", "#14395e"])
            self.nav_frame.grid_remove()

    def _init_slider(self, folder_path):
        self.slice_files_list = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
        if self.slice_files_list:
            count = len(self.slice_files_list)
            self.slice_slider.configure(from_=0, to=count-1, number_of_steps=count-1)
            self.slice_slider.set(count // 2)
            self.nav_frame.grid()
            self.btn_save_batch.configure(state="disabled") 
            if hasattr(self.backend, 'batch_cache'):
                self.backend.batch_cache.clear() 
            self.on_slice_slider_move(count // 2)

    def gui_load_image(self):
        p = filedialog.askopenfilename()
        if p and self.backend.load_image(p):
            self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
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

            self.active_batch_folder = d  
            self._init_slider(d)          
            self.status_bar.configure(text=f"Stare: Set date încărcat '{os.path.basename(d)}'.")

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
        op = self.operator_var.get()
        ks = int(self.kernel_slider.get())
        if self.tabview.get() == "Pipeline Medical":
            if not self.active_batch_folder: 
                self.show_custom_message("Avertisment", "Vă rugăm să încărcați un set de date existent sau să convertiți un volum .nii mai întâi.", "error")
                return
            
            self.status_bar.configure(text=f"Stare: Se procesează {op} ({ks}x{ks}) în memoria RAM... Așteptați.")
            self.update_idletasks()
            
            suc, count = self.backend.batch_process_to_memory(self.active_batch_folder, op, ks)
            if suc:
                self.status_bar.configure(text=f"Stare: Pipeline finalizat cu succes. Navigare activă.")
                self.btn_save_batch.configure(state="normal") 
                self.on_slice_slider_move(self.slice_slider.get()) 
        else:
            if self.backend.apply_operator(op, ks):
                self.display_image(self.backend.get_processed_image(), self.lbl_proc_img)
                self.status_bar.configure(text=f"Stare: Filtru aplicat pe imaginea curentă.")
            else:
                self.show_custom_message("Avertisment", "Încărcați o imagine binară/grayscale înainte de a aplica operatorul.", "error")

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
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB) if len(cv_img.shape)==2 else cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        img = ctk.CTkImage(Image.fromarray(rgb), size=(500, 500))
        lbl.configure(image=img, text="")
        lbl.image = img

if __name__ == "__main__":
    app = MorphoApp()
    app.mainloop()