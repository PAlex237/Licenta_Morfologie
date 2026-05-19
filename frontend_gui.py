import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import cv2
import os
from tkinter import filedialog, messagebox, simpledialog
from backend_morph import MorphoBackend

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class MorphoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Prelucrare Morfologică - Pipeline Medical Automatizat")
        self.geometry("1150x750")

        self.backend = MorphoBackend()
        self.active_batch_folder = None
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        """Construiește panoul din stânga cu toate comenzile."""
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar_frame, text="Panou Control", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))

        # OPERAȚII STANDARD
        ctk.CTkButton(self.sidebar_frame, text="Încărcare Imagine (2D)", command=self.gui_load_image).grid(row=1, column=0, padx=20, pady=5)
        ctk.CTkButton(self.sidebar_frame, text="Salvare Rezultat", fg_color="green", command=self.gui_save_image).grid(row=2, column=0, padx=20, pady=5)

        ctk.CTkLabel(self.sidebar_frame, text="Selectare Operator:", anchor="w").grid(row=3, column=0, padx=20, pady=(10, 0))
        self.operator_var = ctk.StringVar(value="Deschidere")
        ctk.CTkOptionMenu(self.sidebar_frame, variable=self.operator_var, values=["Eroziune", "Dilatare", "Deschidere", "Închidere", "Top-Hat", "Black-Hat"]).grid(row=4, column=0, padx=20, pady=5)

        self.slider_label = ctk.CTkLabel(self.sidebar_frame, text="Dimensiune Kernel (3x3):", anchor="w")
        self.slider_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.kernel_slider = ctk.CTkSlider(self.sidebar_frame, from_=3, to=15, number_of_steps=6, command=self.update_slider_label)
        self.kernel_slider.set(3)
        self.kernel_slider.grid(row=6, column=0, padx=20, pady=5)

        # CONFIGURARE MOD PROCESSARE (SINGLE VS BATCH)
        self.batch_mode_var = ctk.BooleanVar(value=False)
        self.batch_switch = ctk.CTkSwitch(self.sidebar_frame, text="Mod Batch (Tot folderul)", variable=self.batch_mode_var, command=self.toggle_batch_mode)
        self.batch_switch.grid(row=7, column=0, padx=20, pady=10)

        # BUTON EXECUTĂ
        self.btn_apply = ctk.CTkButton(self.sidebar_frame, text="APLICĂ PROCESARE", height=40, font=ctk.CTkFont(weight="bold"), command=self.gui_apply_processing)
        self.btn_apply.grid(row=8, column=0, padx=20, pady=15)

        # PIPELINE MEDICAL (.NII)
        ctk.CTkLabel(self.sidebar_frame, text="-----------------------------------", text_color="gray").grid(row=9, column=0, pady=5)
        ctk.CTkLabel(self.sidebar_frame, text="Pipeline Medical (3D)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1f538d").grid(row=10, column=0, padx=20, pady=2)
        
        ctk.CTkButton(self.sidebar_frame, text="Convertește Volum .nii", fg_color="#1f538d", command=self.gui_convert_nii).grid(row=11, column=0, padx=20, pady=10)

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

    def update_slider_label(self, value):
        val = int(value)
        if val % 2 == 0: val += 1
        self.slider_label.configure(text=f"Dimensiune Kernel ({val}x{val}):")

    def toggle_batch_mode(self):
        if self.batch_mode_var.get():
            self.btn_apply.configure(text="APLICĂ PE TOT FOLDERUL", fg_color="orange", hover_color="#cc7a00")
            self.status_bar.configure(text="Stare: Mod Batch activat. Operația se va aplica pe tot folderul converted_2d.")
        else:
            self.btn_apply.configure(text="APLICĂ PROCESARE", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#3269a0", "#14395e"])
            self.status_bar.configure(text="Stare: Mod Single activat. Procesare pe imaginea curentă.")

    def gui_load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif")])
        if file_path:
            success = self.backend.load_image(file_path)
            if success:
                self.active_batch_folder = os.path.dirname(file_path) # <--- Reține folderul sursă
                # ... restul codului ramane la fel ...
                self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
                self.lbl_proc_img.configure(image="", text="Așteaptă procesarea...")
                self.lbl_proc_img.image = None
                self.status_bar.configure(text=f"Imagine încărcată: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Eroare", "Nu s-a putut citi imaginea.")

    def gui_save_image(self):
        if self.batch_mode_var.get():
            messagebox.showinfo("Informație", "În modul Batch, salvarea se face automat în datasets/processed_2d/!")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png")])
        if file_path:
            success = self.backend.save_image(file_path)
            if success:
                self.status_bar.configure(text=f"Salvat la: {file_path}")

    def gui_convert_nii(self):
        file_path = filedialog.askopenfilename(filetypes=[("NIfTI medical files", "*.nii *.nii.gz")])
        if not file_path:
            return
            
        # 1. Generăm sugestia de nume bazată pe fișier (fără extensii)
        base_name = os.path.basename(file_path).replace('.nii.gz', '').replace('.nii', '')
        
        # 2. Deschidem popup-ul cu sugestia precompletată
        custom_folder_name = simpledialog.askstring("Nume Folder", 
                                                    "Introduceți numele folderului pentru salvare:", 
                                                    initialvalue=base_name)
        
        # Dacă utilizatorul a dat Cancel, oprim execuția
        if not custom_folder_name:
            return
            
        # 3. Construim calea finală
        output_dir = os.path.join("datasets", "converted_2d", custom_folder_name)
            
        self.status_bar.configure(text=f"Se convertește volumul în {custom_folder_name}... Așteptați...")
        self.update_idletasks()
        
        # Trimitem calea personalizată către Backend
        success, info = self.backend.convert_nii_volume(file_path, output_folder=output_dir)
        
        if success:
            self.active_batch_folder = output_dir # Salvăm folderul ca "activ" pentru procesare
            num_slices = info 
            middle_idx = num_slices // 2 
            
            self.status_bar.configure(text=f"Succes! S-au extras {num_slices} felii în '{output_dir}'.")
            messagebox.showinfo("Succes", f"Volumul a fost tăiat în {num_slices} felii 2D!\nLocație: {output_dir}")
            
            nume_fisier = f"slice_{middle_idx:03d}.png"
            preview_path = os.path.join(output_dir, nume_fisier) 
            
            if not os.path.exists(preview_path):
                preview_path = os.path.join(output_dir, "slice_000.png")
                
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
        
        if self.batch_mode_var.get():
            # Ne asigurăm că știm ce folder procesăm
            if not self.active_batch_folder:
                messagebox.showwarning("Avertisment", "Nu există niciun folder activ! Vă rugăm să convertiți un volum .nii sau să încărcați o imagine dintr-un folder.")
                return

            # Construim sugestia inteligentă de nume
            parent_folder_name = os.path.basename(self.active_batch_folder)
            sugestie = f"{parent_folder_name}_{operator}_{k_size}x{k_size}"
            
            # Cerem confirmarea/modificarea utilizatorului
            custom_folder_name = simpledialog.askstring("Salvare Procesare Lot", 
                                                        "Introduceți numele folderului pentru rezultate:", 
                                                        initialvalue=sugestie)
            
            if not custom_folder_name:
                return # Utilizatorul a dat Cancel
                
            output_dir = os.path.join("datasets", "processed_2d", custom_folder_name)

            self.status_bar.configure(text=f"Se procesează lotul în {custom_folder_name}...")
            self.update_idletasks()
            
            # Apelăm Backend-ul cu folderele personalizate
            success, count = self.backend.batch_process_folder(input_folder=self.active_batch_folder, 
                                                               output_folder=output_dir, 
                                                               operator=operator, 
                                                               k_size=k_size)
            if success:
                self.status_bar.configure(text=f"Mod Batch finalizat! Salvat în '{output_dir}'.")
                messagebox.showinfo("Succes Batch", f"S-au procesat {count} imagini!\nRezultatele sunt în: {output_dir}")
                
                middle_idx = count // 2
                nume_fisier = f"slice_{middle_idx:03d}.png"
                preview_path = os.path.join(output_dir, nume_fisier)
                
                if not os.path.exists(preview_path):
                    preview_path = os.path.join(output_dir, "slice_000.png")
                
                if os.path.exists(preview_path):
                    img_proc = cv2.imread(preview_path, cv2.IMREAD_GRAYSCALE)
                    self.display_image(img_proc, self.lbl_proc_img)
            else:
                messagebox.showwarning("Eroare", count)

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