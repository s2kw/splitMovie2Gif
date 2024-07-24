import os
import subprocess
import argparse
from tqdm import tqdm

def get_video_info(input_file):
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
           '-count_packets', '-show_entries', 'stream=width,height,r_frame_rate,bit_rate', 
           '-of', 'csv=p=0', input_file]
    output = subprocess.check_output(cmd).decode('utf-8').strip().split(',')
    return {'width': int(output[0]), 'height': int(output[1]), 
            'fps': eval(output[2]), 'bitrate': int(output[3]) if output[3] != 'N/A' else None}

def create_output(input_file, start, end, output_file, fps, scale, output_type, video_info, include_audio):
    if output_type == 'gif':
        cmd = [
            'ffmpeg', '-i', input_file, 
            '-ss', str(start), 
            '-t', str(end - start),
            '-vf', f'fps={fps},scale={scale}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
            '-y', output_file
        ]
    else:  # mp4 or other video format
        bitrate = video_info['bitrate'] if video_info['bitrate'] else '5M'
        cmd = [
            'ffmpeg', '-i', input_file,
            '-ss', str(start),
            '-t', str(end - start),
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-vf', f'scale={scale}:-1',
            '-b:v', str(bitrate),
        ]
        if include_audio:
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        else:
            cmd.extend(['-an'])
        cmd.extend(['-y', output_file])
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def split_video(input_file, output_dir, duration=15, fps=None, scale=None, output_type='gif', include_audio=True):
    video_info = get_video_info(input_file)
    fps = fps or video_info['fps']
    scale = scale or video_info['width']
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    total_duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_file]).strip())
    
    num_segments = int(total_duration // duration) + (1 if total_duration % duration > 0 else 0)
    
    print(f"Total {output_type.upper()} files to create: {num_segments}")
    
    for i in tqdm(range(num_segments), desc=f"Creating {output_type.upper()} files"):
        start = i * duration
        end = min((i + 1) * duration, total_duration)
        output_file = os.path.join(output_dir, f"output_{i+1}.{output_type}")
        create_output(input_file, start, end, output_file, fps, scale, output_type, video_info, include_audio)
    
    print(f"All {num_segments} {output_type.upper()} files have been created successfully.")

def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split video into GIF or MP4 segments')
    parser.add_argument('input_file', help='Path to the input video file')
    parser.add_argument('output_dir', help='Path to the output directory')
    parser.add_argument('--type', choices=['gif', 'mp4'], default='gif', help='Output file type (default: gif)')
    parser.add_argument('--duration', type=int, default=15, help='Duration of each segment in seconds (default: 15)')
    parser.add_argument('--fps', type=int, help='Frames per second (default: same as input)')
    parser.add_argument('--scale', type=int, help='Output width in pixels (default: same as input)')
    parser.add_argument('--no-audio', action='store_true', help='Remove audio from MP4 output (ignored for GIF)')
    
    args = parser.parse_args()
    
    # 入力ファイルの拡張子をチェック
    input_extension = get_file_extension(args.input_file)
    if input_extension not in ['.mp4', '.mov']:
        print(f"Warning: Input file format '{input_extension}' may not be supported. Proceeding anyway...")
    
    include_audio = not args.no_audio if args.type == 'mp4' else False
    split_video(args.input_file, args.output_dir, args.duration, args.fps, args.scale, args.type, include_audio)