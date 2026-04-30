import gradio as gr
import subprocess
import os
import glob
import shutil
import time

def get_bgm_options():
    bgm_path = "/home/nico/OpenClaw_V2/plugins/anime_video_generator/assets/bgm"
    files = glob.glob(os.path.join(bgm_path, "*.mp3"))
    options = ["Random BGM"] + [os.path.basename(f) for f in files]
    return options

def generate_video(youtube_url, streamer_name, custom_hook, bgm_choice, tts_voice, enable_montage):
    work_dir = "/home/nico/OpenClaw_V2/plugins/anime_video_generator"
    
    logs = "Starting generation process with custom features...\n"
    yield None, None, logs
    
    # 1. Update streamer name and BGM in build_short.sh
    shutil.copy2(os.path.join(work_dir, "src/build_short.sh"), os.path.join(work_dir, "src/build_short.sh.bak"))
    with open(os.path.join(work_dir, "src/build_short.sh"), "r") as f:
        content = f.read()
    
    import re
    content = re.sub(r'STREAMER_NAME=".*?"', f'STREAMER_NAME="{streamer_name}"', content)
    
    if bgm_choice != "Random BGM":
        content = re.sub(r'RANDOM_BGM=\$\(find assets/bgm -name "\*\.mp3" \| shuf -n 1\)', f'RANDOM_BGM="assets/bgm/{bgm_choice}"', content)
        
    if not enable_montage:
        # If montage is disabled, just rename the temp file and exit before the montage step
        content = re.sub(r'echo "8\. Generating 8-Second Beat-Sync Montage\.\.\."', 'mv final_short_temp.mp4 final_short.mp4\n    exit 0\n    echo "8. Generating 8-Second Beat-Sync Montage..."', content)
        
    with open(os.path.join(work_dir, "src/build_short.sh"), "w") as f:
        f.write(content)
        
    # 2. Update TTS Voice in auto_director.py
    shutil.copy2(os.path.join(work_dir, "src/auto_director.py"), os.path.join(work_dir, "src/auto_director.py.bak"))
    with open(os.path.join(work_dir, "src/auto_director.py"), "r") as f:
        dir_content = f.read()
    dir_content = re.sub(r'VOICE = ".*?"', f'VOICE = "{tts_voice}"', dir_content)
    with open(os.path.join(work_dir, "src/auto_director.py"), "w") as f:
        f.write(dir_content)
        
    # 3. Write custom hook if provided
    if custom_hook and custom_hook.strip():
        with open(os.path.join(work_dir, "hook_title.txt"), "w") as f:
            f.write(custom_hook.strip().upper())
    else:
        if os.path.exists(os.path.join(work_dir, "hook_title.txt")):
            os.remove(os.path.join(work_dir, "hook_title.txt"))

    # 4. Clean up previous raw files
    os.system(f"cd {work_dir} && rm -f clip_time.txt clip_fixed.mp4 raw_anime.mp4* raw_video.* final_short.mp4 final_thumbnail.jpg")
    
    # 5. Download new video
    if youtube_url and youtube_url.strip():
        logs += f"Downloading source video from {youtube_url}...\n"
        yield None, None, logs
        yt_cmd = f"/home/nico/.gemini/antigravity/scratch/video-use/venv/bin/yt-dlp --playlist-random --max-downloads 1 '{youtube_url}' -o 'raw_video.%(ext)s' || true && mv raw_video.* raw_anime.mp4 2>/dev/null || true"
        process = subprocess.Popen(yt_cmd, shell=True, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            logs += line
            if len(logs) > 6000:
                logs = "..." + logs[-5000:]
            yield None, None, logs
        process.wait()
        
    # 6. Build
    logs += "\nRunning Video Generation Pipeline...\n"
    yield None, None, logs
    build_cmd = f"bash src/build_short.sh"
    process = subprocess.Popen(build_cmd, shell=True, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    for line in process.stdout:
        logs += line
        if len(logs) > 6000:
            logs = "..." + logs[-5000:]
        yield None, None, logs
        
    process.wait()
    
    # Check if the thumbnail script part of build_short was skipped because of the exit 0
    if not enable_montage:
        # We need to run the thumbnail manually since we exited early
        os.system(f"cd {work_dir} && CLIMAX_TIME=$(cat climax_time.txt 2>/dev/null || echo 0) && ffmpeg -y -ss \"$CLIMAX_TIME\" -i main_normalized.mp4 -vframes 1 -q:v 2 raw_thumbnail.jpg && ffmpeg -y -i raw_thumbnail.jpg -vf 'eq=saturation=1.5:contrast=1.2,vignette=PI/4' final_thumbnail.jpg && mv final_thumbnail.jpg outputs/{streamer_name}_thumb.jpg && mv final_short.mp4 outputs/{streamer_name}_nomontage.mp4")
    
    # 7. Restore original files
    shutil.copy2(os.path.join(work_dir, "src/build_short.sh.bak"), os.path.join(work_dir, "src/build_short.sh"))
    shutil.copy2(os.path.join(work_dir, "src/auto_director.py.bak"), os.path.join(work_dir, "src/auto_director.py"))
        
    # 8. Find outputs
    mp4_files = sorted(glob.glob(os.path.join(work_dir, "outputs", "*.mp4")), key=os.path.getmtime, reverse=True)
    jpg_files = sorted(glob.glob(os.path.join(work_dir, "outputs", "*.jpg")), key=os.path.getmtime, reverse=True)
    
    final_video = mp4_files[0] if mp4_files else None
    final_thumbnail = jpg_files[0] if jpg_files else None
    
    logs += "\n✅ Success! Video and Thumbnail generated successfully."
    yield final_video, final_thumbnail, logs

with gr.Blocks(title="Viral Shorts Generator Pro") as demo:
    gr.Markdown("# 🚀 Viral Shorts & Reels Generator PRO")
    gr.Markdown("Advanced generation with direct asset control and real-time terminal output.")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 1. Source & Metadata")
            yt_url = gr.Textbox(label="YouTube/Instagram/TikTok URL (e.g., https://www.youtube.com/@IShowSpeed/shorts)")
            streamer = gr.Textbox(label="Streamer Name (e.g., IShowSpeed, Kai Cenat, Logan Paul)")
            hook = gr.Textbox(label="Custom Title Hook (Max 25 characters, leave blank for AI generation)")
            
            gr.Markdown("### 2. Audio & Video Settings")
            bgm_dropdown = gr.Dropdown(choices=get_bgm_options(), value="Random BGM", label="Background Music (Phonk/Sigma)")
            tts_dropdown = gr.Dropdown(choices=["am_onyx", "am_echo", "am_michael", "af_bella", "af_sarah", "af_sky"], value="am_onyx", label="AI Narrator Voice")
            montage_check = gr.Checkbox(label="Enable 8-Second Phonk Beat-Sync Montage Ending", value=True)
            
            generate_btn = gr.Button("🔥 Generate High-Retention Short 🔥", variant="primary")
            status = gr.Textbox(label="Real-Time Terminal Output", lines=10, max_lines=15)
            
        with gr.Column(scale=1):
            out_video = gr.Video(label="Generated Short")
            out_thumb = gr.Image(label="Generated Thumbnail")
            
    generate_btn.click(
        generate_video,
        inputs=[yt_url, streamer, hook, bgm_dropdown, tts_dropdown, montage_check],
        outputs=[out_video, out_thumb, status]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7862)
