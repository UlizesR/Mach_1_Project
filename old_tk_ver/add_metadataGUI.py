import tkinter as tk
from tkinter import ttk

class TagCreationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tag Creation")

        self.tag_label = ttk.Label(root, text="Enter tags for the sound:")
        self.tag_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.tag_entry = ttk.Entry(root, width=40)
        self.tag_entry.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.save_button = ttk.Button(root, text="Save", command=self.save_tags)
        self.save_button.grid(row=2, column=0, padx=10, pady=5, sticky="w")

    def save_tags(self):
        tags = self.tag_entry.get()
        # You can add code here to save the tags
        print("Tags saved:", tags)
        self.root.destroy()
