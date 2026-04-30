#!/usr/bin/env python3
import sys
import json
import librosa
import numpy as np
import random
from faster_whisper import WhisperModel
import os

video_file = "clip_fixed.mp4"
out_file = "narrations.json"

if not os.path.exists(video_file):
    print(f"Error: {video_file} not found.")
    sys.exit(1)

print("AI Director: Analyzing video dynamics and speech...")

# 1. Transcribe the video to find when the streamer speaks
print("AI Director: Transcribing streamer speech to find silent gaps...")
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, info = model.transcribe(video_file, word_timestamps=False)

speech_segments = []
for s in segments:
    speech_segments.append((s.start, s.end, s.text))

# 2. Analyze audio to find the climax (loudest reaction)
print("AI Director: Analyzing audio waveform to locate the climax/reaction...")
y, sr = librosa.load(video_file, sr=16000)
rms = librosa.feature.rms(y=y)[0]
times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
climax_idx = np.argmax(rms)
climax_time = times[climax_idx]

print(f"AI Director: Climax detected at {climax_time:.2f}s")

with open("climax_time.txt", "w") as f:
    f.write(str(climax_time))

narrations = []

import urllib.request
import urllib.parse

# Analyze transcription for context keywords
full_text = " ".join([text for _, _, text in speech_segments])
truncated_text = full_text[:1500]

prompt = f"""You are an expert TikTok editor. Here is a video transcript:
"{truncated_text}"
Analyze the context. Generate a JSON with two keys:
1. "title": A persistent on-screen text hook (MAX 25 CHARACTERS, all uppercase). It must create an "information gap" that forces the viewer to watch until the end. Use proven curiosity formulas like: "WAIT UNTIL THE END", "THE SECRET TO...", "THIS IS CRAZY!", "PLOT TWIST...", "WHAT HAPPENS NEXT". Do NOT just describe the video literally.
2. "narration": A 1-sentence voiceover script (max 15 words) setting the scene. It MUST make the viewer extremely curious about what happens at the end (e.g., "Wait until you see how they handle this.", "You won't believe what happens at the end."). Make it sound like a gripping movie narrator.

Return ONLY raw valid JSON, no markdown formatting. Example: {{"title": "TRYING A NEW GAME", "narration": "He decides to finally test the hardest level."}}"""

url = "https://text.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
url += "?seed=" + str(random.randint(1, 1000000))

hook_title = "WAIT UNTIL THE END"
hook_narration = "Things get incredibly awkward when they realize what just happened."

try:
    print("AI Director: Requesting dynamic context-aware hook from LLM...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        result = response.read().decode('utf-8')
        
    # Clean the response in case there are markdown blocks
    result = result.replace('```json', '').replace('```', '').strip()
    data = json.loads(result)
    hook_title = data.get("title", hook_title).upper()
    hook_narration = data.get("narration", hook_narration)
    print(f"AI Director: Generated Dynamic Hook via LLM!")
except Exception as e:
    print(f"AI Director: LLM API failed ({e}). Using default hooks.")

print(f"AI Director: Setting Hook Title to: {hook_title}")
print(f"AI Director: Setting Hook Narration to: {hook_narration}")

# Save the dynamic hook title for build_short.sh to read
with open("hook_title.txt", "w") as f:
    f.write(hook_title)

# High retention Hooks (Dynamic)
HOOKS = [hook_narration]

# Mid-video context
GAPS = [
    "The tension is unreal right now.",
    "He's trying to figure out what to do.",
    "Everything is about to change.",
    "Notice how quiet it got.",
    "This is pure focus."
]

# Pre-reaction
PRE_REACTIONS = [
    "Wait for it...",
    "Here it comes...",
    "Watch his face...",
    "And then... this happened."
]

# 1. THE HOOK (Always at 0.5s to grab attention)
narrations.append({"start": 0.5, "text": random.choice(HOOKS)})

# 2. SILENCE FILLER (Find a gap > 3 seconds)
longest_gap = 0
best_gap_start = 0
if len(speech_segments) > 1:
    for i in range(len(speech_segments)-1):
        gap = speech_segments[i+1][0] - speech_segments[i][1]
        if gap > longest_gap:
            longest_gap = gap
            best_gap_start = speech_segments[i][1] + 0.5

# Ensure the gap is long enough, not too close to the start, and not overlapping the climax
if longest_gap > 3.0 and best_gap_start > 5.0 and abs(best_gap_start - climax_time) > 4.0:
    narrations.append({"start": best_gap_start, "text": random.choice(GAPS)})

# 3. THE BUILDUP (2.5 seconds before the climax)
pre_climax_time = climax_time - 2.5
if pre_climax_time > 4.0:
    overlap = False
    for n in narrations:
        if abs(n["start"] - pre_climax_time) < 3.0:
            overlap = True
    if not overlap:
        narrations.append({"start": pre_climax_time, "text": random.choice(PRE_REACTIONS)})

# Sort by start time
narrations.sort(key=lambda x: x["start"])

with open(out_file, "w") as f:
    json.dump(narrations, f, indent=4)

print("AI Director: Finalized Narration Script:")
for n in narrations:
    print(f"  [{n['start']:.2f}s] {n['text']}")
