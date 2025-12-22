# Gemini Project: EPUB to Audiobook/Video Converter

## Project Overview

This project is a Python-based command-line tool that automates the conversion of EPUB files into audiobooks and videos. It is designed to be highly customizable and resilient, with a rich set of features for generating high-quality content for platforms like YouTube.

The application is structured into a core logic layer, a features layer, and a main script that orchestrates the entire process. It uses a `config.json` file for detailed configuration of audio, video, and system settings.

**Main Technologies:**
- **Python 3:** The core language of the project.
- **MoviePy:** For video editing and composition.
- **faster-whisper:** For generating word-level transcriptions for subtitles.
- **edge-tts, pyttsx3, Piper:** For text-to-speech synthesis.
- **ffmpeg-python:** For advanced video rendering and effects.
- **ebooklib, BeautifulSoup4:** For parsing EPUB files.
- **Pillow:** For image manipulation.

**Architecture:**
The project follows a modular architecture:
- `epub_project_manager.py`: The main entry point and orchestrator of the conversion process.
- `core/`: Contains the core functionalities like EPUB parsing (`epub_io.py`), TTS synthesis (`tts.py`), video pipeline (`video_pipeline.py`), and configuration management (`config.py`).
- `features/`: Contains higher-level features like auto-recovery (`auto_recovery.py`), chapter merging (`chapter_merger.py`), and checkpoint management (`checkpoint_manager.py`).
- `config.json`: A comprehensive configuration file that allows for fine-tuning of the entire process.
- `requirements.txt`: Lists all the Python dependencies.

## Building and Running

**1. Installation:**
To install the required dependencies, run the following command:
```bash
pip install -r requirements.txt
```
You will also need to have FFmpeg installed and available in your system's PATH.

**2. Running the Application:**
The main script is `epub_project_manager.py`. You can run it with the following command:
```bash
python epub_project_manager.py
```
The application will then guide you through the process of selecting an EPUB file, configuring the conversion settings, and generating the final output.

**3. Command-line Arguments:**
The application also supports a variety of command-line arguments for non-interactive mode. You can see the available options by running:
```bash
python epub_project_manager.py --help
```

## Development Conventions

- **Modular and Extensible:** The code is organized into modules with clear responsibilities, making it easy to extend and maintain.
- **Configuration-driven:** Most of the application's behavior is controlled by the `config.json` file, allowing for easy customization without modifying the code.
- **Resilience:** The application includes features like auto-recovery and retry logic to handle errors gracefully.
- **Detailed Logging:** The application generates detailed logs to help with debugging and monitoring the conversion process.
- **Pre-flight Checks:** The application performs pre-flight checks to ensure that all the required dependencies are installed and that the configuration is valid before starting the conversion process.
- **Code Style:** The code follows the PEP 8 style guide.
I put much more focus in piper tts compare to other tts engine
