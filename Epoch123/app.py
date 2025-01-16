from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt
import sys
import logging
from pathlib import Path

from FileNavigator import FileNavigator
from eutils import get_main_sound_dir_path
from MetaData import MetaDataDB
from pydub import AudioSegment
from AudioManager import AudioPlayer
from SoundEditor import SoundEditor


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Epoch123 Audio Viewer")
        self.setMinimumSize(850, 650)

        # Initialize Metadata Database
        self.metaDataDB = MetaDataDB()

        # Define the directory to scan for audio
        self.audio_path = Path(get_main_sound_dir_path('Epoch123/ESMD'))  # Changed to Path
        self.scan_and_insert_metadata(self.audio_path)

        # Audio player instance
        self.audio_player = AudioPlayer()

        # Set up central stacked widget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Create File Navigator and Sound Editor
        self.file_navigator = FileNavigator(self)
        self.sound_editor = SoundEditor(self)

        self.stack.addWidget(self.file_navigator)
        self.stack.addWidget(self.sound_editor)

    def scan_and_insert_metadata(self, directory: Path):
        """
        Walk through 'directory' and insert metadata for audio files 
        into the database if they don't already exist.
        """
        audio_extensions = {'.wav', '.flac', '.mp3'}
        for file_path in directory.rglob('*'):
            if file_path.suffix.lower() in audio_extensions:
                full_path = str(file_path.resolve())
                if self.metaDataDB.file_already_exists(full_path):
                    continue
                try:
                    audio = AudioSegment.from_file(full_path)
                    metadata = {
                        'file_name': file_path.name,
                        'file_path': full_path,
                        'num_channels': audio.channels,
                        'sample_rate': audio.frame_rate,
                        'file_size_kb': round(file_path.stat().st_size / 1024, 2),
                        'duration_seconds': round(audio.duration_seconds, 2)
                    }
                    self.metaDataDB.insert_metadata(**metadata)
                    logging.info(f"Inserted metadata for {full_path}")
                except Exception as e:
                    logging.error(f"Failed to process {full_path}: {e}")

    def show_file_nav_widget(self):
        """Show the file navigator view."""
        self.stack.setCurrentWidget(self.file_navigator)

    def show_sound_editor(self):
        """Show the sound editor view."""
        self.stack.setCurrentWidget(self.sound_editor)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()