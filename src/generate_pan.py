#!/usr/bin/env python3
import cv2
import numpy as np
import sys
import os

def generate_pan(video_path, output_video):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error opening video")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 24.0
    
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # We will scale the original video so the height is at least 1440 AND width is at least 1080
    scale_factor = max(1080 / orig_w, 1440 / orig_h)
    scaled_w = int(orig_w * scale_factor)
    scaled_h = int(orig_h * scale_factor)
    
    out_w, out_h = 1080, 1440

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (out_w, out_h))

    # Use human face cascade instead of anime face
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    saliency = cv2.saliency.StaticSaliencySpectralResidual_create()

    max_x = scaled_w - out_w
    current_x = float(max_x) / 2.0
    alpha = 0.02  # Much smoother panning
    
    no_face_count = 0
    last_face_x = float(max_x) / 2.0

    frame_idx = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Generating auto-panned video to {output_video} ({total_frames} frames)...")
    
    prev_gray = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Human face detection
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(50, 50))
        
        cx = None
        if len(faces) > 0:
            scored_faces = []
            for (x, y, w, h) in faces:
                size_score = w * h
                center_dist = abs((x + w/2) - orig_w/2) / orig_w
                center_score = 1.0 - center_dist
                total_score = size_score * (0.5 + 0.5 * center_score)
                scored_faces.append((total_score, x, y, w, h))
            
            scored_faces.sort(reverse=True)
            _, x, y, w, h = scored_faces[0]
            cx = x + w / 2.0
            last_face_x = cx * scale_factor - (out_w / 2.0)
            last_face_x = max(0, min(max_x, last_face_x))
            no_face_count = 0
        else:
            no_face_count += 1
            cx_motion = None
            if prev_gray is not None:
                diff = cv2.absdiff(prev_gray, gray)
                _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
                thresh = cv2.blur(thresh, (20, 20))
                M_motion = cv2.moments(thresh)
                if M_motion["m00"] > 1000:
                    cx_motion = M_motion["m10"] / M_motion["m00"]
                    
            if cx_motion is not None and no_face_count > 5:
                cx = cx_motion
            elif no_face_count > 10:
                (success, saliencyMap) = saliency.computeSaliency(frame)
                if success:
                    saliencyMap = (saliencyMap * 255).astype("uint8")
                    h_s, w_s = saliencyMap.shape
                    center_weight = np.zeros_like(saliencyMap, dtype=np.float32)
                    cv2.circle(center_weight, (w_s//2, h_s//2), max(w_s, h_s)//2, 1.0, -1)
                    center_weight = cv2.GaussianBlur(center_weight, (0, 0), w_s * 0.3)
                    center_weight = center_weight / center_weight.max()
                    weighted = saliencyMap.astype(np.float32) * (0.3 + 0.7 * center_weight)
                    M = cv2.moments(weighted.astype(np.uint8))
                    if M["m00"] != 0:
                        cx = M["m10"] / M["m00"]

        if cx is not None:
            target_cx = cx * scale_factor
            target_x = target_cx - (out_w / 2.0)
            target_x = max(0, min(max_x, target_x))
        elif no_face_count <= 10:
            target_x = last_face_x
        else:
            target_x = float(max_x) / 2.0

        current_x = (1 - alpha) * current_x + alpha * target_x

        if scale_factor < 1.0:
            resized = cv2.resize(frame, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
        else:
            resized = cv2.resize(frame, (scaled_w, scaled_h), interpolation=cv2.INTER_LANCZOS4)
        start_x = int(current_x)
        end_x = start_x + out_w
        # Center crop from the scaled height
        start_y = max(0, (scaled_h - out_h) // 2)
        cropped = resized[start_y:start_y+out_h, start_x:end_x]
        
        out.write(cropped)
        frame_idx += 1
        prev_gray = gray.copy()
        
        if frame_idx % 50 == 0:
            print(f"  [AI Face Tracking] Processed {frame_idx}/{total_frames} frames...", flush=True)

    cap.release()
    out.release()
    print(f"Auto-panning complete ({frame_idx} frames).")

if __name__ == "__main__":
    generate_pan("clip_fixed.mp4", "clip_panned.mp4")
