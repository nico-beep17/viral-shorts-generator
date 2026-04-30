# AI Anime Video Generator (Hormozi Style)

This plugin autonomously generates high-retention, 9:16 vertical anime Shorts with synchronized, dynamic "Hormozi-style" captions and AI narration.

## Pipeline Architecture
The pipeline relies on three main scripts:
1. `gen_narration.py`: Uses Kokoro TTS (`kokoro-onnx`) to generate a high-quality voiceover (`narration.wav`) from a provided text script.
2. `gen_cmd.py`: Uses `faster-whisper` to transcribe the narration audio and generates an FFmpeg `sendcmd` file (`cmd.txt`). This file dictates precisely when 1-2 word caption chunks appear on-screen.
3. `build_short.sh`: The master FFmpeg rendering script. It composites the raw video, audio, and applies the text styling.

## Aesthetic Configuration
The video layout strictly adheres to the following rules:
- **Aspect Ratio**: 9:16 (Vertical 1080x1920) padded with black bars.
- **Duration**: Strictly less than 59 seconds. The source clip is capped at 50 seconds to guarantee the final looped output stays under 1 minute.
- **Top Hook**: Static white text (LiberationSans-Bold, size 42) stating the premise of the video without clipping.
- **Dynamic Captions**: Centered perfectly in the middle of the screen. Uses a bright yellow font (`#FFFF00`), size 72, with a thick black outline (`borderw=7:bordercolor=black`) and a 5px drop shadow (`shadowx=5:shadowy=5`) for high contrast readability using LiberationSans-Bold font.
- **Watermark Logo**: A semi-transparent (25% opacity) scaled image overlay is perfectly centered at the bottom of the video.
- **Audio Ducking & Diverse BGM**: The system supports various BGM genres (Trap, House, Phonk) to prevent repetition. The BGM and the raw video sound are heavily ducked during the AI narration. When the narration finishes, both the BGM and the original video audio boost back up to over 100% volume for the hyped highlight section.
- **Visual Enhancements**: Blurred dynamic background fill, vignette effect, subtle color grading (saturation/contrast boost), and horizontal flip for copyright resistance. No static lines or scanning overlays.
- **Perfect TikTok Loop**: The last 2.5 seconds of the video are sliced and prepended to the beginning, creating a seamless infinite loop when the Short restarts.

## How To Use
1. Place your raw 16:9 video in this folder as `raw_anime.mp4`.
2. Place your channel logo in this folder as `watermark.jpg`.
3. Download a non-copyrightable song (like NCS Trap or EDM) and save it as `bgm.mp3`.
4. Edit `gen_narration.py` and replace `TEXT` with your desired story.
5. Activate the virtual environments (Kokoro/Whisper).
6. Edit `build_short.sh` and update the `ANIME_NAME` and `HOOK_TITLE` variables at the very top.
7. Run:
   ```bash
   python gen_narration.py
   python gen_cmd.py
   bash build_short.sh
   ```
8. Your final video will be automatically generated with your anime name and a unique timestamp (e.g., `re_zero_season_4_20260423_120000.mp4`). Duration is strictly kept under 59 seconds.
