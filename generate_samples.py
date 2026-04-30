import os
import torch
import soundfile as sf
import kokoro
import numpy as np

VOICES = ["am_onyx", "am_echo", "am_michael", "af_bella", "af_sarah", "af_sky"]
SAMPLE_TEXT = "This is a sample of my voice. I will be your cinematic narrator."

os.makedirs("assets/samples", exist_ok=True)
pipeline = kokoro.KPipeline(lang_code='a')

for voice in VOICES:
    print(f"Generating sample for {voice}...")
    samples = []
    for result in pipeline(SAMPLE_TEXT, voice=voice, speed=1.0):
        if result.audio is not None:
            samples.append(result.audio.numpy())
    if samples:
        audio = np.concatenate(samples)
        sf.write(f"assets/samples/{voice}.wav", audio, 24000)
        print(f"Saved assets/samples/{voice}.wav")
