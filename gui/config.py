"""
Constante și configurări pentru interfața grafică.
"""

# Hărți clinice → tehnice
HARTA_OPERATORI = {
    "Fără Filtru":                   "Niciunul",
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
    "Extremă":   15,
}