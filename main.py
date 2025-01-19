import os
import argparse
import subprocess
from tqdm import tqdm
import math

def get_video_info(input_file):
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
           '-count_packets', '-show_entries', 'stream=width,height,r_frame_rate,bit_rate', 
           '-of', 'csv=p=0', input_file]
    output = subprocess.check_output(cmd).decode('utf-8').strip().split(',')
    return {'width': int(output[0]), 'height': int(output[1]), 
            'fps': eval(output[2]), 'bitrate': int(output[3]) if output[3] != 'N/A' else None}

def create_output(input_file, start, end, output_file, fps, scale, output_type, video_info, include_audio):
    cmd = ['ffmpeg', '-y', '-i', input_file, '-ss', str(start), '-t', str(end - start)]
    
    if fps:
        cmd.extend(['-r', str(fps)])
    
    if scale:
        cmd.extend(['-vf', f'scale={scale}:-1'])

    if output_type == 'gif':
        cmd.extend(['-f', 'gif'])
    elif output_type == 'mp4':
        if include_audio:
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
        else:
            cmd.extend(['-c:v', 'libx264', '-an'])
    
    cmd.append(output_file)
    
    try:
        print(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error executing FFmpeg command: {result.stderr}")
            return False
            
        if os.path.getsize(output_file) == 0:
            print(f"Warning: Output file {output_file} is empty!")
            return False
            
        return True
            
    except Exception as e:
        print(f"Error during file creation: {str(e)}")
        return False

def split_video(input_file, output_dir, duration=15.0, fps=None, scale=None, output_type='gif', include_audio=True):
    video_info = get_video_info(input_file)
    fps = fps or video_info['fps']
    scale = scale or video_info['width']
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    total_duration = float(subprocess.check_output([
        'ffprobe', '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        input_file
    ]).strip())
    
    num_segments = math.ceil(total_duration / duration)
    
    print(f"Total {output_type.upper()} files to create: {num_segments}")
    
    for i in tqdm(range(num_segments), desc=f"Creating {output_type.upper()} files"):
        start = i * duration
        end = min((i + 1) * duration, total_duration)
        output_file = os.path.join(output_dir, f"output_{i+1}.{output_type}")
        if not create_output(input_file, start, end, output_file, fps, scale, output_type, video_info, include_audio):
            print(f"Failed to create segment {i+1}")
            continue

def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()

def main():
    parser = argparse.ArgumentParser(description='Split video into segments')
    parser.add_argument('input_file', help='Path to the input video file')
    parser.add_argument('output_dir', help='Path to the output directory')
    parser.add_argument('--type', choices=['gif', 'mp4'], default='gif', help='Output file type (default: gif)')
    parser.add_argument('--duration', type=float, default=15.0, help='Duration of each segment in seconds (default: 15.0)')
    parser.add_argument('--fps', type=int, help='Frames per second (default: same as input)')
    parser.add_argument('--scale', type=int, help='Output width in pixels (default: same as input)')
    parser.add_argument('--no-audio', action='store_true', help='Remove audio from MP4 output (ignored for GIF)')
    
    args = parser.parse_args()
    
    # 入力ファイルの拡張子をチェック
    input_extension = get_file_extension(args.input_file)
    if input_extension not in ['.mp4', '.mov']:
        print(f"Warning: Input file format '{input_extension}' may not be supported. Proceeding anyway...")
    
    include_audio = not args.no_audio if args.type == 'mp4' else False
    split_video(
        args.input_file,
        args.output_dir,
        duration=args.duration,
        fps=args.fps,
        scale=args.scale,
        output_type=args.type,
        include_audio=include_audio
    )

if __name__ == '__main__':
    main()