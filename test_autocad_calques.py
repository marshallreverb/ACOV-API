from pathlib import Path

import pythoncom
import win32com.client

from cmd_reader import read_autocad_command_output


def main() -> None:
    drawing_path = Path(__file__).resolve().parent / "LEVE_CORRIGE_.dwg"
    if not drawing_path.is_file():
        raise FileNotFoundError(f"DWG introuvable : {drawing_path}")

    pythoncom.CoInitialize()
    try:
        autocad = win32com.client.Dispatch("AutoCAD.Application")
        document = autocad.Documents.Open(str(drawing_path))

        output = read_autocad_command_output(
            document,
            "_.-LAYER\n?\n*\n",
            timeout=30.0,
        )
        print(output, end="")
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
