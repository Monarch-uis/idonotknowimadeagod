# Sample Audio File

This directory should contain a sample audio file (sample_audio.mp3 or sample_audio.wav) 
that corresponds to the text in sample_text.txt.

To create a sample audio file, you can use any TTS tool such as:

1. **Edge TTS** (recommended):
   ```bash
   pip install edge-tts
   edge-tts --text "$(cat sample_text.txt)" --write-media sample_audio.mp3
   ```

2. **Piper TTS**:
   ```bash
   pip install piper-tts
   piper-tts --model <model_name> --text sample_text.txt --output sample_audio.wav
   ```

3. **pyttsx3**:
   ```bash
   pip install pyttsx3
   python -c "import pyttsx3; engine = pyttsx3.init(); engine.save_to_file(open('sample_text.txt').read(), 'sample_audio.mp3'); engine.runAndWait()"
   ```

The sample audio should be approximately 30 seconds long and match the content of sample_text.txt exactly.
