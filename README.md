# 🚀 Viral Shorts & Reels Generator PRO

An autonomous, fully-automated AI video pipeline that converts long-form VODs and YouTube streams into high-retention, seamlessly looping vertical Shorts/Reels/TikToks. 

Built with advanced computer vision, audio processing, and a beautiful Gradio web interface.

## 🌟 Key Features

* **🤖 Auto-Clipper (Climax Detection):** Automatically scans massive VODs for the highest-energy, non-vocal action sequences using motion tracking, audio spike detection, and tension scoring.
* **🎯 AI Face & Saliency Tracking:** No more manual panning. The system runs every frame through Haar Cascades and Spectral Saliency mapping to ensure the streamer's face (or the most interesting object) is perfectly centered in the 1080x1920 vertical crop.
* **🗣️ AI Narrator & Dynamic Captions:** Leverages Kokoro-82M TTS for expressive storytelling hooks and Faster-Whisper to generate perfectly timed, Hormozi-style animated captions.
* **🔊 Phonk Beat-Sync Montage:** Automatically isolates the heaviest bass drop in a background track and stitches together a high-fidelity 60FPS beat-synced action montage, heavily stylized with chromatic aberration, camera shakes, and color vibrance.
* **🔁 Seamless TikTok Looping:** Intelligently splits the final montage so that the video begins with the end of the action sequence, ensuring that when the video loops on TikTok, it creates an infinite, seamless viewing experience.
* **🔥 Multi-Clip Output:** Generate up to 5 completely unique, ranked clips back-to-back from a single YouTube URL, all with dynamically selected unique background music and custom text hooks.

## 🛠️ Architecture

1. **Gradio UI (`app_v5.py`)**: A modern web dashboard that accepts YouTube URLs, streamer names, and settings. It automatically pulls older viral clips via `yt-dlp`.
2. **Orchestrator (`build_short.sh`)**: The bash engine that chains all Python scripts and FFmpeg filters together.
3. **AI Clipper (`auto_clipper.py`)**: Slices the video into non-overlapping high-retention windows.
4. **AI Director (`auto_director.py`)**: Analyzes the scene context to generate dynamic text hooks.
5. **Tracker (`generate_pan.py`)**: Frame-by-frame computer vision cropping.
6. **Beat Detector (`detect_beats.py`)**: Extracts high-quality frames and renders synced VFX using Librosa and OpenCV.

## 🚀 How to Run (Portable)

This project is fully portable and uses relative paths. 

1. **Install Dependencies:**
   Ensure you have `ffmpeg` and `yt-dlp` installed on your system.
   ```bash
   pip install gradio faster-whisper librosa opencv-python numpy soundfile torch
   ```
2. **Launch the Web UI:**
   ```bash
   python3 app_v5.py
   ```
3. **Generate:**
   Open your browser to `http://localhost:7864`. Select a streamer from the dropdown or paste a custom URL, select the number of clips, and click Generate!

*(Note: If running on Windows/Mac, ensure you update the FFmpeg `fontfile` path in `src/build_short.sh` to a local system font like Arial).*

## 📈 Outputs
All generated videos and high-saturation thumbnails are automatically saved to the `outputs/` folder.
