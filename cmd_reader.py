import locale
import time
from pathlib import Path


_POLL_INTERVAL = 0.1
_QUIET_PERIOD = 0.3


def read_autocad_command_output(
    document: object,
    command: str,
    timeout: float = 15.0,
) -> str:
    """Run an AutoCAD command and return the new text written to its command log."""
    if not command.strip():
        raise ValueError("La commande AutoCAD ne peut pas être vide.")
    if timeout <= 0:
        raise ValueError("Le délai d'attente doit être positif.")
    if int(document.GetVariable("CMDACTIVE")):
        raise RuntimeError(
            "AutoCAD exécute déjà une commande ; impossible de capturer "
            "une nouvelle commande de façon fiable."
        )

    log_path = Path(str(document.GetVariable("LOGFILENAME")))
    original_log_mode = int(document.GetVariable("LOGFILEMODE"))
    logging_enabled_here = False

    try:
        if not original_log_mode:
            document.SetVariable("LOGFILEMODE", 1)
            logging_enabled_here = True

        start_size = log_path.stat().st_size if log_path.is_file() else 0
        command_text = command if command.endswith("\n") else f"{command}\n"
        document.SendCommand(command_text)

        deadline = time.monotonic() + timeout
        last_size = start_size
        last_change = time.monotonic()
        command_started = False

        while time.monotonic() < deadline:
            command_active = int(document.GetVariable("CMDACTIVE"))
            current_size = log_path.stat().st_size if log_path.is_file() else 0
            now = time.monotonic()

            if command_active:
                command_started = True
            if current_size > last_size:
                command_started = True
                last_size = current_size
                last_change = now

            if (
                command_started
                and not command_active
                and now - last_change >= _QUIET_PERIOD
            ):
                break
            time.sleep(_POLL_INTERVAL)
        else:
            raise TimeoutError(
                "AutoCAD n'a pas terminé la commande ou écrit sa sortie "
                f"dans le délai de {timeout:g} s."
            )

        if logging_enabled_here:
            document.SetVariable("LOGFILEMODE", 0)
            logging_enabled_here = False

        contents = log_path.read_bytes()
        if len(contents) < start_size:
            raise RuntimeError("Le fichier journal AutoCAD a été tronqué pendant la lecture.")
        return contents[start_size:].decode(locale.getpreferredencoding(False))
    finally:
        if logging_enabled_here:
            document.SetVariable("LOGFILEMODE", original_log_mode)
