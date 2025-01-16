# Mach 1 Team Project: Personal Sound Archive

This repository contains a semester-long CS370 project that implements a personal sound archive with a GUI interface. The application allows users to upload `.wav` files, organize and label them with metadata (e.g., tags, descriptions), visualize audio waveforms, and edit or remix sounds.

## Features

- **Upload & Organize Sounds**  
  Users can upload `.wav` files, organize them into folders, and manage their collection via a built-in file navigator.

- **Audio Playback & Visualization**  
  Leverages PySide and matplotlib (among other libraries) to display a waveform for each audio file. Basic playback controls let users play, pause, stop, and even play the audio in reverse.

- **Editing & Remixing**  
  Includes a `SoundEditor` that allows users to crop or zoom into selected regions of audio, facilitating basic sound-editing functionality.

- **Metadata Management**  
  Each audio file can store metadata such as duration, sample rate, file size, tags, and descriptions. A SQLite database (via `MetaDataDB`) is used to keep metadata in sync with the file system.

## Installation

1. **Clone the repository** (or download the ZIP).  
2. **Create and activate a virtual environment** (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate    # On macOS/Linux
   .venv\Scripts\activate       # On Windows
   ```
3. **Install required modules**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Launch the application**:
   ```bash
   python3 Epoch123/app.py
   ```

> **Important**: All sounds must end with a `.wav` extension to ensure compatibility with the project’s goals and initial requirements.

## Usage

- **File Navigator**:  
  Use the left pane to browse the file system for `.wav` files. Select a file to load its waveform and metadata.  
- **Audio Controls**:  
  Click the play (`▶`), pause (`⏸`), stop (`⏹`), or resume (`▶⏸`) buttons to control playback.  
- **Editing**:  
  Use the right-click context menu in the waveform to crop or zoom into a selected region.  
- **Metadata**:  
  View each file’s metadata (channels, duration, etc.) in the `MetaDataWidget`.  

## Project Timeline

### Epoch 1
- **Goals**:  
  - Implement the core functional requirements: uploading `.wav` sounds, basic playback, organizing files, and associating metadata.
- **Team Roles**:  
  - **Uli**: Driver for implementing functional requirements.  
  - **Molly**: Tested requirements and verified correctness.  
  - **Marlyn**: Added documentation and cleaned up code.  
  - **Clara**: Guided Uli on what needed to be implemented.
- **Progress Summary**:  
  - Completed initial functionality and tested all core commands.  
  - Encountered challenges getting sounds to play simultaneously; resolved by researching and testing.  
- **Reflection**:  
  - Next steps included refining code structure and possibly adding more commands.

### Epoch 2
- **Goals**:  
  - Enhance the ways users can listen to sounds (e.g., visualization, improved playback controls).  
  - Develop organization features (tags, categories).
- **Team Roles**:  
  - **Uli**: Implemented Part B (ways to characterize/organize sounds).  
  - **Molly**: Implemented Part A (enhanced ways to listen to sounds).  
  - **Marlyn**: Documentation, requirements, and use cases.  
  - **Clara**: Testing, use case documentation.
- **Reflection**:  
  - Biggest hurdle was `visualize_audio`. Struggled with displaying an audio “bar,” ultimately solved with research.  
  - Planned to transition to a GUI for Epoch 3 to enrich the user experience.

### Epoch 3
- **Goals**:  
  - Integrate a fully functional GUI (using PySide) for file navigation, waveform display, metadata editing, and more.  
  - Add advanced editing features.
- **Team Roles**:  
  - **Uli**: Implementation of advanced editing features in the GUI (Part 2).  
  - **Molly**: Implementation of basic GUI structure (Part 1).  
  - **Marlyn**: Requirements, use cases, and project documentation.  
  - **Clara**: File navigation, GUI testing, extended requirements documentation.
- **Reflection**:  
  - Switched from an initial Tkinter prototype to PySide, enabling robust waveform visualization.  
  - Continuing to refine audio tagging and descriptions.

## Testing

- **Command-Line Verification** (Epoch 1 & 2):  
  Tested each module with both correct and incorrect formats to confirm error messages appear and valid commands succeed.
- **GUI Testing** (Epoch 3):  
  - Verified that each button triggers the correct functionality (uploading files, playing audio, editing regions, etc.).  
  - Tested edge cases (e.g., missing metadata, empty directories).

## Future Improvements

- **Complete Tagging System**  
  Integrate audio tagging (genre, location, custom labels) in the main GUI to improve searching/filtering.
- **Advanced Editing Tools**  
  Beyond cropping and reversing, consider fade-in/out, volume normalization, or multi-track layering.
- **Performance Optimizations**  
  Speed up waveform rendering with downsampling, or consider a more GPU-friendly library (e.g., pyqtgraph).

## Contributing

We welcome feedback and suggestions for improvement. Feel free to open issues or submit pull requests.

## License

This project is part of a CS370 course and may have additional academic usage restrictions. For external use, please consult the course instructors or project maintainers.

---

**Mach 1 Team** – CS370  
Uli • Molly • Marlyn • Clara  