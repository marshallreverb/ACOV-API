import locale
import tempfile
import unittest
from pathlib import Path

from cmd_reader import read_autocad_command_output


class FakeDocument:
    def __init__(self, log_path: Path, log_mode: int = 0) -> None:
        self.log_path = log_path
        self.log_mode = log_mode
        self.output = "Commande\nRésultat\n"
        self.sent_command = None
        self.command_active = 0

    def GetVariable(self, name: str) -> int | str:
        if name == "LOGFILENAME":
            return str(self.log_path)
        if name == "LOGFILEMODE":
            return self.log_mode
        if name == "CMDACTIVE":
            return self.command_active
        raise AssertionError(f"Variable inattendue : {name}")

    def SetVariable(self, name: str, value: int) -> None:
        if name != "LOGFILEMODE":
            raise AssertionError(f"Variable inattendue : {name}")
        self.log_mode = value
        if value and not self.log_path.exists():
            self.log_path.write_bytes(b"")

    def SendCommand(self, command: str) -> None:
        self.sent_command = command
        with self.log_path.open("ab") as log_file:
            log_file.write(
                self.output.encode(locale.getpreferredencoding(False))
            )


class ReadAutoCADCommandOutputTests(unittest.TestCase):
    def test_captures_only_new_output_and_restores_logging_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "acad.log"
            log_path.write_text("Ancienne sortie\n", encoding="utf-8")
            document = FakeDocument(log_path)

            output = read_autocad_command_output(document, "_.-LAYER")

        self.assertEqual(output, document.output)
        self.assertEqual(document.sent_command, "_.-LAYER\n")
        self.assertEqual(document.log_mode, 0)

    def test_preserves_logging_that_was_already_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "acad.log"
            log_path.write_bytes(b"")
            document = FakeDocument(log_path, log_mode=1)

            read_autocad_command_output(document, "_.-LAYER")

        self.assertEqual(document.log_mode, 1)

    def test_rejects_empty_command_and_non_positive_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = FakeDocument(Path(directory) / "acad.log")

            with self.assertRaisesRegex(ValueError, "ne peut pas être vide"):
                read_autocad_command_output(document, "  ")
            with self.assertRaisesRegex(ValueError, "positif"):
                read_autocad_command_output(document, "_.-LAYER", timeout=0)

    def test_refuses_to_start_while_another_command_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = FakeDocument(Path(directory) / "acad.log")
            document.command_active = 1

            with self.assertRaisesRegex(RuntimeError, "déjà une commande"):
                read_autocad_command_output(document, "_.-LAYER")

        self.assertIsNone(document.sent_command)
        self.assertEqual(document.log_mode, 0)

    def test_restores_logging_mode_after_timeout(self) -> None:
        class SilentDocument(FakeDocument):
            def SendCommand(self, command: str) -> None:
                self.sent_command = command

        with tempfile.TemporaryDirectory() as directory:
            document = SilentDocument(Path(directory) / "acad.log")

            with self.assertRaises(TimeoutError):
                read_autocad_command_output(document, "_.-LAYER", timeout=0.01)

        self.assertEqual(document.log_mode, 0)


if __name__ == "__main__":
    unittest.main()
