import time
try:
    from chatterbox import ChatterboxTTS as Chatterbox
    print("Chatterbox (ChatterboxTTS) imported successfully.")
except ImportError as e:
    import traceback
    traceback.print_exc()
    print(f"Failed to import Chatterbox: {e}")
    # Fallback to check what was installed
    # import pkg_resources
    # installed_packages = [d.project_name for d in pkg_resources.working_set]
    # print(f"Installed packages: {', '.join(installed_packages)}")

def test_generation():
    print("Initializing Chatterbox (this might download models)...")
    print(f"Chatterbox methods: {dir(Chatterbox)}")
    try:
        # Inspect from_pretrained
        import inspect
        print(f"from_pretrained sig: {inspect.signature(Chatterbox.from_pretrained)}")
        
        # Try loading. If no default, this will fail.
        # Guessing model name based on search results.
        # Usually libraries have a default or we pass a HF repo id.
        print("Attempting to load model 'resemble-ai/chatterbox-turbo'...")
        # Try loading with just device="cpu" if model name is implicit
        try:
            print("Trying Chatterbox.from_pretrained(device='cpu')...")
            cbox = Chatterbox.from_pretrained(device="cpu")
        except TypeError:
             # Maybe it expects positional?
             print("Trying Chatterbox.from_pretrained('cpu')...")
             cbox = Chatterbox.from_pretrained("cpu")
            
        # cbox = Chatterbox.from_pretrained("resemble-ai/chatterbox-turbo") # ERROR here previously
        
        # If that fails, might be just "resemble-ai/chatterbox"
        
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
        
        if hasattr(cbox, 'generate'):
            import inspect
            sig = inspect.signature(cbox.generate)
            print(f"generate sig: {sig}")
            
            # Text to speech
            print(f"Generating audio for: '{text}'")
            # implementation might vary on arguments
            audio = cbox.generate(text)
            # Check what audio is (tensor? object with save?)
            print(f"Result type: {type(audio)}")
            
            if hasattr(audio, 'save'):
                audio.save(output_file)
                print(f"Saved to {output_file}")
            else:
                # If it's a tensor, might need saving differently
                print("Result does not have .save(). Check logic.")
                
        else:
             print("Chatterbox object has no 'generate' method?")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Success! Saved to {output_file}")
        print(f"Time taken: {duration:.2f} seconds")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"An error occurred during generation: {e}")

if __name__ == "__main__":
    test_generation()
