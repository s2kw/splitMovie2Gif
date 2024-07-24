import argparse
import subprocess
import os
from PIL import Image

def get_audio_duration(audio_file):
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        audio_file
    ]
    output = subprocess.check_output(cmd).decode('utf-8').strip()
    return float(output)

def create_video(image_file, audio_file, output_file, width=None, height=None, fps=30):
    # 画像サイズの取得
    with Image.open(image_file) as img:
        img_width, img_height = img.size

    # 出力サイズの決定
    if width and height:
        out_width, out_height = width, height
    elif width:
        out_width = width
        out_height = int(img_height * (width / img_width))
    elif height:
        out_height = height
        out_width = int(img_width * (height / img_height))
    else:
        out_width, out_height = img_width, img_height

    # 音声の長さを取得
    duration = get_audio_duration(audio_file)

    # FFmpegコマンドの構築
    cmd = [
        'ffmpeg',
        '-loop', '1',
        '-i', image_file,
        '-i', audio_file,
        '-c:v', 'libx264',
        '-tune', 'stillimage',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-vf', f'scale={out_width}:{out_height}:force_original_aspect_ratio=decrease,pad={out_width}:{out_height}:-1:-1:color=black',
        '-shortest',
        '-fflags', '+shortest',
        '-max_interleave_delta', '100M',
        '-t', str(duration),
        '-y',
        output_file
    ]

    # FFmpegを実行
    subprocess.run(cmd, check=True)

    print(f"Video created successfully: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a video from an image and an audio file.")
    parser.add_argument("image_file", help="Path to the image file")
    parser.add_argument("audio_file", help="Path to the audio file (WAV)")
    parser.add_argument("output_file", help="Path for the output video file")
    parser.add_argument("--width", type=int, help="Output video width")
    parser.add_argument("--height", type=int, help="Output video height")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")

    args = parser.parse_args()

    create_video(args.image_file, args.audio_file, args.output_file, args.width, args.height, args.fps)
