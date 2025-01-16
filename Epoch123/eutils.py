import os
from PySide6.QtWidgets import QMessageBox


def get_main_sound_dir_path(ext: str) -> str:
    """
    Returns the path to the main sound directory
    The Epoch123 Sounds Manager Directory (ESMD).
    """
    if ext is not None:
        main_sound_dir = os.path.join(os.getcwd(), ext)
    else:
        main_sound_dir = os.getcwd()
    return main_sound_dir


def show_error_message(self, message):
    """Show error message as a critical message box."""
    QMessageBox.critical(self, "Error", message)
