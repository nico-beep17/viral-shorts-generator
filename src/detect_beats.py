import librosa
import numpy as np
import cv2
import sys
import os
import random
import subprocess

def create_beat_montage(bgm_path, video_path, output_concat, duration=8.0):
    """Generate an 8-second beat-synced montage from video highlights."""
    print(f"Analyzing {bgm_path} for beats ({duration}s montage)...")
    y, sr = librosa.load(bgm_path)
    
    # Use the most energetic section of the BGM for the montage
    # Analyze onset strength to find bass drops
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    
    # Find the highest-energy 8-second window in the track
    hop_length = 512
    window_frames = int(duration * sr / hop_length)
    if len(onset_env) > window_frames:
        energy = np.convolve(onset_env, np.ones(window_frames), mode='valid')
        best_start_frame = np.argmax(energy)
        best_start_time = librosa.frames_to_time(best_start_frame, sr=sr)
    else:
        best_start_time = 0.0
    
    # Extract audio chunk from the best window
    start_sample = int(best_start_time * sr)
    end_sample = min(len(y), start_sample + int(duration * sr))
    y_chunk = y[start_sample:end_sample]
    import soundfile as sf
    sf.write('montage_bgm.wav', y_chunk, sr)
    
    tempo, beat_frames = librosa.beat.beat_track(y=y_chunk, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    if len(beat_times) < 2:
        print("Not enough beats detected, generating evenly spaced cuts...")
        beat_times = np.linspace(0, duration, int(duration * 3))

    print(f"Detected {len(beat_times)} beats for the montage.")

    # Extract visually interesting frames from the video
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 24.0
    
    frames_dir = "montage_frames"
    os.makedirs(frames_dir, exist_ok=True)
    # Clean old frames
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))
    
    concat_lines = []
    
    # Build intervals from beat times
    intervals = []
    if beat_times[0] > 0.01:
        intervals.append(beat_times[0])
    for i in range(len(beat_times) - 1):
        intervals.append(beat_times[i+1] - beat_times[i])
    remaining = duration - beat_times[-1]
    if remaining > 0.01:
        intervals.append(remaining)
    
    # Use FFmpeg to extract 1 frame every 10 seconds to bypass AV1 codec issues in OpenCV
    temp_dir = "temp_samples"
    os.makedirs(temp_dir, exist_ok=True)
    for f in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, f))
        
    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vf", "fps=1", "-qscale:v", "2", f"{temp_dir}/sample_%04d.jpg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    sample_files = sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.jpg')])
    
    scored_frames = []
    face_cascade = cv2.CascadeClassifier('assets/lbpcascade_animeface.xml')
    for idx, path in enumerate(sample_files):
        frame = cv2.imread(path)
        if frame is not None:
            # Score by face presence + color variance + edge density
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.05, 3, minSize=(40, 40))
            face_score = 5.0 if len(faces) > 0 else 0.0
            edges = cv2.Canny(gray, 50, 150)
            edge_score = np.mean(edges) / 255.0
            color_score = np.std(frame) / 128.0
            score = face_score + edge_score * 0.6 + color_score * 0.4
            scored_frames.append((idx, score))
    
    # Sort by score descending, pick the best ones
    scored_frames.sort(key=lambda x: x[1], reverse=True)
    best_frame_indices = [sf[0] for sf in scored_frames[:len(intervals) + 5]]
    random.shuffle(best_frame_indices)
    
    print(f"Extracting frames and rendering 60FPS beat-drop effects...")
    
    global_frame_idx = 0
    fps_out = 60
    
    for i, duration_sec in enumerate(intervals):
        if duration_sec < 0.01:
            continue
            
        # Use scored frame if available, otherwise random
        if i < len(best_frame_indices):
            frame_idx = best_frame_indices[i]
        else:
            frame_idx = random.randint(0, len(sample_files) - 1)
        
        frame = cv2.imread(sample_files[frame_idx])
        if frame is not None:
            # Scale to fill 1080x1920 while maintaining aspect ratio
            h, w = frame.shape[:2]
            scale_w = 1080 / w
            scale_h = 1920 / h
            scale = max(scale_w, scale_h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            
            # Center crop to exactly 1080x1920
            start_x = (new_w - 1080) // 2
            start_y = (new_h - 1920) // 2
            base_cropped = resized[start_y:start_y+1920, start_x:start_x+1080]
            
            # 1. Unsharp Mask to FIX BLURRINESS
            gaussian = cv2.GaussianBlur(base_cropped, (0, 0), 2.0)
            base_enhanced = cv2.addWeighted(base_cropped, 1.8, gaussian, -0.8, 0)
            
            # 2. Color Enhancement (Vibrance)
            hsv = cv2.cvtColor(base_enhanced, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:,:,1] = np.clip(hsv[:,:,1] * 1.3, 0, 255)
            hsv[:,:,2] = np.clip(hsv[:,:,2] * 1.1, 0, 255)
            base_enhanced = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            
            # Render exactly the number of frames for this beat interval
            frames_in_interval = int(np.round(duration_sec * fps_out))
            for f in range(frames_in_interval):
                t = f / float(fps_out)
                decay = np.exp(-15 * t)  # Very sharp decay for aggressive stomp
                
                # Zoom parameter (Aggressive Stomp: jumps to 1.35x, settles to 1.05x)
                zoom = 1.05 + 0.30 * decay
                
                # Shake parameters (Violent oscillation that dies out)
                shake_x = 60 * np.sin(90 * t) * decay
                shake_y = 60 * np.cos(105 * t) * decay
                
                # Affine transform matrix for zoom and translation
                center = (540, 960)
                M = cv2.getRotationMatrix2D(center, 0, zoom)
                M[0, 2] += shake_x
                M[1, 2] += shake_y
                
                # Apply warp
                frame_warped = cv2.warpAffine(base_enhanced, M, (1080, 1920), borderMode=cv2.BORDER_REFLECT)
                
                # Heavy Chromatic Aberration on the beat
                if decay > 0.05:
                    shift = int(35 * decay)
                    b, g, r = cv2.split(frame_warped)
                    # Shift Red channel right
                    M_r = np.float32([[1, 0, shift], [0, 1, 0]])
                    r_shifted = cv2.warpAffine(r, M_r, (1080, 1920), borderMode=cv2.BORDER_REFLECT)
                    # Shift Blue channel left
                    M_b = np.float32([[1, 0, -shift], [0, 1, 0]])
                    b_shifted = cv2.warpAffine(b, M_b, (1080, 1920), borderMode=cv2.BORDER_REFLECT)
                    frame_warped = cv2.merge((b_shifted, g, r_shifted))
                
                # Flash Effect: Flash white at the exact moment of the beat
                if decay > 0.6:
                    flash_strength = (decay - 0.6) / 0.4  # scales 0 to 1
                    white = np.full_like(frame_warped, 255)
                    frame_warped = cv2.addWeighted(frame_warped, 1 - (0.7 * flash_strength), white, 0.7 * flash_strength, 0)
                
                frame_path = f"{frames_dir}/frame_{global_frame_idx:04d}.jpg"
                cv2.imwrite(frame_path, frame_warped, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                global_frame_idx += 1

    cap.release()
    print(f"Montage generation complete ({global_frame_idx} total 60fps frames rendered).")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: detect_beats.py <bgm_path> <video_path> <output_concat>")
        sys.exit(1)
    create_beat_montage(sys.argv[1], sys.argv[2], sys.argv[3])
