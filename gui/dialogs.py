"""
Ferestre de dialog personalizate.
"""

import customtkinter as ctk
from typing import Optional, List

def show_custom_message(parent, title: str, message: str, msg_type: str = "info"):
    """Afișează o fereastră simplă de informare sau eroare."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    w, h = 420, 200
    parent.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() // 2 - w // 2
    y = parent.winfo_rooty() + parent.winfo_height() // 2 - h // 2
    dialog.geometry(f"{w}x{h}+{x}+{y}")
    dialog.resizable(False, False)
    dialog.transient(parent)
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
    parent.wait_window(dialog)


def ask_label_name(parent) -> Optional[str]:
    """Dialog hibrid: Selectează din listă sau scrie text propriu."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Etichetă Nouă")
    w, h = 400, 200
    parent.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() // 2 - w // 2
    y = parent.winfo_rooty() + parent.winfo_height() // 2 - h // 2
    dialog.geometry(f"{w}x{h}+{x}+{y}")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    ctk.CTkLabel(dialog, text="Selectați sau introduceți eticheta medicală:", 
                 font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 10))

    optiuni = ["Tumoare", "Edem", "Necroză", "Leziune", "Artefact vizual"]
    combo = ctk.CTkComboBox(dialog, values=optiuni, width=280)
    combo.pack(pady=10)
    combo.set(optiuni[0])

    result = [None]
    def on_confirm():
        if combo.get().strip():
            result[0] = combo.get().strip()
            dialog.destroy()

    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=15)
    ctk.CTkButton(btn_frame, text="Confirmă", command=on_confirm, width=110, 
                  fg_color="#28a745", hover_color="#218838").pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text="Anulează", command=dialog.destroy, width=110, 
                  fg_color="gray", hover_color="#555555").pack(side="left", padx=10)

    parent.wait_window(dialog)
    return result[0]


def ask_custom_folder_name(parent, title: str, prompt: str, initial_value: str) -> Optional[str]:
    """Cere utilizatorului să introducă un text (nume fișier/folder)."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    w, h = 450, 220
    parent.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() // 2 - w // 2
    y = parent.winfo_rooty() + parent.winfo_height() // 2 - h // 2
    dialog.geometry(f"{w}x{h}+{x}+{y}")
    dialog.resizable(False, False)
    dialog.transient(parent)
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

    parent.wait_window(dialog)
    return result[0]