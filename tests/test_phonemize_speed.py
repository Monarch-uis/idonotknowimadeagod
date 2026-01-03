
from phonemizer import phonemize
import time

words = ["Hello", "world", "this", "is", "a", "test", "of", "batch", "processing"] * 10
print(f"Processing {len(words)} words...")

start = time.time()
# Test list input
try:
    res = phonemize(words, language='en-us', backend='espeak', strip=True, with_stress=False, njobs=4)
    print(f"Batch List Output type: {type(res)}")
    print(f"Batch List Output length: {len(res)}")
    print(f"First 5: {res[:5]}")
    print(f"Time taken (batch): {time.time() - start:.4f}s")
except Exception as e:
    print(f"Batch failed: {e}")

start = time.time()
# Test loop
res2 = []
for w in words[:10]:
    res2.append(phonemize(w, language='en-us', backend='espeak', strip=True, with_stress=False))
print(f"Time taken (loop 10 items): {time.time() - start:.4f}s")
