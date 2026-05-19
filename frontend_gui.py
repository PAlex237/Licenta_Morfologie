import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image
import cv2
import os

from backend_morph import MorphoBackend

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class MorphoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MorphoMed - Medical Slice Viewer & Processor")
        self.geometry("1200x850")

        self.backend = MorphoBackend()
        self.active_batch_folder = None
        self.processed_batch_folder = None # Folderul unde stau rezultatele curente
        self.slice_files_list = [] # Lista cu numele fisierelor (ex: slice_001.png)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar_frame, text="Meniu Principal", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))

        self.tabview = ctk.CTkTabview(self.sidebar_frame, command=self.on_tab_change)
        self.tabview.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        self.tabview.add("Single Image")
        self.tabview.add("Pipeline Medical")
        
        # TAB: SINGLE
        ctk.CTkButton(self.tabview.tab("Single Image"), text="Încărcare Imagine", command=self.gui_load_image).pack(pady=(15, 10), fill="x", padx=10)
        ctk.CTkButton(self.tabview.tab("Single Image"), text="Salvare Rezultat", fg_color="green", command=self.gui_save_image).pack(pady=10, fill="x", padx=10)

        # TAB: PIPELINE
        ctk.CTkButton(self.tabview.tab("Pipeline Medical"), text="Conversie Nouă (.nii)", fg_color="#1f538d", command=self.gui_convert_nii).pack(pady=(15, 10), fill="x", padx=10)
        ctk.CTkButton(self.tabview.tab("Pipeline Medical"), text="Încarcă Set Existent", fg_color="#b35900", command=self.gui_load_dataset).pack(pady=10, fill="x", padx=10)

        # SETARI GLOBALE
        ctk.CTkLabel(self.sidebar_frame, text="Setări Procesare:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=20, pady=(20, 5))
        self.operator_var = ctk.StringVar(value="Deschidere")
        ctk.CTkOptionMenu(self.sidebar_frame, variable=self.operator_var, values=["Eroziune", "Dilatare", "Deschidere", "Închidere", "Top-Hat", "Black-Hat"]).grid(row=3, column=0, padx=20, pady=5)

        self.slider_label = ctk.CTkLabel(self.sidebar_frame, text="Dimensiune Kernel (3x3):")
        self.slider_label.grid(row=4, column=0, padx=20, pady=(15, 0))
        self.kernel_slider = ctk.CTkSlider(self.sidebar_frame, from_=3, to=15, number_of_steps=6, command=self.update_slider_label)
        self.kernel_slider.set(3)
        self.kernel_slider.grid(row=5, column=0, padx=20, pady=5)

        self.btn_apply = ctk.CTkButton(self.sidebar_frame, text="APLICĂ PE IMAGINE", height=40, font=ctk.CTkFont(weight="bold"), command=self.gui_apply_processing)
        self.btn_apply.grid(row=6, column=0, padx=20, pady=30)

    def _build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure((0, 1), weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # IMAGINI
        frame_orig = ctk.CTkFrame(self.main_frame)
        frame_orig.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame_orig, text="Original / Sursă", font=ctk.CTkFont(size=16)).pack(pady=10)
        self.lbl_orig_img = ctk.CTkLabel(frame_orig, text="Așteptare...")
        self.lbl_orig_img.pack(expand=True, fill="both", padx=10, pady=10)

        frame_proc = ctk.CTkFrame(self.main_frame)
        frame_proc.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame_proc, text="Rezultat Procesare", font=ctk.CTkFont(size=16)).pack(pady=10)
        self.lbl_proc_img = ctk.CTkLabel(frame_proc, text="Așteptare...")
        self.lbl_proc_img.pack(expand=True, fill="both", padx=10, pady=10)

        # --- SLIDER NAVIGARE (NOU) ---
        self.nav_frame = ctk.CTkFrame(self.main_frame, height=80)
        self.nav_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        self.lbl_slice_info = ctk.CTkLabel(self.nav_frame, text="Navigare Felii: - / -")
        self.lbl_slice_info.pack()
        
        self.slice_slider = ctk.CTkSlider(self.nav_frame, from_=0, to=100, number_of_steps=100, command=self.on_slice_slider_move)
        self.slice_slider.set(0)
        self.slice_slider.pack(fill="x", padx=20, pady=5)
        self.nav_frame.grid_remove() # Ascuns initial

        self.status_bar = ctk.CTkLabel(self.main_frame, text="Gata.", anchor="w", text_color="lightgreen")
        self.status_bar.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

    def on_slice_slider_move(self, value):
        """Sincronizează ambele ferestre când miști slider-ul."""
        if not self.slice_files_list: return
        
        idx = int(value)
        file_name = self.slice_files_list[idx]
        self.lbl_slice_info.configure(text=f"Navigare Felii: {idx + 1} / {len(self.slice_files_list)} ({file_name})")
        
        # 1. Incarca originalul
        orig_path = os.path.join(self.active_batch_folder, file_name)
        self.backend.load_image(orig_path)
        self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
        
        # 2. Incarca procesatul (daca exista)
        if self.processed_batch_folder:
            proc_path = os.path.join(self.processed_batch_folder, file_name)
            if os.path.exists(proc_path):
                img_proc = cv2.imread(proc_path, cv2.IMREAD_GRAYSCALE)
                self.display_image(img_proc, self.lbl_proc_img)

    def on_tab_change(self):
        tab = self.tabview.get()
        if tab == "Pipeline Medical":
            self.btn_apply.configure(text="PROCESEAZĂ TOT SETUL", fg_color="#b35900")
            if self.active_batch_folder: self.nav_frame.grid()
        else:
            self.btn_apply.configure(text="APLICĂ PE IMAGINE", fg_color="#1f538d")
            self.nav_frame.grid_remove()

    def _init_slider(self, folder_path):
        """Resetează slider-ul pentru noul set de date."""
        self.slice_files_list = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
        if self.slice_files_list:
            count = len(self.slice_files_list)
            self.slice_slider.configure(from_=0, to=count-1, number_of_steps=count-1)
            self.slice_slider.set(count // 2)
            self.nav_frame.grid()
            self.on_slice_slider_move(count // 2)

    def ask_custom_folder_name(self, title, prompt, init):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("400x200")
        # Centrare
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width()//2) - 200
        y = self.winfo_rooty() + (self.winfo_height()//2) - 100
        dialog.geometry(f"400x200+{x}+{y}")
        dialog.transient(self); dialog.grab_set()
        ctk.CTkLabel(dialog, text=prompt).pack(pady=15)
        entry = ctk.CTkEntry(dialog, width=300); entry.insert(0, init); entry.pack()
        res = [None]
        def sub(): res[0] = entry.get(); dialog.destroy()
        ctk.CTkButton(dialog, text="OK", command=sub).pack(pady=20)
        self.wait_window(dialog)
        return res[0]

    def gui_load_image(self):
        p = filedialog.askopenfilename()
        if p and self.backend.load_image(p):
            self.display_image(self.backend.get_original_image(), self.lbl_orig_img)

    def gui_save_image(self):
        p = filedialog.asksaveasfilename(defaultextension=".png")
        if p: self.backend.save_image(p)

    def gui_load_dataset(self):
        d = filedialog.askdirectory(initialdir="datasets/converted_2d")
        if d:
            self.active_batch_folder = d
            self.processed_batch_folder = None
            self._init_slider(d)

    def gui_convert_nii(self):
        p = filedialog.askopenfilename(filetypes=[("NIfTI", "*.nii *.nii.gz")])
        if not p: return
        name = self.ask_custom_folder_name("Conversie", "Nume folder:", os.path.basename(p).split('.')[0])
        if name:
            out = os.path.join("datasets", "converted_2d", name)
            suc, info = self.backend.convert_nii_volume(p, out)
            if suc:
                self.active_batch_folder = out
                self.processed_batch_folder = None
                self._init_slider(out)

    def gui_apply_processing(self):
        op = self.operator_var.get()
        ks = int(self.kernel_slider.get())
        if self.tabview.get() == "Pipeline Medical":
            if not self.active_batch_folder: return
            sug = f"{os.path.basename(self.active_batch_folder)}_{op}_{ks}x{ks}"
            name = self.ask_custom_folder_name("Batch", "Folder rezultat:", sug)
            if name:
                out = os.path.join("datasets", "processed_2d", name)
                suc, count = self.backend.batch_process_folder(self.active_batch_folder, out, op, ks)
                if suc:
                    self.processed_batch_folder = out
                    self.on_slice_slider_move(self.slice_slider.get())
        else:
            if self.backend.apply_operator(op, ks):
                self.display_image(self.backend.get_processed_image(), self.lbl_proc_img)

    def update_slider_label(self, v):
        val = int(v); 
        if val % 2 == 0: val += 1
        self.slider_label.configure(text=f"Dimensiune Kernel ({val}x{val}):")

    def display_image(self, cv_img, lbl):
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB) if len(cv_img.shape)==2 else cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        img = ctk.CTkImage(Image.fromarray(rgb), size=(450, 450))
        lbl.configure(image=img, text=""); lbl.image = img

if __name__ == "__main__":
    app = MorphoApp(); app.mainloop()