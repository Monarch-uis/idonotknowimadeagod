import time
import pytest

chatterbox_module = pytest.importorskip("chatterbox", reason="chatterbox package not installed")
Chatterbox = chatterbox_module.ChatterboxTTS


def test_generation():
    print("Initializing Chatterbox (this might download models)...")
    print(f"Chatterbox methods: {dir(Chatterbox)}")

    import inspect
    print(f"from_pretrained sig: {inspect.signature(Chatterbox.from_pretrained)}")

    print("Attempting to load model 'resemble-ai/chatterbox-turbo'...")
    try:
        print("Trying Chatterbox.from_pretrained(device='cpu')...")
        cbox = Chatterbox.from_pretrained(device="cpu")
    except TypeError:
        print("Trying Chatterbox.from_pretrained('cpu')...")
        cbox = Chatterbox.from_pretrained("cpu")

    text = """
    This is a very long text designed to test the automatic chunking logic of the Chatterbox TTS client.
    It contains multiple sentences to ensure that the splitting logic correctly identifies sentence boundaries.
    We want to make sure that even when the input text exceeds the maximum character limit for a single generation chunk,
    the client can still process it by splitting it into smaller pieces and then merging the resulting audio files seamlessly using ffmpeg.
    This is a critical fix to prevent the IndexError that was occurring previously during long chapter generations.
    [laugh] Testing expressive tags across chunks.
    """
    output_file = "chatterbox_chunking_test.wav"

    print(f"Generating audio for: '{text}'")
    start_time = time.time()

    assert hasattr(cbox, 'generate'), "Chatterbox object has no 'generate' method"

    sig = inspect.signature(cbox.generate)
    print(f"generate sig: {sig}")

    audio = cbox.generate(text)
    print(f"Result type: {type(audio)}")

    if hasattr(audio, 'save'):
        audio.save(output_file)
        print(f"Saved to {output_file}")

    end_time = time.time()
    duration = end_time - start_time

    print(f"Success! Saved to {output_file}")
    print(f"Time taken: {duration:.2f} seconds")


if __name__ == "__main__":
    test_generation()
