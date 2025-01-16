from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt
import numpy as np
import scipy.signal as sig
from numpy.fft import fft, ifft
import soundfile as sf

from GUIElements import Button, LineEdit, GuiWidget, CustomComboBox, Slider
from PlotWidget import PlotWidget
from AudioManager import AudioControlWidget

class SoundEditor(QFrame):
    """
    Provides a simple "editor" for an audio file with options like filters, pitch shift, trimming, etc.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.audio_player = parent.audio_player
        self.audio_data = None
        self.audio_file = None
        self.sample_rate = None
        self.audio = None  # pydub AudioSegment

        self.setStyleSheet("background-color: #111111; color: white;")
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Plot and nav buttons
        self.plot_widget = PlotWidget(audio_player=self.audio_player, parent=self)
        self.set_nav_buttons(layout)
        layout.addWidget(self.plot_widget)

        # Editor options
        self.editor_layout = QVBoxLayout()
        layout.addLayout(self.editor_layout)
        self.set_editor()

    def set_audio_data(self, audio_data, audio_file, sample_rate, audio):
        """Set the audio data, file, rate, and pydub segment for editing."""
        self.audio_data = audio_data
        self.audio_file = audio_file
        self.sample_rate = sample_rate
        self.audio = audio

    def set_nav_buttons(self, layout):
        """Create top navigation row with 'back', 'save', and audio controls."""
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(Button("\u2190", self.parent.show_file_nav_widget, setFixedWidth=75))
        nav_layout.addWidget(Button("Save", self.save_audio, setFixedWidth=75))
        nav_layout.addWidget(AudioControlWidget(self.audio_player))
        nav_layout.addWidget(Button("\u23EA", self.audio_player.play_reverse, setFixedWidth=75))
        layout.addLayout(nav_layout)

    def set_editor(self):
        """Create interactive elements for filters, pitch shift, trim, volume."""
        self.create_dropdown("Filter", ["Low Pass", "High Pass", "Band Pass"], self.apply_filter)
        self.create_input("Pitch Shift (Semitones):", "0", self.change_pitch, 200)
        self.create_input("Trim Level (dB):", "0.0", self.trim_audio, 200)
        self.create_slider("Volume", 0, 100, 1, self.audio_player.set_volume, 200)

    def create_dropdown(self, label, items, callback):
        dropdown = CustomComboBox(items)
        dropdown.set_on_change(callback)
        layout = GuiWidget(label_text=f"{label}:", gui_elements=[dropdown])
        self.editor_layout.addWidget(layout)

    def create_input(self, label, placeholder, action, width):
        input_field = LineEdit(placeholder=placeholder, setFixedWidth=50)
        input_field.returnPressed.connect(lambda: action(float(input_field.text())))
        widget = GuiWidget(label_text=label, gui_elements=[input_field], setFixedWidth=width)
        self.editor_layout.addWidget(widget)

    def create_slider(self, label, min_val, max_val, step, callback, width):
        slider = Slider(Qt.Horizontal, min_val, max_val, step, setFixedWidth=width)
        slider.valueChanged.connect(callback)
        layout = GuiWidget(label_text=f"{label}:", gui_elements=[slider], setFixedWidth=width)
        self.editor_layout.addWidget(layout)

    def apply_filter(self, index):
        """Apply a simple Butterworth filter to the current audio data."""
        filter_options = ["Low Pass", "High Pass", "Band Pass"]
        if not self.audio_data is not None or len(self.audio_data) == 0:
            QMessageBox.critical(self, "Error", "Audio data is empty.")
            return
        if 0 <= index < len(filter_options):
            selected_filter = filter_options[index]
            try:
                if self.audio_data.ndim > 1:
                    self.audio_data = np.mean(self.audio_data, axis=1)

                # Map filter name to Butterworth design
                filter_map = {
                    "Low Pass": sig.butter(4, 0.1),
                    "High Pass": sig.butter(4, 0.1, btype='high'),
                    "Band Pass": sig.butter(4, [0.05, 0.15], btype='band')
                }
                if selected_filter not in filter_map:
                    QMessageBox.critical(self, "Filter Error", "Unknown filter type.")
                    return
                b, a = filter_map[selected_filter]

                # Push current state to undo stack
                self.plot_widget.undo_stack.append((np.copy(self.audio_data), self.plot_widget.ax.get_xlim()))

                self.audio_data = sig.filtfilt(b, a, self.audio_data)
                self.audio_player.set_audio_data(self.audio_data, self.sample_rate)
                self.plot_widget.update_plot(self.audio_data, self.sample_rate, self.audio)
                QMessageBox.information(self, "Filter Applied", f"{selected_filter} filter applied successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Filter Application Error", f"Failed to apply {selected_filter} filter: {str(e)}")
        else:
            QMessageBox.critical(self, "Filter Error", "Index out of range.")

    def change_pitch(self, semitones):
        """Change pitch by shifting FFT bins."""
        if not self.audio_data is not None or len(self.audio_data) == 0:
            QMessageBox.critical(self, "Error", "No audio data to process.")
            return
        try:
            factor = 2 ** (semitones / 12)
            self.plot_widget.undo_stack.append((np.copy(self.audio_data), self.plot_widget.ax.get_xlim()))
            self.audio_data = self.fft_pitch_shift(self.audio_data, factor)

            self.audio_player.set_audio_data(self.audio_data, self.sample_rate)
            self.plot_widget.update_plot(self.audio_data, self.sample_rate, self.audio)
            QMessageBox.information(self, "Pitch Shift", "Pitch changed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to change pitch: {str(e)}")

    def fft_pitch_shift(self, data, factor):
        """Shift pitch by factoring index in FFT domain."""
        fft_spectrum = fft(data)
        new_fft_spectrum = np.zeros_like(fft_spectrum)
        N = len(fft_spectrum)
        new_indices = (np.arange(N) * factor).astype(int)
        valid = (new_indices < N)
        new_fft_spectrum[new_indices[valid]] = fft_spectrum[valid]
        return ifft(new_fft_spectrum).real

    def trim_audio(self, decibel_level):
        """
        Zero out samples below a threshold derived from decibel_level 
        relative to the maximum amplitude.
        """
        if not self.audio_data is not None or len(self.audio_data) == 0:
            QMessageBox.critical(self, "Error", "No audio data to process.")
            return
        ref_level = np.max(np.abs(self.audio_data))
        if ref_level == 0:
            return

        threshold = ref_level * (10 ** (decibel_level / 20.0))
        self.plot_widget.undo_stack.append((np.copy(self.audio_data), self.plot_widget.ax.get_xlim()))
        self.audio_data = np.where(np.abs(self.audio_data) < threshold, 0, self.audio_data)

        self.audio_player.set_audio_data(self.audio_data, self.sample_rate)
        self.plot_widget.update_plot(self.audio_data, self.sample_rate, self.audio)
        QMessageBox.information(self, "Trim Audio", f"Audio trimmed at {decibel_level} dB successfully!")

    def save_audio(self):
        """
        Save the modified audio data back to the file with the same sample rate.
        """
        if not self.audio_file:
            QMessageBox.critical(self, "Error", "No audio file specified.")
            return
        try:
            sf.write(self.audio_file, self.audio_data, self.sample_rate)
            QMessageBox.information(self, "Save Audio", "Audio saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save audio: {str(e)}")