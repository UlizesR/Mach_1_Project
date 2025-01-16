import tkinter as tk
from tkinter import ttk, filedialog, StringVar
import os
import wave
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class FileNavigation:
    """
    Displays file navigation system on the GUI with option to upload a sound
    """
    def __init__(self, parent_frame):
        self.frame = ttk.Frame(parent_frame, padding="20")
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.file_label = ttk.Label(self.frame, text="Select File or Upload Sound:")
        self.file_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.upload_option = ttk.Button(self.frame, text="Upload Sound", command=self.upload_sound)
        self.upload_option.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # Search bar
        self.search_bar = ttk.Entry(self.frame, width=60)
        self.search_bar.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.search_entry = tk.StringVar()  # Corrected here
        self.search_bar = ttk.Entry(self.frame, textvariable= self.search_entry, width=60)
        self.search_bar.grid(row=2, column=0, padx=5, pady=5, sticky="w")


        # Search button
        search_button = ttk.Button(self.frame, text="Search", command=self.search) # Add search function/command
        search_button.grid(row=2, column=1, padx=5, pady=5)

        # File navigator box
        self.tree = ttk.Treeview(self.frame, columns=("fullpath", "type"), show="tree", height=20)
        self.tree.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.tree.bind("<<TreeviewOpen>>", self.populate_tree)

        # Scroll bar
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.grid(row=3, column=3, sticky="ns")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

    def populate_tree(self, event):
        item = self.tree.focus()
        if self.tree.item(item, "values")[1] == "drive":
            path = self.tree.item(item, "values")[0]
            self.tree.delete(self.tree.get_children(item))
            for directory in os.listdir(path):
                if os.path.isdir(os.path.join(path, directory)):
                    self.tree.insert(item, "end", text=directory, open=False, values=(os.path.join(path, directory), "folder"))
                else:
                    self.tree.insert(item, "end", text=directory, open=False, values=(os.path.join(path, directory), "file"))

    def upload_sound(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            return file_path  # Return the file path for further processing in the main application

    def search(self):
        """
        Add functionality to search bar
        """
        query = self.search_entry.get()

class EditingOptions:
    """
    Allows user to play and edit the sound in Editing Options tab
    """
    def __init__(self, parent_frame):
        self.frame = ttk.Frame(parent_frame, padding="20")
        self.frame.grid(row=0, column=1, sticky="nsew")

    def edit_sound(self):
        pass

class ViewMetadata:
    """
    Displays metadata of sound, audio visual, and option to add additional tags
    in Metadata tab
    """
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        
        # Create metadata frame (top left frame)
        self.metadata_frame = tk.Frame(self.parent_frame)
        self.metadata_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create audio visual frame (top right frame)
        self.tags_frame = tk.Frame(self.parent_frame)
        self.tags_frame.grid(row=0, column=1, sticky="nsew")
        
        # Create tags frame
        self.audio_visual_frame = tk.Frame(self.parent_frame, bg="green")
        self.audio_visual_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        
        # Configure row and column weights to allow resizing
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_rowconfigure(1, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(1, weight=1)

        # Populate metadata section
        metadata_labels = ["Encoding", "Format", "Number of Channels", "Sample Rate", "File Size", "Duration"]
        self.metadata_widgets = {}

        for i, label in enumerate(metadata_labels):
            ttk.Label(self.metadata_frame, text=label + ":").grid(row=i, column=0, sticky="w", padx=5, pady=5)
            self.metadata_widgets[label] = ttk.Label(self.metadata_frame, text="", anchor="w")
            self.metadata_widgets[label].grid(row=i, column=1, sticky="we", padx=5, pady=5)

        # Tag section
        self.tag_label = ttk.Label(self.tags_frame, text="Enter tags for the sound:")
        self.tag_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.tag_entry = ttk.Entry(self.tags_frame, width=25)
        self.tag_entry.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.save_button = ttk.Button(self.tags_frame, text="Save", command=self.save_tags)
        self.save_button.grid(row=2, column=0, padx=10, pady=5, sticky="w")

    def display_metadata(self, metadata):
        for key, value in metadata.items():
            if key in self.metadata_widgets:
                self.metadata_widgets[key].config(text=str(value))

    def save_tags(self): #FIXME#
        """
        Saves tags
        """
        tags = self.tag_entry.get()
        print("Tags saved:", tags)
        self.root.destroy()        


    
class AudioArchiveGUI:
    """
    Main driver for the different tabs
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Archive System")

        # Create a ttk Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # File Navigation Section
        self.file_nav = FileNavigation(self.notebook)
        self.notebook.add(self.file_nav.frame, text="File Navigation")

        # Editing Options Section
        self.edit_options = EditingOptions(self.notebook)
        self.notebook.add(self.edit_options.frame, text="Editing Options")

        # Metadata Viewing Section
        self.metadata_frame = tk.Frame(self.notebook)
        self.view_metadata = ViewMetadata(self.metadata_frame)
        self.metadata_frame.grid(row=0, column=0, sticky="nsew")
    
        #self.metadata_frame.pack(fill=tk.BOTH, expand=True)
        #self.view_metadata = ViewMetadata(self.metadata_frame)

        self.notebook.add(self.metadata_frame, text="Metadata")

        # Populate the tree with the specified folder
        folder_path = "/Users/uliraudales/Desktop/School/SoftwareDesign/Mach_1_Project/Epoch123/ESMD"
        self.populate_tree_with_folder(folder_path)

    def populate_tree_with_folder(self, folder_path):
        self.file_nav.tree.delete(*self.file_nav.tree.get_children())
        self.populate_tree_recursively("", folder_path)

    def populate_tree_recursively(self, parent, path):
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                folder_id = self.file_nav.tree.insert(parent, "end", text=item, open=False, values=(full_path, "folder"))
                self.populate_tree_recursively(folder_id, full_path)
            else:
                self.file_nav.tree.insert(parent, "end", text=item, open=False, values=(full_path, "file"))

def main():
    root = tk.Tk()
    app = AudioArchiveGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()