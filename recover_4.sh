#!/bin/bash
set -e

STREAMER_NAME="Kai Cenat"
PROJECT_SLUG=$(echo "$STREAMER_NAME" | tr '[:upper:]' '[:lower:]' | tr -d '[:punct:]' | tr ' ' '_')

BGM_FILE=$(ls assets/bgm/*.mp3 | shuf -n 1)
echo "Selected BGM: $BGM_FILE"

echo "8. Generating 8-Second Beat-Sync Montage..."
# Use raw_anime.mp4 to get diverse scenes from the ENTIRE video instead of the same boring 50s clip!
/home/nico/.gemini/antigravity/scratch/video-use/venv/bin/python src/detect_beats.py "$BGM_FILE" raw_anime.mp4 montage.concat

# Montage is compiled directly from the rendered 60fps image sequence
ffmpeg -y -framerate 60 -i montage_frames/frame_%04d.jpg -i montage_bgm.wav -filter_complex "
    [0:v]setsar=1:1,drawtext=text='@openclips_ai':fontcolor=white@0.5:fontsize=48:x=(w-text_w)/2:y=1600:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf[v]
" -map "[v]" -map 1:a -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -r 60 -c:a aac -b:a 192k -shortest montage.mp4

echo "9. Creating TikTok Loop via Montage Split..."
MONTAGE_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 montage.mp4)
START_TIME=$(awk "BEGIN {print $MONTAGE_DUR - 4}")

ffmpeg -y -i montage.mp4 -filter_complex "
    [0:v]trim=start=${START_TIME}:end=${MONTAGE_DUR},setpts=PTS-STARTPTS,fps=60,setsar=1:1[v];
    [0:a]atrim=start=${START_TIME}:end=${MONTAGE_DUR},asetpts=PTS-STARTPTS[a]
" -map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k montage_last4.mp4

ffmpeg -y -i montage.mp4 -filter_complex "
    [0:v]trim=start=0:end=4,setpts=PTS-STARTPTS,fps=60,setsar=1:1[v];
    [0:a]atrim=start=0:end=4,asetpts=PTS-STARTPTS[a]
" -map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k montage_first4.mp4

echo "10. Final Assembly..."
ffmpeg -y -i final_short_temp.mp4 -vf "fps=60,setsar=1:1" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k main_normalized.mp4

# Use concat filter instead of demuxer to prevent broken timestamps and corrupt files
ffmpeg -y -i montage_last4.mp4 -i main_normalized.mp4 -i montage_first4.mp4 -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k final_short.mp4

FINAL_OUT="${PROJECT_SLUG}_$(date +%Y%m%d_%H%M%S).mp4"
mv final_short.mp4 "outputs/$FINAL_OUT"

echo "Done! Your video is saved as: outputs/$FINAL_OUT"
