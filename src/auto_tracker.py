import cv2
import sys
import numpy as np

def track_video(input_path, output_path, target_width=1080, target_height=1188):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print("Error opening video")
        sys.exit(1)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (target_width, target_height))

    # Anime face detection cascade
    face_cascade = cv2.CascadeClassifier('lbpcascade_animeface.xml')

    scaled_width = int(width * (target_height / height))
    current_x = (scaled_width - target_width) // 2
    desired_x = current_x
    
    print("Tracking faces...")
    frame_count = 0
    while True:
        ret, raw_frame = cap.read()
        if not ret:
            break
            
        # Scale frame to height 1188
        h, w = raw_frame.shape[:2]
        new_w = int(w * (target_height / h))
        frame = cv2.resize(raw_frame, (new_w, target_height))
        
        width = new_w
        height = target_height
        
        frame_count += 1
        # Only run detection every 6 frames to speed up
        if frame_count % 6 == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                # Get the largest face
                faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
                fx, fy, fw, fh = faces[0]
                # Target center
                target_cx = fx + fw // 2
                desired_x = target_cx - target_width // 2
            else:
                # Default to center if no face
                desired_x = (width - target_width) // 2
                
            # Clamp desired_x
            desired_x = max(0, min(desired_x, width - target_width))
        
        # Smoothly interpolate current_x towards desired_x
        current_x = current_x + (desired_x - current_x) * 0.1
        
        # Crop
        x_int = int(current_x)
        y_int = (height - target_height) // 2
        
        cropped = frame[y_int:y_int+target_height, x_int:x_int+target_width]
        out.write(cropped)

    cap.release()
    out.release()
    print("Tracking complete.")

if __name__ == "__main__":
    track_video("clip_fixed.mp4", "clip_tracked.mp4")
