#!/bin/bash
set -e

STREAMER_NAME="IShowSpeed"
PROJECT_SLUG=$(echo "$STREAMER_NAME" | tr '[:upper:]' '[:lower:]' | tr -d '[:punct:]' | tr ' ' '_')

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
