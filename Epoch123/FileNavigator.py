import os
import logging
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLineEdit, QLabel, QFileSystemModel,
    QTreeView, QHBoxLayout, QMenu, QMessageBox, QWidget, QFileDialog
)

from eutils import get_main_sound_dir_path, show_error_message
from PlotWidget import PlotWidget
from AudioManager import AudioProcessor, AudioControlWidget
from MetaData import MetaDataWidget
from GUIElements import Button
from pydub import AudioSegment


class CustomFileSystemModel(QFileSystemModel):
    """
    Customized file system model that ensures certain columns (e.g., column 1)
    remain non-editable in the tree view.
    """
    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            flags &= ~Qt.ItemIsEditable
        return flags


class CustomTreeView(QTreeView):
    """
    A QTreeView subclass with custom styling and improved editing behavior.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTreeView {
                background-color: #151515;
                color: white;
                font-size: 14px;
            }
            QTreeView::item {
                height: 25px;
                padding: 4px;
            }
            QTreeView::item:selected {
                background-color: #574B90;
            }
        """)

    def edit(self, index, trigger, event):
        """
        Override edit to style the QLineEdit editor (when renaming a file/folder).
        """
        if not index.isValid():
            return False
        editor = super().edit(index, trigger, event)
        if editor:
            line_edit = self.findChild(QLineEdit)
            if line_edit:
                line_edit.setStyleSheet(
                    "QLineEdit { border: 2px solid orange; padding: 4px; }"
                )
        return editor


