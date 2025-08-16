import os
from tkinter import Tk, filedialog, simpledialog, messagebox
from concurrent.futures import ThreadPoolExecutor
from moviepy.editor import VideoFileClip

def process_clip(video_path, output_filename, start_time, end_time, resolution, aspect_ratio, rotate, crop):
    with VideoFileClip(video_path).subclip(start_time, end_time) as clip:
        
        # Rotate if user requested and clip is wider than tall
        if rotate and clip.w > clip.h:
            clip = clip.rotate(90)
        
        # Force aspect ratio handling
        target_w, target_h = resolution
        if aspect_ratio != "original":
            if crop:
                # Crop center to fit ratio
                if aspect_ratio == "9:16":
                    target_h = int(clip.w * 16 / 9)
                    clip = clip.crop(
                        x_center=clip.w / 2,
                        y_center=clip.h / 2,
                        width=clip.w,
                        height=target_h
                    )
                elif aspect_ratio == "16:9":
                    target_h = int(clip.w * 9 / 16)
                    clip = clip.crop(
                        x_center=clip.w / 2,
                        y_center=clip.h / 2,
                        width=clip.w,
                        height=target_h
                    )
                clip = clip.resize(resolution)
            else:
                # Fit inside target resolution with black bars
                clip = clip.resize(height=target_h)
                clip = clip.margin(
                    left=(target_w - clip.w) // 2,
                    right=(target_w - clip.w) // 2,
                    color=(0, 0, 0)
                )
        else:
            clip = clip.resize(resolution)

        # Export
        clip.write_videofile(
            output_filename,
            codec="libx264",
            fps=20,
            threads=2,
            preset="ultrafast",
            audio_codec="aac"
        )

def split_and_process_video(video_path, output_dir, clip_duration, resolution, aspect_ratio, rotate, crop):
    with VideoFileClip(video_path) as video:
        total_duration = video.duration

    os.makedirs(output_dir, exist_ok=True)
    num_clips = int(total_duration // clip_duration) + (1 if total_duration % clip_duration else 0)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for i in range(num_clips):
            start_time = i * clip_duration
            end_time = min((i + 1) * clip_duration, total_duration)

            output_filename = os.path.join(output_dir, f"clip_{i+1:03d}.mp4")
            futures.append(
                executor.submit(process_clip, video_path, output_filename, start_time, end_time, resolution, aspect_ratio, rotate, crop)
            )

        for future in futures:
            future.result()

if __name__ == "__main__":
    # File selection
    root = Tk()
    root.withdraw()
    video_path = filedialog.askopenfilename(
        title="Select a video file",
        filetypes=[("Video Files", "*.mp4 *.mkv *.mov *.avi")]
    )
    if not video_path:
        messagebox.showerror("Error", "No video selected!")
        exit()

    # Clip duration
    clip_duration = simpledialog.askinteger("Clip Duration", "Enter clip duration in seconds:", initialvalue=50)

    # Resolution
    resolution_choice = simpledialog.askstring(
        "Resolution",
        "Enter output resolution (widthxheight), e.g. 1080x1920:",
        initialvalue="1080x1920"
    )
    resolution = tuple(map(int, resolution_choice.lower().split("x")))

    # Aspect ratio
    aspect_ratio = simpledialog.askstring(
        "Aspect Ratio",
        "Choose aspect ratio (original / 9:16 / 16:9 / 1:1):",
        initialvalue="9:16"
    )

    # Rotation
    rotate = messagebox.askyesno("Rotation", "Rotate video if it's landscape?")

    # Cropping
    crop = messagebox.askyesno("Cropping", "Crop to fill screen? (No = add black bars)")

    # Output folder
    output_dir = filedialog.askdirectory(title="Select output folder")
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(video_path), "output_clips")

    root.destroy()

    # Run processing
    split_and_process_video(video_path, output_dir, clip_duration, resolution, aspect_ratio, rotate, crop)
    messagebox.showinfo("Done", f"✅ Processing completed.\nClips saved in: {output_dir}")
