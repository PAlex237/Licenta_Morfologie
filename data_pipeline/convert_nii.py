"""
 Convertor NIfTI → PNG
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backend_morph import MorphoBackend

def main():
    parser = argparse.ArgumentParser(
        description="Convertește un volum NIfTI 3D în felii PNG 2D.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemple de utilizare:
  python data_pipeline/convert_nii.py fisier.nii
  python data_pipeline/convert_nii.py fisier.nii.gz --output datasets/converted_2d/pacient_01
        """
    )
    parser.add_argument("input", help="Calea către fișierul .nii sau .nii.gz")
    parser.add_argument(
        "--output", "-o",
        help="Directorul de ieșire (implicit: datasets/converted_2d/<nume_fisier>)",
        default=None
    )
    args = parser.parse_args()

    nii_path = os.path.abspath(args.input)
    if not os.path.exists(nii_path):
        print(f"[EROARE] Fișierul nu există: {nii_path}")
        sys.exit(1)

    if args.output:
        output_folder = os.path.abspath(args.output)
    else:
        base_name = os.path.basename(nii_path).split(".")[0]
        output_folder = os.path.abspath(
            os.path.join("datasets", "converted_2d", base_name))

    print(f"Intrare:  {nii_path}")
    print(f"Ieșire:   {output_folder}")
    print("Procesare în curs...")

    backend = MorphoBackend()
    ok, info = backend.convert_nii_volume(nii_path, output_folder)

    if ok:
        print(f"[OK] S-au generat {info} felii în: {output_folder}")
    else:
        print(f"[EROARE] Conversia a eșuat: {info}")
        sys.exit(1)

if __name__ == "__main__":
    main()