import numpy as np
import soundfile as sf
import pygame as pg
import os
import tempfile
import logging
from PySide6.QtWidgets import QWidget, QHBoxLayout, QMessageBox
from PySide6.QtCore import QObject, Signal, QThread, QTimer, Qt
from pydub import AudioSegment
from GUIElements import Button
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class AudioProcessor(QObject):
    """
    Loads and processes raw audio data for visualization and playback.
    Signals:
      - data_loaded(data: np.ndarray, samplerate: float, audio_segment: pydub.AudioSegment)
      - error_occurred(error_msg: str)
    """
    data_loaded = Signal(np.ndarray, float, object)
    error_occurred = Signal(str)

    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path

    def process_audio(self):
        """Process the audio file and emit results or errors."""
        try:
            data, samplerate = sf.read(self.audio_path, always_2d=True)
            audio_segment = AudioSegment.from_file(self.audio_path)

            if data.shape[1] > 1:
                data = np.mean(data, axis=1)

            self.data_loaded.emit(data, samplerate, audio_segment)
        except Exception as e:
            error_message = f"Error processing audio: {e}"
            self.error_occurred.emit(error_message)
            logger.error(error_message)


class AudioPlayer(QThread):
    """
    Handles audio playback using pygame mixer in a background thread-like structure.
    Signals:
      - error(str)
      - update_position(int)   -> Sends the current playback position in ms
      - playback_finished()    -> Emitted when playback stops
    """
    error = Signal(str)
    update_position = Signal(int)
    playback_finished = Signal()

    def __init__(self, audio_path=None, sample_rate=0, audio_data=None):
        super().__init__()
        self.audio_path = audio_path
        self.sample_rate = sample_rate
        self.audio_data = audio_data
        self.temp_file = None
        self.playing = False
        self.start_time = None
        self.start_frame = 0
        self.pause_time = 0
        self.initial_frame = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.emit_position)
        self.timer.setInterval(50)

        if not pg.mixer.get_init():
            pg.mixer.init()

    def set_initial_frame(self, frame):
        """Set the initial frame to start playback from."""
        self.initial_frame = frame

    def emit_position(self):
        """Emit the current position in ms, adjusted by the initial frame."""
        if pg.mixer.music.get_busy():
            position = pg.mixer.music.get_pos()
            self.update_position.emit(position + int(self.initial_frame * (1000 / self.sample_rate)))
        else:
            if self.playing:
                self.playback_finished.emit()
                self.stop_playback()

    def set_audio(self, audio_segment, audio_data, sample_rate, audio_path):
        """Set the audio for playback."""
        self.audio = audio_segment
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.audio_path = audio_path

    def set_audio_data(self, audio_data, sample_rate=0):
        """Directly set audio data (usually used for a selected region)."""
        self.audio_data = audio_data
        if sample_rate:
            self.sample_rate = sample_rate

    def start_playback(self):
        """
        Begin playback. If audio_data is set, writes the data to a temp file 
        and uses pygame to play. Use 'stop_playback()' to end playback.
        """
        if self.audio_data is None:
            logger.error("No audio data to play.")
            self.error.emit("No audio data to play.")
            return

        self.playing = True
        try:
            self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            sf.write(self.temp_file.name, self.audio_data, self.sample_rate)
            pg.mixer.music.load(self.temp_file.name)
            pg.mixer.music.play()
            self.start_time = time.time()
            self.timer.start()
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"Error playing audio: {e}")

    def stop_playback(self):
        """Stop playback and cleanup."""
        if pg.mixer.get_init():
            pg.mixer.music.stop()
        self.timer.stop()
        self.playing = False
        self.playback_finished.emit()
        self.cleanup()

    def pause(self):
        """Pause the current playback."""
        try:
            if pg.mixer.get_init() and self.playing:
                pg.mixer.music.pause()
                self.pause_time = pg.mixer.music.get_pos()
                self.timer.stop()
                self.playing = False
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"Error pausing audio: {e}")

    def resume(self):
        """Resume playback from a paused state."""
        try:
            if pg.mixer.get_init() and not self.playing:
                pg.mixer.music.unpause()
                self.start_time = time.time() - self.pause_time / 1000.0
                self.timer.start()
                self.playing = True
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"Error resuming audio: {e}")

    def set_volume(self, volume):
        """Set the mixer volume (0-100)."""
        try:
            pg.mixer.music.set_volume(volume / 100.0)
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"Error setting volume: {e}")

    def play_reverse(self):
        """
        Play the current audio in reverse by exporting reversed AudioSegment 
        to a temporary mp3 and playing that via pygame.
        """
        try:
            if not hasattr(self, 'audio'):
                raise ValueError("No AudioSegment loaded to reverse.")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as temp:
                reversed_segment = self.audio.reverse()
                reversed_segment.export(temp.name, format="mp3")
                pg.mixer.music.load(temp.name)
                pg.mixer.music.play()
            self.playing = True
            self.start_time = time.time()
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error playing audio in reverse: {e}")
            logger.error(f"Error playing audio in reverse: {e}")
            raise

    def cleanup(self):
        """Remove any temporary files used for playback."""
        if self.temp_file:
            temp_path = self.temp_file.name
            self.temp_file.close()
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            self.temp_file = None


class AudioControlWidget(QWidget):
    """
    A simple row of playback control buttons that call methods in the given audio_player.
    """
    def __init__(self, audio_player, parent=None):
        super().__init__(parent)
        self.audio_player = audio_player
        self.buttons_layout = QHBoxLayout()
        self.setLayout(self.buttons_layout)
        self.init_ui()

    def init_ui(self):
        """
        Create and add the playback buttons to the layout.
        """
        actions = {
            "▶": self.audio_player.start_playback,
            "⏹": self.audio_player.stop_playback,
            "⏸": self.audio_player.pause,
            "▶⏸": self.audio_player.resume
        }
        for label, func in actions.items():
            button = self.create_button(label, func)
            self.buttons_layout.addWidget(button)

    def create_button(self, label, func):
        """
        Helper that creates a styled Button with label `label` 
        and clicks calling function `func`.
        """
        return Button(label, callback=func, setFixedWidth=75)