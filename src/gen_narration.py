#!/usr/bin/env python3
import kokoro
import soundfile as sf
import numpy as np
import json
import sys
import os
import gc

gc.collect()

if not os.path.exists("narrations.json"):
    print("Error: narrations.json not found. Run auto_director.py first.")
    sys.exit(1)

with open("narrations.json", "r") as f:
    narrations_data = json.load(f)

NARRATIONS = [(item["start"], item["text"]) for item in narrations_data]

TOTAL_DURATION = 50.0  # Length of the short
SR = 24000

print("Loading Kokoro am_onyx...")
try:
    pipeline = kokoro.KPipeline(lang_code='a')
except Exception as e:
    print(f"Error loading Kokoro: {e}")
    sys.exit(1)

total_samples = int(TOTAL_DURATION * SR)
full_audio = np.zeros(total_samples, dtype=np.float32)

for start_time, text in NARRATIONS:
    print(f"Synthesizing at {start_time:.2f}s: {text}")
    samples = []
    for result in pipeline(text, voice='am_onyx', speed=1.1):
        if result.audio is not None:
            samples.append(result.audio.numpy())
    
    if samples:
        audio = np.concatenate(samples)
        start_idx = int(start_time * SR)
        end_idx = start_idx + len(audio)
        
        if end_idx > total_samples:
            end_idx = total_samples
            audio = audio[:(end_idx - start_idx)]
            
        full_audio[start_idx:end_idx] += audio

max_val = np.max(np.abs(full_audio))
if max_val > 1.0:
    full_audio = full_audio / max_val

sf.write("narration.wav", full_audio, SR)
print("Saved targeted narration.wav")
