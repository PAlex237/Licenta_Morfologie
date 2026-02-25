import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import cv2

# Importăm clasa de Backend!
from backend_morph import MorphoBackend

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class MorphoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Prelucrare Morfologică - Prototip Modular")
        self.geometry("1100x700")

        # Instanțiem Backend-ul
        self.backend = MorphoBackend()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        """Construiește panoul din stânga."""
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar_frame, text="Panou Control", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)

        ctk.CTkButton(self.sidebar_frame, text="Încărcare Imagine", command=self.gui_load_image).grid(row=1, column=0, padx=20, pady=10)
        ctk.CTkButton(self.sidebar_frame, text="Salvare Rezultat", fg_color="green", command=self.gui_save_image).grid(row=2, column=0, padx=20, pady=10)

        ctk.CTkLabel(self.sidebar_frame, text="Selectare Operator:", anchor="w").grid(row=4, column=0, padx=20, pady=(10, 0))
        self.operator_var = ctk.StringVar(value="Deschidere")
        ctk.CTkOptionMenu(self.sidebar_frame, variable=self.operator_var, values=["Eroziune", "Dilatare", "Deschidere", "Închidere", "Top-Hat", "Black-Hat"]).grid(row=5, column=0, padx=20, pady=(10, 20))

        self.slider_label = ctk.CTkLabel(self.sidebar_frame, text="Dimensiune Kernel (3x3):", anchor="w")
        self.slider_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.kernel_slider = ctk.CTkSlider(self.sidebar_frame, from_=3, to=15, number_of_steps=6, command=self.update_slider_label)
        self.kernel_slider.set(3)
        self.kernel_slider.grid(row=7, column=0, padx=20, pady=(10, 20))

        ctk.CTkButton(self.sidebar_frame, text="APLICĂ PROCESARE", height=40, font=ctk.CTkFont(weight="bold"), command=self.gui_apply_processing).grid(row=8, column=0, padx=20, pady=20)

    def _build_main_area(self):
        """Construiește zona de afișare a imaginilor."""
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure((0, 1), weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Original
        frame_orig = ctk.CTkFrame(self.main_frame)
        frame_orig.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame_orig, text="Imagine Originală", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.lbl_orig_img = ctk.CTkLabel(frame_orig, text="Nicio imagine încărcată")
        self.lbl_orig_img.pack(expand=True, fill="both", padx=10, pady=10)

        # Procesat
        frame_proc = ctk.CTkFrame(self.main_frame)
        frame_proc.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame_proc, text="Rezultat Procesare", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.lbl_proc_img = ctk.CTkLabel(frame_proc, text="Niciun rezultat")
        self.lbl_proc_img.pack(expand=True, fill="both", padx=10, pady=10)

        self.status_bar = ctk.CTkLabel(self.main_frame, text="Stare: Așteptare input...", anchor="w", text_color="lightgreen")
        self.status_bar.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

    # --- METODE CARE COMUNICĂ CU BACKEND-UL ---

    def update_slider_label(self, value):
        val = int(value)
        if val % 2 == 0: val += 1
        self.slider_label.configure(text=f"Dimensiune Kernel ({val}x{val}):")

    def gui_load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif")])
        if file_path:
            success = self.backend.load_image(file_path)
            if success:
                # Afișăm imaginea originală nouă
                self.display_image(self.backend.get_original_image(), self.lbl_orig_img)
                
                # --- AICI ESTE MODIFICAREA ---
                # Curățăm zona de imagine procesată (o facem goală)
                self.lbl_proc_img.configure(image="", text="Așteaptă procesarea...")
                self.lbl_proc_img.image = None # Ștergem și referința din memorie
                # -----------------------------
                
                self.status_bar.configure(text="Imagine încărcată cu succes.")
            else:
                messagebox.showerror("Eroare", "Nu s-a putut citi imaginea.")
    def gui_save_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png")])
        if file_path:
            success = self.backend.save_image(file_path)
            if success:
                self.status_bar.configure(text=f"Salvat la: {file_path}")
            else:
                messagebox.showwarning("Avertisment", "Nu există imagine de salvat!")

    def gui_apply_processing(self):
        operator = self.operator_var.get()
        k_size = int(self.kernel_slider.get())
        
        self.status_bar.configure(text="Se procesează...")
        self.update_idletasks()

        # Cerem backend-ului să calculeze
        success = self.backend.apply_operator(operator, k_size)
        
        if success:
            self.display_image(self.backend.get_processed_image(), self.lbl_proc_img)
            self.status_bar.configure(text=f"Stare: Procesare {operator} finalizată!")
        else:
            messagebox.showwarning("Avertisment", "Încărcați o imagine mai întâi!")

    def display_image(self, cv_img, label_widget):
        """Converteste matricea OpenCV pt a fi afisata in GUI."""
        if len(cv_img.shape) == 2: 
            img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(img_rgb)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(400, 500))
        label_widget.configure(image=ctk_img, text="")
        label_widget.image = ctk_img