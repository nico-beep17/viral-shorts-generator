#!/usr/bin/env python3
import sys
from faster_whisper import WhisperModel

video_file = "clip_fixed.mp4"
out_file = "cmd.txt"

print("Loading Whisper 'small' model for high accuracy...")
try:
    model = WhisperModel("small", device="cpu", compute_type="int8")
    
    all_words = []
    
    print(f"Transcribing {video_file}...")
    segments_vid, _ = model.transcribe(video_file, word_timestamps=True)
    for s in segments_vid:
        for w in s.words:
            all_words.append(w)
            
    print("Transcribing narration.wav...")
    segments_narr, _ = model.transcribe("narration.wav", word_timestamps=True)
    for s in segments_narr:
        for w in s.words:
            all_words.append(w)
            
    # Sort chronologically
    all_words.sort(key=lambda x: x.start)
    
except Exception as e:
    print(f"Could not load whisper or read audio: {e}")
    sys.exit(1)

STRONG_WORDS = {'crazy', 'insane', 'never', 'always', 'secret', 'money', 'million', 'billion', 'worst', 'best', 'epic', 'huge', 'massive', 'mindblowing', 'wow', 'dead', 'win', 'lose', 'free', 'real', 'fake', 'stop', 'wait', 'look', 'what', 'omg', 'god', 'bro', 'dude'}
FONT_FILE = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

with open(out_file, "w") as f:
    i = 0
    for w in all_words:
        # Remove single quotes to prevent breaking ffmpeg drawtext syntax
        clean_word = "".join(c for c in w.word.upper() if c.isalnum() or c == "-")
        if not clean_word:
            continue
            
        text = clean_word.upper()
        COLORS = ["yellow", "0x00FF00", "white", "0x00FFFF", "yellow", "white"]
        STRONG_COLORS = ["red", "0xFFA500", "0xFF00FF"]
        
        is_strong = clean_word.lower() in STRONG_WORDS
        if is_strong:
            color = STRONG_COLORS[i % len(STRONG_COLORS)]
            font_size = 150
            border_w = 12
            y_pos = 1220
        else:
            color = COLORS[i % len(COLORS)]
            font_size = 120
            border_w = 9
            y_pos = 1250
            
        style = f"fontcolor={color}:fontsize={font_size}:borderw={border_w}:bordercolor=black:shadowcolor=black:shadowx=8:shadowy=8:fontfile={FONT_FILE}:x=(w-text_w)/2:y={y_pos}"
        
        f.write(f"{w.start:.2f} [enter] drawtext reinit 'text={text}:{style}';\n")
        f.write(f"{w.end:.2f} [enter] drawtext reinit 'text= :{style}';\n")
        i += 1

print(f"Generated {out_file} with dynamic highlighting.")
