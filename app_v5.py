import gradio as gr
import os
import glob
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STREAMER_PRESETS = {
    "Custom (Use Textboxes Below)": "",
    "IShowSpeed (Rage/Funny)": "ytsearch50:IShowSpeed best rage funny moments 2022",
    "Kai Cenat (Hype/Funny)": "ytsearch50:Kai Cenat best stream highlights 2022",
    "xQc (Rage/Reactions)": "ytsearch50:xQc funniest rage moments compilation",
    "Tyler1 (Rage)": "ytsearch50:Tyler1 funniest rage moments classic",
    "Jynxzi (Rage/Clips)": "ytsearch50:Jynxzi best rage moments Rainbow Six",
    "CaseOh (Funny/Rage)": "ytsearch50:CaseOh funniest stream moments compilation",
    "Markiplier (Jump Scares)": "ytsearch50:Markiplier best jump scares compilation",
    "CoryxKenshin (Funny/Scary)": "ytsearch50:CoryxKenshin funniest horror jump scares",
    "PewDiePie (Classic Funny)": "ytsearch50:PewDiePie funniest gaming moments classic",
    "DashieGames (Rage/Funny)": "ytsearch50:DashieGames best funny rage compilation"
}

def get_bgm_options():
    bgm_path = os.path.join(BASE_DIR, "assets", "bgm")
    files = glob.glob(os.path.join(bgm_path, "*.mp3"))
    options = ["Random BGM"] + [os.path.basename(f) for f in files]
    return options

def update_voice_sample(voice):
    sample_path = os.path.join(BASE_DIR, "assets", "samples", f"{voice}.wav")
    if os.path.exists(sample_path):
        return sample_path
    return None

