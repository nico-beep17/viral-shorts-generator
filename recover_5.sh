#!/bin/bash
set -e

STREAMER_NAME="Kai Cenat"
PROJECT_SLUG=$(echo "$STREAMER_NAME" | tr '[:upper:]' '[:lower:]' | tr -d '[:punct:]' | tr ' ' '_')
BGM_FILE=$(ls assets/bgm/*.mp3 | shuf -n 1)

echo "5. Generating Dynamic Captions (Streamer + Narration)..."
/home/nico/.gemini/antigravity/scratch/video-use/venv/bin/python src/gen_cmd.py

echo "7. Assembling Composite Video (Background + Game + HUD + Subtitles)..."
ffmpeg -y -i clip_fixed.mp4 -i clip_panned.mp4 -i narration.wav -i "$BGM_FILE" -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5,setsar=1:1[bg];
    [1:v]scale=1080:1440:force_original_aspect_ratio=decrease,setsar=1:1,
         hue=s=1.2,eq=contrast=1.1,unsharp=5:5:1.0:5:5:0.0[fg];
    [bg][fg]overlay=0:(1920-1440)/2,vignette=PI/4,
    sendcmd=f=cmd.txt,drawtext=text=' ':fontcolor=yellow:fontsize=72:borderw=7:bordercolor=black:shadowcolor=black:shadowx=5:shadowy=5:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf,
    drawtext=textfile=hook_title.txt:fontcolor=white:fontsize=100:borderw=10:bordercolor=red:shadowcolor=black:shadowx=8:shadowy=8:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf:x=(w-text_w)/2:y=300:enable='between(t,0,4)'[vfinal];
    [0:a]volume=1.5[a_orig];
    [2:a]volume=10.0[a_narr];
    [3:a]volume=0.3[a_bgm];
    [a_orig][a_narr][a_bgm]amix=inputs=3:duration=first:dropout_transition=2[aout]
" -map "[vfinal]" -map "[aout]" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k -threads 1 -shortest final_short_temp.mp4

echo "10. Final Assembly..."
ffmpeg -y -i final_short_temp.mp4 -vf "fps=60,setsar=1:1" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k main_normalized.mp4

# Montage loop
ffmpeg -y -i montage_last4.mp4 -i main_normalized.mp4 -i montage_first4.mp4 -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k final_short.mp4

FINAL_OUT="${PROJECT_SLUG}_$(date +%Y%m%d_%H%M%S).mp4"
mv final_short.mp4 "outputs/$FINAL_OUT"

echo "Done! Your video is saved as: outputs/$FINAL_OUT"
