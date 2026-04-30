#!/usr/bin/env python3
import cv2
import librosa
import numpy as np
import subprocess
import os
import sys

video_path = "raw_anime.mp4"
window_length = 50.0

if not os.path.exists(video_path):
    print(f"Error: {video_path} not found.")
    sys.exit(1)

print("AI Clipper: Scanning full video for the most exciting non-vocal action sequence...")

# Extract low-res audio for fast analysis
subprocess.run(["ffmpeg", "-y", "-i", video_path, "-ac", "1", "-ar", "8000", "temp_audio.wav"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    y, sr = librosa.load("temp_audio.wav", sr=8000)
except Exception as e:
    print(f"Failed to load audio: {e}")
    sys.exit(1)

# Compute RMS energy (volume) to detect loudness/screaming
rms_env = librosa.feature.rms(y=y)[0]

# Compute onset strength (percussive sounds/fast movement)
onset_env = librosa.onset.onset_strength(y=y, sr=sr)

# Fast visual motion scan (1 frame per second)
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0: fps = 24.0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps

print(f"AI Clipper: Analyzing {duration:.0f} seconds of visual and audio data...")

motion_scores = []
prev_frame = None

# Sample 1 frame per second
for sec in range(int(duration)):
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()
    if not ret:
        motion_scores.append(0)
        continue
    
    # Resize heavily for speed
    gray = cv2.cvtColor(cv2.resize(frame, (160, 90)), cv2.COLOR_BGR2GRAY)
    if prev_frame is not None:
        diff = cv2.absdiff(prev_frame, gray)
        motion_scores.append(np.mean(diff))
    else:
        motion_scores.append(0)
    prev_frame = gray

cap.release()

# Synchronize audio features to 1 per second
onset_per_sec = []
rms_per_sec = []
samples_per_sec = len(onset_env) / duration
rms_samples_per_sec = len(rms_env) / duration

for sec in range(int(duration)):
    start_idx = int(sec * samples_per_sec)
    end_idx = int((sec + 1) * samples_per_sec)
    if start_idx < len(onset_env) and start_idx < end_idx:
        onset_per_sec.append(np.mean(onset_env[start_idx:end_idx]))
    else:
        onset_per_sec.append(0)
        
    rms_start_idx = int(sec * rms_samples_per_sec)
    rms_end_idx = int((sec + 1) * rms_samples_per_sec)
    if rms_start_idx < len(rms_env) and rms_start_idx < rms_end_idx:
        rms_per_sec.append(np.mean(rms_env[rms_start_idx:rms_end_idx]))
    else:
        rms_per_sec.append(0)

motion_scores = np.array(motion_scores)
onset_per_sec = np.array(onset_per_sec)
rms_per_sec = np.array(rms_per_sec)

# Compute sudden tension spikes (jump scares, sudden screaming)
rms_diff = np.diff(rms_per_sec, prepend=0)
tension_spikes = np.clip(rms_diff, 0, None) # Only care about positive volume spikes

# Normalize
if np.max(motion_scores) > 0: motion_scores = motion_scores / np.max(motion_scores)
if np.max(onset_per_sec) > 0: onset_per_sec = onset_per_sec / np.max(onset_per_sec)
if np.max(rms_per_sec) > 0: rms_per_sec = rms_per_sec / np.max(rms_per_sec)
if np.max(tension_spikes) > 0: tension_spikes = tension_spikes / np.max(tension_spikes)

# Total Emotional Score = High Audio Tension (Sudden spikes/screams) + Loud Volume + Visual Motion
# This perfectly targets jump scares, rage moments, and extreme emotional reactions
total_scores = tension_spikes * 0.4 + rms_per_sec * 0.3 + motion_scores * 0.2 + onset_per_sec * 0.1

best_starts = []
window_size = int(window_length)

if len(total_scores) <= window_size + 5:
    best_start = 0
    max_window_score = np.sum(total_scores) if len(total_scores) > 0 else 0.0
else:
    for i in range(len(total_scores) - window_size - 5):
        window_score = np.sum(total_scores[i:i+window_size])
        best_starts.append((window_score, i))
    
    best_starts.sort(reverse=True)
    filtered_starts = []
    for score, start in best_starts:
        overlap = False
        for _, f_start in filtered_starts:
            if abs(start - f_start) < window_size:
                overlap = True
                break
        if not overlap:
            filtered_starts.append((score, start))
            if len(filtered_starts) >= 5:
                break
    
    if len(filtered_starts) > 0:
        for idx, chosen in enumerate(filtered_starts[:5]):
            best_start = chosen[1]
            max_window_score = chosen[0]
            print(f"AI Clipper: Rank #{idx+1} climax starting at {best_start} seconds! (Score: {max_window_score:.2f})")
            h = best_start // 3600
            m = (best_start % 3600) // 60
            s = best_start % 60
            time_str = f"{h:02d}:{m:02d}:{s:02d}"
            with open(f"clip_time_{idx+1}.txt", "w") as f:
                f.write(time_str)
    else:
        print("AI Clipper: No suitable action sequence found, using start of video.")
        with open("clip_time_1.txt", "w") as f:
            f.write("00:00:00")

if os.path.exists("temp_audio.wav"):
    os.remove("temp_audio.wav")
