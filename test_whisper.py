from faster_whisper import WhisperModel

print("Loading model...")
model = WhisperModel("small", device="cpu", compute_type="int8")

print("Transcribing clip_fixed.mp4...")
segments, info = model.transcribe("clip_fixed.mp4", word_timestamps=True)
words = []
for s in segments:
    print(f"Segment: {s.text}")
    for w in s.words:
        words.append(w)

print(f"Total words in clip_fixed.mp4: {len(words)}")

print("Transcribing narration.wav...")
segments2, info2 = model.transcribe("narration.wav", word_timestamps=True)
words2 = []
for s in segments2:
    print(f"Segment: {s.text}")
    for w in s.words:
        words2.append(w)

print(f"Total words in narration.wav: {len(words2)}")
