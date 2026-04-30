#!/bin/bash
set -e

HOOK_TITLE="YOU WILL NOT BELIEVE THIS"
STREAMER_NAME="IShowSpeed"
BGM_FILE=$(ls assets/bgm/*.mp3 | shuf -n 1)

echo "Selected BGM: $BGM_FILE"

# 7. Final Composite
ffmpeg -y -i clip_fixed.mp4 -i clip_panned.mp4 -i narration.wav -i "$BGM_FILE" -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=luma_radius=40:luma_power=5,eq=brightness=-0.1[bg];
    [1:v]eq=saturation=1.2:contrast=1.1,unsharp=5:5:1.0:5:5:0.0[fg];
    [bg][fg]overlay=0:(1920-1440)/2,vignette=PI/4,
    sendcmd=f=cmd.txt,drawtext=text=' ':fontcolor=yellow:fontsize=72:borderw=7:bordercolor=black:shadowcolor=black:shadowx=5:shadowy=5:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf,
    drawtext=text='${HOOK_TITLE}':fontcolor=white:fontsize=64:borderw=5:bordercolor=black:shadowcolor=black:shadowx=3:shadowy=3:box=1:boxcolor=red@0.8:boxborderw=15:x=(w-text_w)/2:y=300:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf,
    drawtext=text='${STREAMER_NAME}':fontcolor=yellow:fontsize=48:borderw=5:bordercolor=black:shadowcolor=black:shadowx=3:shadowy=3:box=1:boxcolor=black@0.8:boxborderw=10:x=(w-text_w)/2:y=400:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf[vsub];
    [vsub]drawtext=text='@openclips_ai':fontcolor=white@0.5:fontsize=48:x=(w-text_w)/2:y=1600:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf[vfinal];
    [0:a]volume=0.8[a_main];
    [2:a]volume=10.0[a_narr];
    [3:a]volume=0.1,bass=g=5[a_music];
    [a_main][a_narr][a_music]amix=inputs=3:duration=first:dropout_transition=2:normalize=0[aout]
" -map "[vfinal]" -map "[aout]" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k -threads 1 -shortest final_short_temp.mp4

echo "8. Generating 8-Second Beat-Sync Montage..."
/home/nico/.gemini/antigravity/scratch/video-use/venv/bin/python src/detect_beats.py "$BGM_FILE" clip_fixed.mp4 montage.concat

# Montage is full-screen 1080x1920 with watermark overlay, visual effects, and audio
ffmpeg -y -f concat -safe 0 -i montage.concat -i montage_bgm.wav -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1:1,rgbashift=rh=3:bv=3:gh=-3,drawtext=text='@openclips_ai':fontcolor=white@0.5:fontsize=48:x=(w-text_w)/2:y=1600:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf[v]
" -map "[v]" -map 1:a -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -r 60 -c:a aac -b:a 192k -shortest montage.mp4

echo "9. Creating TikTok Loop via Montage Split..."
MONTAGE_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 montage.mp4)
MONTAGE_HALF=$(awk "BEGIN {print $MONTAGE_DUR / 2}")

ffmpeg -y -i montage.mp4 -t "$MONTAGE_HALF" loop_end.mp4
ffmpeg -y -i montage.mp4 -ss "$MONTAGE_HALF" loop_start.mp4

PROJECT_SLUG=$(echo "$STREAMER_NAME" | tr '[:upper:]' '[:lower:]' | tr -d '[:punct:]' | tr ' ' '_')
FINAL_OUT="outputs/${PROJECT_SLUG}_$(date +%Y%m%d_%H%M%S).mp4"
mkdir -p outputs

cat << EOF > build.concat
file 'loop_start.mp4'
file 'final_short_temp.mp4'
file 'loop_end.mp4'
EOF

ffmpeg -y -f concat -safe 0 -i build.concat -c copy "$FINAL_OUT"

echo "Done! Your video is saved as: $FINAL_OUT"
