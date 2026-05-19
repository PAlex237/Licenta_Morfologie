import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import cv2
import os

from backend_morph import MorphoBackend

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class MorphoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Prelucrare Morfologică - Pipeline Medical Automatizat")
        self.geometry("1150x750")

        self.backend = MorphoBackend()
        self.active_batch_folder = None  # Memorează folderul sursă curent pentru Pipeline

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        """Construiește panoul din stânga cu meniurile structurate pe tab-uri."""
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar_frame, text="Meniu Principal", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- TABVIEW PENTRU SCHIMBAREA MODULUI DE LUCRU ---
        self.tabview = ctk.CTkTabview(self.sidebar_frame, command=self.on_tab_change)
        self.tabview.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        
        self.tabview.add("Single Image")
        self.tabview.add("Pipeline Medical")
        
        # --- CONTINUT TAB: SINGLE IMAGE ---
        ctk.CTkButton(self.tabview.tab("Single Image"), text="Încărcare Imagine", command=self.gui_load_image).pack(pady=(15, 10), fill="x", padx=10)
        ctk.CTkButton(self.tabview.tab("Single Image"), text="Salvare Rezultat", fg_color="green", hover_color="#006400", command=self.gui_save_image).pack(pady=10, fill="x", padx=10)

        # --- CONTINUT TAB: PIPELINE MEDICAL ---
        ctk.CTkButton(self.tabview.tab("Pipeline Medical"), text="Conversie Nouă (.nii)", fg_color="#1f538d", command=self.gui_convert_nii).pack(pady=(15, 10), fill="x", padx=10)
        ctk.CTkButton(self.tabview.tab("Pipeline Medical"), text="Încarcă Set Existent", fg_color="#b35900", hover_color="#8c4600", command=self.gui_load_dataset).pack(pady=10, fill="x", padx=10)

        # --- COMENZI GLOBALE (Vizibile indiferent de tab) ---
        ctk.CTkLabel(self.sidebar_frame, text="Setări Procesare:", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=2, column=0, padx=20, pady=(20, 5))
        
        self.operator_var = ctk.StringVar(value="Deschidere")
        ctk.CTkOptionMenu(self.sidebar_frame, variable=self.operator_var, values=["Eroziune", "Dilatare", "Deschidere", "Închidere", "Top-Hat", "Black-Hat"]).grid(row=3, column=0, padx=20, pady=5)

        self.slider_label = ctk.CTkLabel(self.sidebar_frame, text="Dimensiune Kernel (3x3):", anchor="w")
        self.slider_label.grid(row=4, column=0, padx=20, pady=(15, 0))
        self.kernel_slider = ctk.CTkSlider(self.sidebar_frame, from_=3, to=15, number_of_steps=6, command=self.update_slider_label)
        self.kernel_slider.set(3)
        self.kernel_slider.grid(row=5, column=0, padx=20, pady=5)

        # BUTON EXECUTĂ (Dinamic în funcție de tab)
        self.btn_apply = ctk.CTkButton(self.sidebar_frame, text="APLICĂ PE IMAGINE", height=40, font=ctk.CTkFont(weight="bold"), command=self.gui_apply_processing)
        self.btn_apply.grid(row=6, column=0, padx=20, pady=30)

    def _build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure((0, 1), weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Original
        frame_orig = ctk.CTkFrame(self.main_frame)
        frame_orig.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame_orig, text="Imagine Originală / Sursă", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.lbl_orig_img = ctk.CTkLabel(frame_orig, text="Nicio imagine încărcată")
        self.lbl_orig_img.pack(expand=True, fill="both", padx=10, pady=10)

        # Procesat
        frame_proc = ctk.CTkFrame(self.main_frame)
        frame_proc.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.lbl_proc_title = ctk.CTkLabel(frame_proc, text="Rezultat Procesare", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_proc_title.pack(pady=10)
        self.lbl_proc_img = ctk.CTkLabel(frame_proc, text="Niciun rezultat")
        self.lbl_proc_img.pack(expand=True, fill="both", padx=10, pady=10)

        self.status_bar = ctk.CTkLabel(self.main_frame, text="Stare: Așteptare input...", anchor="w", text_color="lightgreen")
        self.status_bar.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

    def ask_custom_folder_name(self, title, prompt, initial_value):
        """Creează un popup modern centrat pe aplicație."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        
        dialog_width = 450
        dialog_height = 220
        self.update_idletasks()
        
        app_x = self.winfo_rootx()
        app_y = self.winfo_rooty()
        app_width = self.winfo_width()
        app_height = self.winfo_height()
        
        pos_x = app_x + (app_width // 2) - (dialog_width // 2)
        pos_y = app_y + (app_height // 2) - (dialog_height // 2)
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        lbl = ctk.CTkLabel(dialog, text=prompt, font=ctk.CTkFont(size=14))
        lbl.pack(pady=(20, 10), padx=20)

        entry = ctk.CTkEntry(dialog, width=350, font=ctk.CTkFont(size=14))
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

        btn_ok = ctk.CTkButton(btn_frame, text="OK", width=100, command=on_submit)
        btn_ok.pack(side="left", padx=10)

        btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", width=100, fg_color="gray", hover_color="#555555", command=on_cancel)
        btn_cancel.pack(side="left", padx=10)

        self.wait_window(dialog)
        return result[0]

    def update_slider_label(self, value):
        val = int(value)
        if val % 2 == 0: val += 1
        self.slider_label.configure(text=f"Dimensiune Kernel ({val}x{val}):")

    def on_tab_change(self):
        """Schimbă textul și culoarea butonului de execuție în funcție de meniul activ."""
        current_tab = self.tabview.get()
        if current_tab == "Pipeline Medical":
            self.btn_apply.configure(text="PROCESEAZĂ TOT SETUL", fg_color="#b35900", hover_color="#8c4600")
            self.status_bar.configure(text="Stare: Mod Pipeline activ. Operația se va aplica pe întregul folder.")
        else:
            self.btn_apply.configure(text="APLICĂ PE IMAGINE", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#3269a0", "#14395e"])
            self.status_bar.configure(text="Stare: Mod Single activ. Procesare doar pe imaginea curentă.")

    def gui_load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif")])
        if file_path:
            success = self.backend.load_image(file_path)
            if success:
                self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
                self.lbl_proc_img.configure(image="", text="Așteaptă procesarea...")
                self.lbl_proc_img.image = None
                self.status_bar.configure(text=f"Imagine încărcată: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Eroare", "Nu s-a putut citi imaginea.")

    def gui_save_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png")])
        if file_path:
            success = self.backend.save_image(file_path)
            if success:
                self.status_bar.configure(text=f"Salvat la: {file_path}")

    def gui_load_dataset(self):
        """NOU: Încarcă un folder cu imagini deja convertite."""
        # Presupunem că folderele noastre stau în datasets/converted_2d
        initial_dir = os.path.abspath(os.path.join("datasets", "converted_2d"))
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir, exist_ok=True)
            
        folder_path = filedialog.askdirectory(title="Selectează setul de date convertit", initialdir=initial_dir)
        if not folder_path:
            return
            
        # Verificăm dacă sunt poze png în el
        files = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
        if not files:
            messagebox.showerror("Eroare", f"Folderul '{os.path.basename(folder_path)}' nu conține imagini .png!")
            return
            
        self.active_batch_folder = folder_path
        count = len(files)
        middle_idx = count // 2
        preview_path = os.path.join(folder_path, files[middle_idx])
        
        # Încărcăm preview-ul pe ecran
        self.backend.load_image(preview_path)
        self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
        self.lbl_proc_img.configure(image="", text="Așteaptă procesarea lotului...")
        
        self.status_bar.configure(text=f"Set date încărcat: '{os.path.basename(folder_path)}' ({count} imagini).")

    def gui_convert_nii(self):
        file_path = filedialog.askopenfilename(filetypes=[("NIfTI medical files", "*.nii *.nii.gz")])
        if not file_path:
            return
            
        base_name = os.path.basename(file_path).replace('.nii.gz', '').replace('.nii', '')
        custom_folder_name = self.ask_custom_folder_name("Nume Folder", "Introduceți numele folderului pentru salvare:", initial_value=base_name)
        if not custom_folder_name:
            return
            
        output_dir = os.path.join("datasets", "converted_2d", custom_folder_name)
        self.status_bar.configure(text=f"Se convertește volumul în {custom_folder_name}... Așteptați...")
        self.update_idletasks()
        
        success, info = self.backend.convert_nii_volume(file_path, output_folder=output_dir)
        
        if success:
            self.active_batch_folder = output_dir 
            num_slices = info 
            
            self.status_bar.configure(text=f"Succes! S-au extras {num_slices} felii în '{output_dir}'.")
            
            # Ne bazăm pe sistemul de fișiere pentru a găsi fix fisierul din mijloc
            files = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
            middle_idx = len(files) // 2
            preview_path = os.path.join(output_dir, files[middle_idx])
                
            if os.path.exists(preview_path):
                self.backend.load_image(preview_path)
                self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
                self.lbl_proc_img.configure(image="", text="Așteaptă procesarea lotului...")
        else:
            self.status_bar.configure(text="Eroare la conversie.")
            messagebox.showerror("Eroare", f"Eroare conversie: {info}")

    def gui_apply_processing(self):
        operator = self.operator_var.get()
        k_size = int(self.kernel_slider.get())
        current_tab = self.tabview.get()
        
        if current_tab == "Pipeline Medical":
            # --- MOD BATCH (PROCESARE FOLDER) ---
            if not self.active_batch_folder:
                messagebox.showwarning("Avertisment", "Nu există niciun set de date activ! Vă rugăm să încărcați un set existent sau să convertiți un .nii.")
                return

            parent_folder_name = os.path.basename(self.active_batch_folder)
            sugestie = f"{parent_folder_name}_{operator}_{k_size}x{k_size}"
            
            custom_folder_name = self.ask_custom_folder_name("Salvare Procesare Lot", "Introduceți numele folderului pentru rezultate:", initial_value=sugestie)
            if not custom_folder_name:
                return 
                
            output_dir = os.path.join("datasets", "processed_2d", custom_folder_name)
            self.status_bar.configure(text=f"Se procesează setul în '{custom_folder_name}'...")
            self.update_idletasks()
            
            success, count = self.backend.batch_process_folder(input_folder=self.active_batch_folder, output_folder=output_dir, operator=operator, k_size=k_size)
            if success:
                self.status_bar.configure(text=f"Pipeline finalizat! Salvat în '{output_dir}'.")
                
                files = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
                if files:
                    middle_idx = len(files) // 2
                    preview_path = os.path.join(output_dir, files[middle_idx])
                    if os.path.exists(preview_path):
                        img_proc = cv2.imread(preview_path, cv2.IMREAD_GRAYSCALE)
                        self.display_image(img_proc, self.lbl_proc_img)
            else:
                messagebox.showwarning("Eroare", count)
        else:
            # --- MOD SINGLE (POZĂ INDIVIDUALĂ) ---
            self.status_bar.configure(text="Se procesează imaginea...")
            self.update_idletasks()
            success = self.backend.apply_operator(operator, k_size)
            if success:
                self.display_image(self.backend.get_processed_image(), self.lbl_proc_img)
                self.status_bar.configure(text=f"Procesare {operator} finalizată!")
            else:
                messagebox.showwarning("Avertisment", "Încărcați o imagine mai întâi din meniul 'Single Image'!")

    def display_image(self, cv_img, label_widget):
        if len(cv_img.shape) == 2: 
            img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(img_rgb)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(400, 500))
        label_widget.configure(image=ctk_img, text="")
        label_widget.image = ctk_img

if __name__ == "__main__":
    app = MorphoApp()
    app.mainloop()