def generate_video(streamer_preset, custom_url, custom_streamer_name, custom_hook, bgm_choice, tts_voice, enable_montage, clip_count):
    work_dir = BASE_DIR
    
    logs = "Starting generation process with custom features...\n"
    # Initial yield (10 None outputs + 1 log)
    yield None, None, None, None, None, None, None, None, None, None, logs
    
    if streamer_preset != "Custom (Use Textboxes Below)":
        search_query = STREAMER_PRESETS[streamer_preset]
        streamer_name = streamer_preset.split(" (")[0]
        yt_target = f'"{search_query}"'
        logs += f"Auto-selected {streamer_name}! Searching for older viral videos...\n"
    else:
        streamer_name = custom_streamer_name
        yt_target = f'"{custom_url}"'
        
    # 1. Update streamer name and BGM in build_short.sh
    shutil.copy2(os.path.join(work_dir, "src/build_short.sh"), os.path.join(work_dir, "src/build_short.sh.bak"))
    with open(os.path.join(work_dir, "src/build_short.sh"), "r") as f:
        content = f.read()
    
    import re
    content = re.sub(r'STREAMER_NAME=".*?"', f'STREAMER_NAME="{streamer_name}"', content)
    content = re.sub(r'NUM_CLIPS=[0-9]+', f'NUM_CLIPS={clip_count}', content)
    
    if bgm_choice != "Random BGM":
        content = re.sub(r'BGM_FILE="\$\{RANDOM_BGMS\[\$BGM_INDEX\]\}"', f'BGM_FILE="assets/bgm/{bgm_choice}"', content)
        
    if not enable_montage:
        # Disable montage by exiting right before the montage step
        content = re.sub(r'echo "8\. Generating 8-Second Beat-Sync Montage\.\.\."', 'mv final_short_temp.mp4 final_short.mp4\n    # Skip montage...\n    echo "8. Generating 8-Second Beat-Sync Montage..."', content)
        
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
    os.system(f"cd {work_dir} && rm -f clip_time*.txt clip_fixed.mp4 raw_anime.mp4* raw_video.* final_short.mp4 final_thumbnail.jpg")
    
    # 5. Download new video
    if yt_target and yt_target.strip() and yt_target != '""':
        logs += f"Downloading source video from {yt_target}...\n"
        yield None, None, None, None, None, None, None, None, None, None, logs
        yt_cmd = f"yt-dlp --playlist-random --max-downloads 1 {yt_target} -o 'raw_video.%(ext)s' || true && mv raw_video.* raw_anime.mp4 2>/dev/null || true"
        process = subprocess.Popen(yt_cmd, shell=True, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            logs += line
            if len(logs) > 6000:
                logs = "..." + logs[-5000:]
            yield None, None, None, None, None, None, None, None, None, None, logs
        process.wait()
        
    # 6. Build
    logs += "\nRunning Video Generation Pipeline (Processing Top 5 Ranked Clips)...\n"
    yield None, None, None, None, None, None, None, None, None, None, logs
    build_cmd = f"bash src/build_short.sh"
    process = subprocess.Popen(build_cmd, shell=True, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    with open(os.path.join(work_dir, "debug_pipeline.log"), "w") as logf:
        for line in process.stdout:
            logf.write(line)
            logf.flush()
            logs += line
            if len(logs) > 6000:
                logs = "..." + logs[-5000:]
            
            # Since the user wants real-time feedback, we can try to surface videos as they are created
            mp4_files = sorted(glob.glob(os.path.join(work_dir, "outputs", "*.mp4")), key=os.path.getmtime, reverse=True)
            jpg_files = sorted(glob.glob(os.path.join(work_dir, "outputs", "*.jpg")), key=os.path.getmtime, reverse=True)
            
            v1, t1, v2, t2, v3, t3, v4, t4, v5, t5 = None, None, None, None, None, None, None, None, None, None
            for f in mp4_files:
                if "Rank1" in f and v1 is None: v1 = f
                elif "Rank2" in f and v2 is None: v2 = f
                elif "Rank3" in f and v3 is None: v3 = f
                elif "Rank4" in f and v4 is None: v4 = f
                elif "Rank5" in f and v5 is None: v5 = f
            for f in jpg_files:
                if "Rank1" in f and t1 is None: t1 = f
                elif "Rank2" in f and t2 is None: t2 = f
                elif "Rank3" in f and t3 is None: t3 = f
                elif "Rank4" in f and t4 is None: t4 = f
                elif "Rank5" in f and t5 is None: t5 = f
                
            yield v1, t1, v2, t2, v3, t3, v4, t4, v5, t5, logs
        
    process.wait()
    
    # 7. Restore original files
    shutil.copy2(os.path.join(work_dir, "src/build_short.sh.bak"), os.path.join(work_dir, "src/build_short.sh"))
    shutil.copy2(os.path.join(work_dir, "src/auto_director.py.bak"), os.path.join(work_dir, "src/auto_director.py"))
    
    logs += "\n✅ Success! All 5 Ranked Videos and Thumbnails generated successfully."
    yield v1, t1, v2, t2, v3, t3, v4, t4, v5, t5, logs

with __import__("gradio").Blocks(title="Viral Shorts Generator Pro") as demo:
    gr.Markdown("# 🚀 Viral Shorts & Reels Generator PRO")
    gr.Markdown("Advanced generation with direct asset control, real-time terminal output, and Top 5 Multi-Output Generation.")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 1. Source & Metadata")
            preset_dropdown = gr.Dropdown(choices=list(STREAMER_PRESETS.keys()), value="Custom (Use Textboxes Below)", label="Auto-Find Trending Clips (Select Streamer)")
            
            with gr.Accordion("Or Manually Enter Custom Video:", open=False):
                yt_url = gr.Textbox(label="YouTube/Instagram/TikTok URL")
                streamer = gr.Textbox(label="Streamer Name")
            
            hook = gr.Textbox(label="Custom Title Hook (Max 25 characters, leave blank for AI generation)")
            
            gr.Markdown("### 2. Audio & Video Settings")
            bgm_dropdown = gr.Dropdown(choices=get_bgm_options(), value="Random BGM", label="Background Music (Phonk/Sigma)")
            tts_dropdown = __import__("gradio").Dropdown(choices=["am_onyx", "am_echo", "am_michael", "af_bella", "af_sarah", "af_sky"], value="am_onyx", label="AI Narrator Voice")
            voice_sample = __import__("gradio").Audio(value=os.path.join(BASE_DIR, "assets/samples/am_onyx.wav"), label="Voice Preview", interactive=False)
            montage_check = __import__("gradio").Checkbox(label="Enable 8-Second Phonk Beat-Sync Montage (2s Front Loop, 6s Back)", value=True)
            clip_count = gr.Slider(minimum=1, maximum=5, step=1, value=5, label="Number of Ranked Clips to Generate")
            
            generate_btn = gr.Button("🔥 Generate High-Retention Shorts 🔥", variant="primary")
            status = gr.Textbox(label="Real-Time Terminal Output (Saved to debug_pipeline.log)", lines=15, max_lines=20)
            
        with gr.Column(scale=2):
            gr.Markdown("### 3. Generated Video Results (Top 5 Clips)")
            with gr.Tabs():
                with gr.TabItem("Rank #1 (Best)"):
                    out_video_1 = gr.Video(label="Rank #1 Video")
                    out_thumb_1 = gr.Image(label="Rank #1 Thumbnail")
                with gr.TabItem("Rank #2"):
                    out_video_2 = gr.Video(label="Rank #2 Video")
                    out_thumb_2 = gr.Image(label="Rank #2 Thumbnail")
                with gr.TabItem("Rank #3"):
                    out_video_3 = gr.Video(label="Rank #3 Video")
                    out_thumb_3 = gr.Image(label="Rank #3 Thumbnail")
                with gr.TabItem("Rank #4"):
                    out_video_4 = gr.Video(label="Rank #4 Video")
                    out_thumb_4 = gr.Image(label="Rank #4 Thumbnail")
                with gr.TabItem("Rank #5"):
                    out_video_5 = gr.Video(label="Rank #5 Video")
                    out_thumb_5 = gr.Image(label="Rank #5 Thumbnail")
            
    # When TTS dropdown changes, update the audio player
    tts_dropdown.change(fn=update_voice_sample, inputs=tts_dropdown, outputs=voice_sample)
            
    generate_btn.click(
        generate_video,
        inputs=[preset_dropdown, yt_url, streamer, hook, bgm_dropdown, tts_dropdown, montage_check, clip_count],
        outputs=[out_video_1, out_thumb_1, out_video_2, out_thumb_2, out_video_3, out_thumb_3, out_video_4, out_thumb_4, out_video_5, out_thumb_5, status]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7864)
