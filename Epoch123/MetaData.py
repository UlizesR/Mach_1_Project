import sqlite3
import os
import logging
from contextlib import contextmanager
from PySide6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QHeaderView
from PySide6.QtCore import Qt
from eutils import get_main_sound_dir_path

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s')


class MetaDataDB:
    """
    Manages audio file metadata in a SQLite database. 
    Provides CRUD operations on metadata and tags.
    """
    def __init__(self):
        self.db_path = os.path.join(get_main_sound_dir_path('Epoch123/DB'), 'metadata.db')
        self.initialize_db()

    def initialize_db(self):
        """
        Create necessary tables if they don't already exist.
        """
        try:
            with self.db_connection() as conn:
                cursor = conn.cursor()
                # Create audio_files table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audio_files (
                        file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_name TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        num_channels INTEGER,
                        sample_rate INTEGER,
                        file_size INTEGER,
                        duration REAL,
                        description TEXT
                    )
                ''')
                # Create tags table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tags (
                        tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tag_name TEXT UNIQUE
                    )
                ''')
                # Create file_tags table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file_tags (
                        file_id INTEGER,
                        tag_id INTEGER,
                        PRIMARY KEY (file_id, tag_id),
                        FOREIGN KEY (file_id) REFERENCES audio_files (file_id),
                        FOREIGN KEY (tag_id) REFERENCES tags (tag_id)
                    )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Initialization Error", f"Database initialization error: {e}")
            logging.error(f"Database initialization error: {e}")

    @contextmanager
    def db_connection(self):
        """ Context manager that ensures the database connection is closed. """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query, params=(), commit=False):
        """
        Execute a query in a managed context. 
        If commit is True, commits the transaction.
        Returns the fetched rows.
        """
        with self.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if commit:
                conn.commit()
            return cursor.fetchall()

    def file_already_exists(self, file_path):
        """
        Check if the file already exists in the database.
        """
        query = "SELECT 1 FROM audio_files WHERE file_path = ?"
        result = self.execute_query(query, (file_path,))
        return len(result) > 0

    def insert_metadata(self, file_name, file_path, num_channels, sample_rate, file_size, duration):
        """
        Insert metadata into the database, skipping if the file already exists.
        """
        if not self.file_already_exists(file_path):
            query = '''
                INSERT INTO audio_files
                (file_name, file_path, num_channels, sample_rate, file_size, duration)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            try:
                self.execute_query(
                    query,
                    (file_name, file_path, num_channels, sample_rate, file_size, duration),
                    commit=True
                )
            except sqlite3.Error as e:
                QMessageBox.critical(None, "Failed to Insert Metadata", f"Failed to insert metadata for {file_name}: {e}")
                logging.error(f"Failed to insert metadata for {file_name}: {e}")

    def write_metadata(self, file_path, num_channels=None, sample_rate=None,
                       file_size=None, duration=None, description=None, tags=None):
        """
        Insert or update metadata for a given file, including tags.
        """
        if self.file_already_exists(file_path):
            # Update existing record
            query = '''
                UPDATE audio_files
                SET file_name = ?,
                    num_channels = ?,
                    sample_rate = ?,
                    file_size = ?,
                    duration = ?,
                    description = ?
                WHERE file_path = ?
            '''
            try:
                self.execute_query(
                    query,
                    (
                        os.path.basename(file_path), num_channels, sample_rate,
                        file_size, duration, description, file_path
                    ),
                    commit=True
                )
                file_id = self.get_file_id(file_path)
                if tags:
                    for tag in tags:
                        self.add_tag(tag)
                        self.add_tag_to_file(file_path, tag)
            except sqlite3.Error as e:
                QMessageBox.critical(None, "Error Writing Metadata", f"Error updating metadata: {e}")
                logging.error(f"Error updating metadata: {e}")
        else:
            # Insert new record
            query = '''
                INSERT INTO audio_files
                (file_name, file_path, num_channels, sample_rate, file_size, duration, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            try:
                self.execute_query(
                    query,
                    (
                        os.path.basename(file_path), file_path, num_channels,
                        sample_rate, file_size, duration, description
                    ),
                    commit=True
                )
                file_id = self.get_file_id(file_path)
                if tags:
                    for tag in tags:
                        self.add_tag(tag)
                        self.add_tag_to_file(file_path, tag)
            except sqlite3.Error as e:
                QMessageBox.critical(None, "Error Writing Metadata", f"Error writing metadata: {e}")
                logging.error(f"Error writing metadata: {e}")

    def get_file_id(self, file_path):
        """Retrieve file_id from the audio_files table for a given file_path."""
        query = "SELECT file_id FROM audio_files WHERE file_path = ?"
        result = self.execute_query(query, (file_path,))
        return result[0][0] if result else None

    def rename_file(self, old_path, new_path):
        """
        Update the database to reflect a rename from old_path to new_path.
        """
        query = """
            UPDATE audio_files
            SET file_path = ?, file_name = ?
            WHERE file_path = ?
        """
        self.execute_query(
            query,
            (new_path, os.path.basename(new_path), old_path),
            commit=True
        )

    def delete_file(self, file_path):
        """Remove file metadata from the database by file_path."""
        query = "DELETE FROM audio_files WHERE file_path = ?"
        self.execute_query(query, (file_path,), commit=True)

    def get_metadata(self, file_path):
        """Return the entire row of metadata for the file_path."""
        query = "SELECT * FROM audio_files WHERE file_path = ?"
        result = self.execute_query(query, (file_path,))
        return result[0] if result else None

    def add_tag(self, tag_name):
        """Add a tag if it does not already exist."""
        query = "INSERT OR IGNORE INTO tags (tag_name) VALUES (?)"
        self.execute_query(query, (tag_name,), commit=True)

    def get_tags(self):
        """Return a list of all tag names."""
        query = "SELECT tag_name FROM tags"
        result = self.execute_query(query)
        return [r[0] for r in result]

    def get_files_by_tag(self, tag_name):
        """Return a list of file_path's for a given tag."""
        query = """
            SELECT file_path FROM audio_files
            WHERE file_id IN (
                SELECT file_id FROM file_tags
                WHERE tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?)
            )
        """
        result = self.execute_query(query, (tag_name,))
        return [r[0] for r in result]

    def remove_tag(self, tag_name):
        """Remove a tag and any associations with it."""
        query = "DELETE FROM tags WHERE tag_name = ?"
        self.execute_query(query, (tag_name,), commit=True)

    def remove_tag_from_file(self, file_path, tag_name):
        """
        Remove an association between a file and a tag.
        """
        query = """
            DELETE FROM file_tags
            WHERE file_id = (SELECT file_id FROM audio_files WHERE file_path = ?)
            AND tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?)
        """
        self.execute_query(query, (file_path, tag_name), commit=True)

    def add_tag_to_file(self, file_path, tag_name):
        """
        Associate an existing tag with a file.
        """
        query = """
            INSERT OR IGNORE INTO file_tags (file_id, tag_id)
            VALUES (
                (SELECT file_id FROM audio_files WHERE file_path = ?),
                (SELECT tag_id FROM tags WHERE tag_name = ?)
            )
        """
        self.execute_query(query, (file_path, tag_name), commit=True)

    def get_tags_for_file(self, file_path):
        """
        Return all tags for a given file.
        """
        query = """
            SELECT tag_name FROM tags
            WHERE tag_id IN (
                SELECT tag_id FROM file_tags
                WHERE file_id = (SELECT file_id FROM audio_files WHERE file_path = ?)
            )
        """
        result = self.execute_query(query, (file_path,))
        return [r[0] for r in result]

    def get_all_files(self):
        """Return all file_paths in audio_files."""
        query = "SELECT file_path FROM audio_files"
        result = self.execute_query(query)
        return [r[0] for r in result] if result else []


class MetaDataWidget(QTableWidget):
    """
    A QTableWidget that displays a file's metadata in 4 rows x 4 columns,
    effectively 8 key-value pairs.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.metadatadb = parent.metaDataDB
        self.layout = QVBoxLayout(self)
        self.setup_table()
        self.setLayout(self.layout)

    def setup_table(self):
        """Set up the table's initial appearance and constraints."""
        self.setRowCount(4)
        self.setColumnCount(4)
        self.setShowGrid(True)
        self.setStyleSheet("""
            QTableView {
                gridline-color: #ffffff;
                background-color: #151515;
                border: 1px solid #ffffff;
            }
        """)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setStretchLastSection(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setMinimumHeight(200)
        self.setMinimumWidth(300)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def update_metadata(self, file_path):
        """Fetch metadata from DB and populate the table."""
        try:
            metadata = self.metadatadb.get_metadata(file_path)
            if metadata:
                file_id, file_name, file_path_, num_channels, sample_rate, file_size, duration, description = metadata
                tags = ', '.join(self.metadatadb.get_tags_for_file(file_path_))

                data = [
                    ("File Name", file_name),
                    ("File Path", file_path_),
                    ("Num of Channels", str(num_channels)),
                    ("Sample Rate", f"{sample_rate} Hz"),
                    ("File Size", f"{file_size} KB"),
                    ("Duration", f"{duration} seconds"),
                    ("Description", str(description) if description else ""),
                    ("Tags", tags)
                ]

                # Fill the 4x4
                for i in range(4):
                    for j in range(2):
                        key = data[i*2 + j][0]
                        val = data[i*2 + j][1]
                        self.setItem(i, j*2, QTableWidgetItem(key))
                        self.setItem(i, j*2 + 1, QTableWidgetItem(val))
                        self.item(i, j*2 + 1).setTextAlignment(Qt.AlignCenter)
            else:
                QMessageBox.warning(None, "No Metadata Found", "No metadata found for this file path.")
                logging.warning("No metadata found for this file path.")
        except Exception as e:
            QMessageBox.critical(None, "Error Fetching Metadata", f"An error occurred while fetching metadata: {e}")
            logging.error(f"An error occurred while fetching metadata: {e}")
