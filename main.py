import os
import subprocess
from moviepy.editor import VideoFileClip
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from tqdm import tqdm

def create_gif(args):
    input_file, start, end, output_file, fps, scale = args
    
    cmd = [
        'ffmpeg', '-i', input_file, 
        '-ss', str(start), 
        '-t', str(end - start),
        '-vf', f'fps={fps},scale={scale}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
        '-y', output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return output_file

def split_video_to_gifs(input_file, output_dir, duration=15, fps=10, scale=320):
    video = VideoFileClip(input_file)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    tasks = []
    for i, start in enumerate(range(0, int(video.duration), duration)):
        end = min(start + duration, video.duration)
        output_file = os.path.join(output_dir, f"output_{i+1}.gif")
        tasks.append((input_file, start, end, output_file, fps, scale))
    
    print(f"Total GIFs to create: {len(tasks)}")
    
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        results = list(tqdm(executor.map(create_gif, tasks), total=len(tasks), desc="Creating GIFs"))
    
    video.close()
    
    print(f"All {len(results)} GIFs have been created successfully.")

if __name__ == '__main__':
    # multiprocessing.freeze_support()  # Windows環境で必要な場合はコメントを解除
    input_file = "originFile/20240705.mp4"
#     input_file = "originFile/DBDB 2024-07-05.mp4"
    output_dir = f"out/{input_file}"
    split_video_to_gifs(input_file, output_dir)
