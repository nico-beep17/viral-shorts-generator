#!/bin/bash
set -e

STREAMER_NAME="Kai Cenat"
PROJECT_SLUG=$(echo "$STREAMER_NAME" | tr '[:upper:]' '[:lower:]' | tr -d '[:punct:]' | tr ' ' '_')
BGM_FILE="assets/bgm/track_00002.mp3" # Or whatever was randomly picked, since it's just the background

HOOK_TITLE="LIVESTREAM HIGHLIGHT"
if [ -f hook_title.txt ]; then
    HOOK_TITLE=$(cat hook_title.txt)
    echo "Using Dynamic Hook Title: $HOOK_TITLE"
fi

echo "7. Compositing Base Video with 1080x1440 Centered Overlay..."
# The layout is: Blurred background + Centered 1080x1440 clip + Dynamic Cmd Captions + Static Hook
ffmpeg -y -i clip_fixed.mp4 -i clip_panned.mp4 -i narration.wav -i "$BGM_FILE" -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=luma_radius=40:luma_power=5,eq=brightness=-0.1[bg];
    [1:v]eq=saturation=1.2:contrast=1.1,unsharp=5:5:1.0:5:5:0.0[fg];
    [bg][fg]overlay=0:(1920-1440)/2,vignette=PI/4,
    sendcmd=f=cmd.txt,drawtext=text=' ':fontcolor=yellow:fontsize=72:borderw=7:bordercolor=black:shadowcolor=black:shadowx=5:shadowy=5:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf,
    drawtext=text='${HOOK_TITLE}':fontcolor=white:fontsize=80:borderw=8:bordercolor=black:shadowcolor=black:shadowx=5:shadowy=5:box=1:boxcolor=red@0.8:boxborderw=15:x=(w-text_w)/2:y=300:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf,
    drawtext=text='${STREAMER_NAME}':fontcolor=yellow:fontsize=56:borderw=6:bordercolor=black:shadowcolor=black:shadowx=4:shadowy=4:box=1:boxcolor=black@0.8:boxborderw=10:x=(w-text_w)/2:y=420:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf[vsub];
    [vsub]drawtext=text='@openclips_ai':fontcolor=white@0.5:fontsize=48:x=(w-text_w)/2:y=1600:fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf[vfinal];
    [0:a]volume=0.8[a_main];
    [2:a]volume=10.0[a_narr];
    [3:a]volume=0.1,bass=g=5[a_music];
    [a_main][a_narr][a_music]amix=inputs=3:duration=first:dropout_transition=2:normalize=0[aout]
" -map "[vfinal]" -map "[aout]" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k -threads 1 -shortest final_short_temp.mp4

echo "10. Final Assembly..."
ffmpeg -y -i final_short_temp.mp4 -vf "fps=60,setsar=1:1" -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k main_normalized.mp4

# Montage loop
ffmpeg -y -i montage_last4.mp4 -i main_normalized.mp4 -i montage_first4.mp4 -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k final_short.mp4

FINAL_OUT="${PROJECT_SLUG}_$(date +%Y%m%d_%H%M%S).mp4"
mv final_short.mp4 "outputs/$FINAL_OUT"

echo "Done! Your video is saved as: outputs/$FINAL_OUT"
