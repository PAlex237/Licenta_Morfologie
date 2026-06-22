"""
Structuri de date fundamentale.
"""
from dataclasses import dataclass

@dataclass
class Operatie:
    nume_clinic: str        # Etichetă prietenoasă pentru UI
    intensitate_text: str   # "Fină" / "Medie" / "Puternică"
    nume: str               # Operator OpenCV intern
    kernel: int             # Dimensiunea kernelului (impară)

    def to_dict(self) -> dict:
        return {
            "nume_clinic": self.nume_clinic,
            "intensitate_text": self.intensitate_text,
            "nume": self.nume,
            "kernel": self.kernel,
        }