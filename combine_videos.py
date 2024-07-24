import os
import subprocess
import argparse
from tqdm import tqdm

def get_video_info(video_file):
    cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-count_packets', '-show_entries', 'stream=width,height,duration',
        '-of', 'csv=p=0', video_file
    ]
    output = subprocess.check_output(cmd).decode('utf-8').strip().split(',')
    return {'width': int(output[0]), 'height': int(output[1]), 'duration': float(output[2])}

def combine_videos(a_files, b_file, output_dir, fade_duration):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    b_info = get_video_info(b_file)
    target_width, target_height = b_info['width'], b_info['height']

    for i, a_file in enumerate(tqdm(a_files, desc="Combining videos")):
        output_file = os.path.join(output_dir, f"combined_{i+1}.mp4")
        
        a_info = get_video_info(a_file)
        a_duration = a_info['duration']
        fade_start = a_duration - fade_duration

        filter_complex = (
            f"[0:v]scale={target_width}:{target_height},setsar=1,fade=t=out:st={fade_start}:d={fade_duration}[v1];"
            f"[0:a]afade=t=out:st={fade_start}:d={fade_duration}[a1];"
            f"[1:v]scale={target_width}:{target_height},setsar=1[v2];"
            "[v1][a1][v2][1:a]concat=n=2:v=1:a=1[outv][outa]"
        )

        cmd = [
            'ffmpeg',
            '-i', a_file,
            '-i', b_file,
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            output_file
        ]

        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Successfully created: {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating {output_file}:")
            print(f"STDOUT: {e.stdout.decode()}")
            print(f"STDERR: {e.stderr.decode()}")

    print(f"Process completed. Please check the output files in {output_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine multiple A videos with a single B video')
    parser.add_argument('a_files', nargs='+', help='Paths to the A video files')
    parser.add_argument('b_file', help='Path to the B video file')
    parser.add_argument('output_dir', help='Path to the output directory')
    parser.add_argument('--fade', type=float, default=1.0, help='Fade duration in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    if not os.access(args.output_dir, os.W_OK):
        print(f"Error: No write permission for the output directory: {args.output_dir}")
    else:
        combine_videos(args.a_files, args.b_file, args.output_dir, args.fade)