import gradio as gr
import subprocess
import os
import glob
import shutil

def generate_video(youtube_url, streamer_name, custom_hook):
    work_dir = "/home/nico/OpenClaw_V2/plugins/anime_video_generator"
    
    # 1. Update streamer name in build_short.sh
    shutil.copy2(os.path.join(work_dir, "src/build_short.sh"), os.path.join(work_dir, "src/build_short.sh.bak"))
    
    with open(os.path.join(work_dir, "src/build_short.sh"), "r") as f:
        content = f.read()
    
    import re
    content = re.sub(r'STREAMER_NAME=".*?"', f'STREAMER_NAME="{streamer_name}"', content)
    
    with open(os.path.join(work_dir, "src/build_short.sh"), "w") as f:
        f.write(content)
        
    # 2. Write custom hook if provided
    if custom_hook and custom_hook.strip():
        with open(os.path.join(work_dir, "hook_title.txt"), "w") as f:
            f.write(custom_hook.strip().upper())
    else:
        if os.path.exists(os.path.join(work_dir, "hook_title.txt")):
            os.remove(os.path.join(work_dir, "hook_title.txt"))

    # 3. Clean up previous raw files
    os.system(f"cd {work_dir} && rm -f clip_time.txt clip_fixed.mp4 raw_anime.mp4* raw_video.*")
    
    # 4. Download new video
    if youtube_url and youtube_url.strip():
        yt_cmd = f"/home/nico/.gemini/antigravity/scratch/video-use/venv/bin/yt-dlp --playlist-random --max-downloads 1 '{youtube_url}' -o 'raw_video.%(ext)s' || true && mv raw_video.* raw_anime.mp4 2>/dev/null || true"
        subprocess.run(yt_cmd, shell=True, cwd=work_dir)
        
    # 5. Build
    build_cmd = f"bash src/build_short.sh"
    try:
        subprocess.run(build_cmd, shell=True, cwd=work_dir, check=True)
    except Exception as e:
        return None, None, f"Error building video: {str(e)}"
        
    # 6. Find outputs
    mp4_files = sorted(glob.glob(os.path.join(work_dir, "outputs", "*.mp4")), key=os.path.getmtime, reverse=True)
    jpg_files = sorted(glob.glob(os.path.join(work_dir, "outputs", "*.jpg")), key=os.path.getmtime, reverse=True)
    
    final_video = mp4_files[0] if mp4_files else None
    final_thumbnail = jpg_files[0] if jpg_files else None
    
    return final_video, final_thumbnail, "Success!"

with gr.Blocks(title="Viral Shorts Generator") as demo:
    gr.Markdown("# 🚀 Viral Shorts & Reels Generator")
    gr.Markdown("Automatically download, track faces, add hooks, and beat-sync any streamer's vertical content.")
    
    with gr.Row():
        with gr.Column():
            yt_url = gr.Textbox(label="YouTube/Instagram/TikTok URL (e.g., https://www.youtube.com/@IShowSpeed/shorts)")
            streamer = gr.Textbox(label="Streamer Name (e.g., IShowSpeed, Kai Cenat, Logan Paul)")
            hook = gr.Textbox(label="Custom Title Hook (Max 25 characters, leave blank for AI generation)")
            generate_btn = gr.Button("Generate High-Retention Short", variant="primary")
            
        with gr.Column():
            out_video = gr.Video(label="Generated Short")
            out_thumb = gr.Image(label="Generated Thumbnail")
            status = gr.Textbox(label="Status")
            
    generate_btn.click(
        generate_video,
        inputs=[yt_url, streamer, hook],
        outputs=[out_video, out_thumb, status]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