class FileNavigator(QFrame):
    """
    FileNavigator is responsible for:
      • Browsing and displaying files (via QFileSystemModel + QTreeView)
      • Searching/filtering file names
      • Uploading new files to the target directory
      • Displaying metadata, waveform, and controls for the selected file
      • Editing (rename), deleting, and undoing deletes
    """

    MAX_WIDTH = 500
    MIN_WIDTH = 300
    SEARCH_STYLESHEET = (
        "background-color: #151515; color: white; padding: 2px; "
        "border: 1px solid #151515; border-radius: 5px; font-size: 14px"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setStyleSheet("background-color: #111111")
        self.setLayout(QHBoxLayout())

        # Database root path and related attributes
        self.root_path = get_main_sound_dir_path('Epoch123/ESMD')
        self.deleted_files = {}
        self.currently_selected_file = None

        # Cache for loaded audio data
        self.audio_cache = {}
        self.audio_workers = {}

        # File system model
        self.model = CustomFileSystemModel(self)
        self.model.setReadOnly(False)

        # Core UI elements (plot, controls, metadata)
        self.plot_widget = PlotWidget(audio_player=self.parent.audio_player)
        self.audio_controls_widget = AudioControlWidget(audio_player=self.parent.audio_player)
        self.metadata_widget = MetaDataWidget(self.parent)

        # Build the FileNavigator UI
        self.setup_ui()

    def setup_ui(self):
        """
        Create the overall layout:
          1. Search bar
          2. Upload button
          3. File tree
          4. Info widget (title, waveform, controls, metadata, edit/delete)
        """
        self.file_nav_layout = QVBoxLayout()
        self.layout().addLayout(self.file_nav_layout)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.setMinimumWidth(self.MIN_WIDTH)
        self.search_bar.setMaximumWidth(self.MAX_WIDTH)
        self.search_bar.setStyleSheet(self.SEARCH_STYLESHEET)
        self.search_bar.textChanged.connect(self.filter_files)
        self.file_nav_layout.addWidget(self.search_bar)

        # Upload button
        self.upload_button = Button("Upload File", self.upload_file)
        self.file_nav_layout.addWidget(self.upload_button)

        # File tree setup
        self.setup_file_tree()

        # Info widget (plot, metadata, edit buttons, etc.)
        self.info_widget = self.setup_info_widget()

    def setup_file_tree(self):
        """Configure the file tree view with the filesystem model and set hidden columns."""
        self.file_tree = CustomTreeView()
        self.file_tree.setMinimumWidth(self.MIN_WIDTH)
        self.file_tree.setMaximumWidth(self.MAX_WIDTH)
        self.file_tree.setModel(self.model)
        self.model.setRootPath(self.root_path)
        self.file_tree.setRootIndex(self.model.index(self.root_path))
        self.file_tree.setHeaderHidden(True)

        # Hide columns other than the name column
        for col in range(1, 4):
            self.file_tree.setColumnHidden(col, True)

        self.file_nav_layout.addWidget(self.file_tree)

    def setup_info_widget(self):
        """
        Create a QWidget that contains:
          • file title
          • waveform plot widget
          • audio control buttons
          • metadata display
          • edit/delete buttons
        """
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)

        # Selected file title
        self.file_title = QLabel("No file selected")
        self.file_title.setStyleSheet("color: white; font-size: 20px")
        self.file_title.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.file_title)

        # Plot, controls, metadata
        info_layout.addWidget(self.plot_widget)
        info_layout.addWidget(self.audio_controls_widget)
        info_layout.addWidget(self.metadata_widget)

        # Edit & delete buttons
        info_layout.addLayout(self.edit_buttons())

        # Hide them initially (until a valid file is selected)
        self.plot_widget.hide()
        self.audio_controls_widget.hide()
        self.metadata_widget.hide()

        # Connect file tree signals
        self.file_tree.clicked.connect(self.on_file_selected)
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_context_menu)

        # Add info_widget to the main layout
        self.layout().addWidget(info_widget)
        return info_widget

    def filter_files(self, keyword: str):
        """
        Simple approach: reset the model root to the main path, then expand
        any file that contains 'keyword' in its name.

        If keyword is empty, it simply resets and doesn't expand anything.
        """
        keyword = keyword.strip().lower()

        # 1) Clear and re-apply root path
        self.model.setRootPath("")
        self.model.setRootPath(self.root_path)
        self.file_tree.setRootIndex(self.model.index(self.root_path))

        # Hide columns again
        for col in range(1, 4):
            self.file_tree.setColumnHidden(col, True)

        if not keyword:
            return  # No search term => no filter

        # 2) Walk the directory and expand matches
        for root, _, files in os.walk(self.root_path):
            for f in files:
                if keyword in f.lower():
                    index = self.model.index(os.path.join(root, f))
                    if index.isValid():
                        self.file_tree.expand(index.parent())
                        self.file_tree.setCurrentIndex(index)

    def upload_file(self):
        """Allow user to select files from disk and copy them to the main directory."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_paths, _ = file_dialog.getOpenFileNames(self, "Select File(s) to Upload")

        if not file_paths:
            return

        for src_path in file_paths:
            # Copy the file to self.root_path
            dest_path = os.path.join(self.root_path, os.path.basename(src_path))
            shutil.copy(src_path, dest_path)
            file_name = os.path.basename(dest_path)

            # Insert metadata into DB
            try:
                audio = AudioSegment.from_file(dest_path)
                num_channels = audio.channels
                sample_rate = audio.frame_rate
                duration = round(audio.duration_seconds, 2)
                file_size = round(os.path.getsize(dest_path) / 1024, 2)

                self.parent.metaDataDB.insert_metadata(
                    file_name, dest_path, num_channels,
                    sample_rate, file_size, duration
                )
            except Exception as e:
                logging.error(f"Failed to upload {src_path}: {e}")

        # Refresh file tree to show new additions
        self.refresh_view()

    def refresh_view(self):
        """Re-set the root path to refresh the file tree view."""
        self.model.setRootPath(self.root_path)
        self.file_tree.setRootIndex(self.model.index(self.root_path))

    def edit_buttons(self) -> QHBoxLayout:
        """
        Create buttons to edit or delete the currently selected file.
        Returns a QHBoxLayout containing 'Edit File' and 'Delete File' buttons.
        """
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        edit_btn = Button("Edit File", self.go_to_sound_editor)
        delete_btn = Button("Delete File", lambda: self.delete_file(
            self.model.filePath(self.file_tree.currentIndex())
        ))

        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        return layout

    @lru_cache(maxsize=50)
    def load_audio(self, file_path: str):
        """
        Synchronous loading of audio data via AudioProcessor. 
        Caches results so repeated requests are fast.
        """
        processor = AudioProcessor(file_path)
        processor.data_loaded.connect(
            lambda data, fs, audio_segment: self.handle_data_loaded(data, fs, audio_segment, file_path)
        )
        processor.error_occurred.connect(show_error_message)
        processor.process_audio()

    def handle_data_loaded(self, data, fs, audio_segment, file_path):
        """
        Callback for AudioProcessor once data is loaded:
          • Cache the data
          • Set the player's audio
          • Update the waveform plot & metadata
        """
        if file_path not in self.audio_cache:
            self.audio_cache[file_path] = (data, fs, audio_segment)

        fs = int(fs)
        self.parent.audio_player.set_audio(audio_segment, data, fs, file_path)
        self.plot_widget.update_plot(data, fs, audio_segment)
        self.metadata_widget.update_metadata(file_path)

        # Show the plot & metadata (in case they were hidden)
        self.plot_widget.show()
        self.metadata_widget.show()

    def update_widgets(self, file_path, data, fs, audio_segment):
        """
        Helper to update the plot and metadata widgets with fresh data.
        """
        self.plot_widget.update_plot(data, fs, audio_segment)
        self.metadata_widget.update_metadata(file_path)
        self.plot_widget.show()
        self.metadata_widget.show()

    def on_file_selected(self, index):
        """
        Called when a file or folder is clicked in the tree:
          - If it's a folder, toggle expand/collapse
          - If it's a file, stop current playback, load & show the file data
        """
        file_path = self.model.filePath(index)
        path_obj = Path(file_path)

        # Expand/collapse if directory
        if path_obj.is_dir():
            if self.file_tree.isExpanded(index):
                self.file_tree.collapse(index)
            else:
                self.file_tree.expand(index)
            return

        # Stop any current playback
        self.audio_controls_widget.audio_player.stop_playback()
        self.currently_selected_file = path_obj.name

        # If not a valid file, hide relevant widgets
        if not path_obj.is_file():
            self.plot_widget.hide()
            self.audio_controls_widget.hide()
            self.metadata_widget.hide()
            return

        # Update UI
        self.file_title.setText(f"Selected File: {self.currently_selected_file}")
        self.plot_widget.show()
        self.audio_controls_widget.show()
        self.metadata_widget.show()

        # Load audio (or retrieve from cache)
        try:
            if file_path not in self.audio_cache:
                self.load_audio(file_path)
            else:
                data, fs, audio_segment = self.audio_cache[file_path]
                fs = int(fs)
                self.parent.audio_player.set_audio(audio_segment, data, fs, file_path)
                self.update_widgets(file_path, data, fs, audio_segment)
        except Exception as e:
            msg = f"Error loading file '{file_path}': {e}"
            show_error_message(self, msg)
            logging.error(msg)

    def show_context_menu(self, position):
        """
        Show a right-click context menu at 'position' in the file tree.
        Provides:
          - Rename
          - Delete
          - Create Folder
          - Undo Delete (if not valid index)
        """
        index = self.file_tree.indexAt(position)
        context_menu = QMenu(self)

        if index.isValid():
            context_menu.addAction(self.create_action('Rename', lambda: self.rename_file(index)))
            context_menu.addAction(self.create_action('Delete', lambda: self.delete_file(self.model.filePath(index))))
            context_menu.addAction(self.create_action('Create Folder', lambda: self.create_folder(index)))
        else:
            context_menu.addAction(self.create_action('Undo Delete', self.undo_delete))
            context_menu.addAction(self.create_action('Create Folder', self.create_folder))

        context_menu.exec_(self.file_tree.viewport().mapToGlobal(position))

    def create_action(self, name, func):
        """
        Helper to create a QAction with a given label and callback.
        """
        action = QAction(name, self)
        action.triggered.connect(func)
        return action

    def delete_file(self, file_path):
        """
        'Soft-delete' a file by moving it to a temp location,
        removing it from caches/DB, and allowing 'undo'.
        """
        if not Path(file_path).exists():
            return

        confirm = QMessageBox.question(
            self,
            'Delete file',
            'Are you sure you want to delete this file?',
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        temp_file_path = self.get_unique_temp_path(Path(file_path).name)
        path_obj = Path(file_path)

        try:
            if path_obj.is_file():
                shutil.move(file_path, temp_file_path)
                self.audio_cache.pop(file_path, None)
                self.audio_workers.pop(file_path, None)
                self.parent.metaDataDB.delete_file(file_path)
            elif path_obj.is_dir():
                # For directories, remove all files from cache/DB
                for root, _, files in os.walk(file_path):
                    for f in files:
                        abs_file_path = str(Path(root) / f)
                        self.audio_cache.pop(abs_file_path, None)
                        self.audio_workers.pop(abs_file_path, None)
                        self.parent.metaDataDB.delete_file(abs_file_path)
                shutil.move(file_path, temp_file_path)

            # Keep track for undo
            self.deleted_files[temp_file_path] = file_path
            self.refresh_view()

        except Exception as e:
            show_error_message(self, f"Error deleting file: {e}")
            logging.error(f"Error deleting file '{file_path}': {e}")

    def undo_delete(self):
        """
        Move the file back from the temp location to its original path.
        Removes it from 'deleted_files' dict once undone.
        """
        if self.deleted_files:
            temp_path, original_path = self.deleted_files.popitem()
            try:
                shutil.move(temp_path, original_path)
            except Exception as e:
                show_error_message(self, f"Error undoing delete: {e}")
                logging.error(f"Error undoing delete: {e}")

            self.refresh_view()

    def rename_file(self, index):
        """
        Start inline editing of the item at 'index' to rename a file/folder.
        """
        if index.isValid():
            self.file_tree.edit(index, QTreeView.EditKeyPressed, None)

    def create_folder(self, index=None):
        """
        Create a new folder named 'New Folder' under the selected directory
        or under the root path if no valid index is selected.
        """
        parent_path = Path(self.get_parent_path(index))
        folder_path = parent_path / "New Folder"

        try:
            folder_path.mkdir()
            self.refresh_view()

            # Automatically start rename on the new folder
            new_index = self.model.index(str(folder_path))
            self.file_tree.setCurrentIndex(new_index)
            self.file_tree.edit(new_index, QTreeView.EditKeyPressed, None)
        except FileExistsError:
            show_error_message(self, "Folder 'New Folder' already exists. Rename or remove it first.")

    def get_unique_temp_path(self, base_name: str) -> str:
        """
        Generate a unique path in the system temp directory for 'soft-deletions'.
        """
        temp_dir = Path(tempfile.gettempdir())
        temp_file_path = temp_dir / base_name
        counter = 1

        while temp_file_path.exists():
            temp_file_path = temp_dir / f"{base_name} ({counter})"
            counter += 1
        return str(temp_file_path)

    def get_parent_path(self, index) -> str:
        """
        Determine the parent directory for the given model index.
        Returns the file's parent if it's a file, or itself if a directory,
        or the root path if invalid.
        """
        if index and index.isValid():
            file_path = Path(self.model.filePath(index))
            return str(file_path.parent) if file_path.is_file() else str(file_path)
        return self.root_path

    def go_to_sound_editor(self):
        """
        Switch to the SoundEditor view if we have a valid file selected.
        Transfers the current file's audio data into the SoundEditor.
        """
        if self.currently_selected_file is None:
            QMessageBox.warning(self, "No file selected", "Please select a file to edit")
            return

        current_path = os.path.join(self.root_path, self.currently_selected_file)
        if current_path not in self.audio_cache:
            QMessageBox.critical(self, "Error", "No audio loaded for editing.")
            return

        try:
            data, fs, audio_segment = self.audio_cache[current_path]

            # Switch to the SoundEditor widget
            self.parent.show_sound_editor()
            self.plot_widget.clear_selection()
            self.parent.audio_player.stop_playback()

            fs = int(fs)
            # Update the SoundEditor plot
            self.parent.sound_editor.plot_widget.data = data
            self.parent.sound_editor.plot_widget.clear_selection()
            self.parent.sound_editor.plot_widget.update_plot(data, fs, audio_segment)
            self.parent.sound_editor.set_audio_data(data, current_path, fs, audio_segment)

        except RuntimeError as e:
            QMessageBox.critical(self, "Error", f"Error loading file for editing: {e}")
            logging.error(f"Error loading file for editing '{current_path}': {e}")
