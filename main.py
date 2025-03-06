import os
import argparse
import subprocess
import math
from tqdm import tqdm

# ---------------
# 共通のユーティリティ
# ---------------

def get_duration(input_file):
    """
    ffprobe を用いて、動画の全長（秒）を取得する。
    """
    cmd = [
        'ffprobe', '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        input_file
    ]
    try:
        output = subprocess.check_output(cmd).strip()
        return float(output)
    except Exception as e:
        print(f"Error getting duration for {input_file}: {e}")
        return None

def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()

# ---------------
# 【再エンコードモード】従来の処理（互換性維持）
# ---------------

def get_video_info(input_file):
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
           '-count_packets', '-show_entries', 'stream=width,height,r_frame_rate,bit_rate', 
           '-of', 'csv=p=0', input_file]
    output = subprocess.check_output(cmd).decode('utf-8').strip().split(',')
    return {
        'width': int(output[0]),
        'height': int(output[1]),
        'fps': eval(output[2]),
        'bitrate': int(output[3]) if output[3] != 'N/A' else None
    }

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
    
    print("Executing command: " + " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error executing FFmpeg command: {result.stderr}")
        return False
    
    if os.path.getsize(output_file) == 0:
        print(f"Warning: Output file {output_file} is empty!")
        return False
    
    return True

def split_video_reencoding(input_file, output_dir, duration, fps, scale, output_type, include_audio):
    """
    従来の分割方法：
    動画全体の長さからセグメント数を算出し、各セグメントを個別に作成する。
    """
    video_info = get_video_info(input_file)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    total_duration = get_duration(input_file)
    if total_duration is None:
        print("Failed to get duration from input file.")
        return
    num_segments = math.ceil(total_duration / duration)
    
    print(f"Total {output_type.upper()} files to create: {num_segments}")
    
    for i in tqdm(range(num_segments), desc=f"Creating {output_type.upper()} files"):
        start = i * duration
        end = min((i + 1) * duration, total_duration)
        output_file = os.path.join(output_dir, f"output_{i+1}.{output_type}")
        if not create_output(input_file, start, end, output_file, fps, scale, output_type, video_info, include_audio):
            print(f"Failed to create segment {i+1}")
            continue

# ---------------
# 【高速モード】ストリームコピー＋中間ファイル方式（mp4・再エンコード不要な場合）
# ---------------

def extract_segment(input_file, segment_duration, output_segment, include_audio):
    """
    入力ファイルの先頭 segment_duration 秒をストリームコピーで抽出する。
    """
    cmd = [
        'ffmpeg', '-y', '-i', input_file,
        '-t', str(segment_duration),
        '-c:v', 'copy'
    ]
    if include_audio:
        cmd.extend(['-c:a', 'copy'])
    else:
        cmd.append('-an')
    cmd.append(output_segment)
    
    print("Executing command: " + " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error extracting segment: {result.stderr}")
        return False
    if not os.path.exists(output_segment) or os.path.getsize(output_segment) == 0:
        print("Warning: extracted segment file is empty!")
        return False
    return True

def extract_remainder(input_file, segment_duration, output_remainder, include_audio):
    """
    入力ファイルの先頭 segment_duration 秒をスキップし、残り部分をストリームコピーで出力する。
    """
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(segment_duration),
        '-i', input_file,
        '-c:v', 'copy'
    ]
    if include_audio:
        cmd.extend(['-c:a', 'copy'])
    else:
        cmd.append('-an')
    cmd.append(output_remainder)
    
    print("Executing command: " + " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error extracting remainder: {result.stderr}")
        return False
    return True

def fast_split_video(input_file, output_dir, segment_duration, include_audio):
    """
    中間ファイルを利用して、常に短い残り部分だけを処理対象とすることで高速分割を実現する。
    この実装では、作業用ファイル名として常に "current.mp4"（および一時ファイル "temp.mp4"）を利用し、
    不要な中間ファイルが残らないように管理します。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    total_duration = get_duration(input_file)
    if total_duration is None:
        print("Failed to get duration from input file.")
        return
    
    estimated_segments = math.ceil(total_duration / segment_duration)
    pbar = tqdm(total=estimated_segments, desc="Extracting segments (fast mode)")
    
    segment_index = 1
    # 最初は元ファイルをそのまま利用
    current_input = input_file
    # 作業用の中間ファイル名
    working_file = os.path.join(output_dir, "current.mp4")
    temp_file = os.path.join(output_dir, "temp.mp4")
    
    while True:
        current_duration = get_duration(current_input)
        if current_duration is None:
            break
        
        # 残り時間が segment_duration 以下なら、最後のセグメントとして単純コピー
        if current_duration <= segment_duration:
            output_segment = os.path.join(output_dir, f"segment_{segment_index}.mp4")
            cmd = ['ffmpeg', '-y', '-i', current_input, '-c', 'copy']
            if not include_audio:
                cmd.append('-an')
            cmd.append(output_segment)
            print("Executing command: " + " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error extracting final segment: {result.stderr}")
            pbar.update(1)
            # クリーンアップ：作業用ファイルが存在するなら削除
            if os.path.exists(working_file):
                os.remove(working_file)
            break
        
        # 先頭 segment_duration 秒を抽出してセグメント出力
        output_segment = os.path.join(output_dir, f"segment_{segment_index}.mp4")
        if not extract_segment(current_input, segment_duration, output_segment, include_audio):
            print(f"Failed to extract segment {segment_index}")
            break
        pbar.update(1)
        
        # 残り部分を一時ファイル（temp.mp4）に抽出
        if not extract_remainder(current_input, segment_duration, temp_file, include_audio):
            print(f"Failed to extract remainder after segment {segment_index}")
            break
        
        # もし current_input が元ファイルでない場合は、古い中間ファイルを削除
        if current_input != input_file and os.path.exists(current_input):
            os.remove(current_input)
        # temp_file を "current.mp4" としてリネームし、次ループの入力とする
        os.rename(temp_file, working_file)
        current_input = working_file
        
        segment_index += 1
    
    pbar.close()

# ---------------
# メイン処理
# ---------------

def main():
    parser = argparse.ArgumentParser(
        description='動画を分割する。出力タイプや再エンコードオプションに応じて高速モードまたは従来モードを自動選択します。'
    )
    parser.add_argument('input_file', help='入力動画ファイルのパス')
    parser.add_argument('output_dir', help='出力ディレクトリ')
    parser.add_argument('--type', choices=['gif', 'mp4'], default='gif', help='出力ファイルタイプ (default: gif)')
    parser.add_argument('--duration', type=float, default=15.0, help='各セグメントの長さ（秒、default:15.0秒）')
    parser.add_argument('--fps', type=int, help='フレームレート（指定しない場合は入力と同じ）')
    parser.add_argument('--scale', type=int, help='出力幅（ピクセル、指定しない場合は入力と同じ）')
    parser.add_argument('--no-audio', action='store_true', help='MP4出力時に音声を除去（GIFの場合は無視）')
    
    args = parser.parse_args()
    
    # 入力ファイルの拡張子チェック
    input_extension = get_file_extension(args.input_file)
    if input_extension not in ['.mp4', '.mov']:
        print(f"Warning: 入力ファイル形式 '{input_extension}' はサポート外の可能性があります。")
    
    # MP4の場合、--no-audio の指定があると音声除去。それ以外（GIF）は音声は不要
    include_audio = (not args.no_audio) if args.type == 'mp4' else False
    
    # 出力タイプが mp4 で、かつ再エンコードパラメータがない場合は高速モード（ストリームコピー＋中間ファイル方式）を利用
    if args.type == 'mp4' and args.fps is None and args.scale is None:
        print("Using fast splitting mode (stream copy, intermediate file approach).")
        fast_split_video(args.input_file, args.output_dir, args.duration, include_audio)
    else:
        print("Using re-encoding splitting mode.")
        split_video_reencoding(args.input_file, args.output_dir, args.duration, args.fps, args.scale, args.type, include_audio)

if __name__ == '__main__':
    main()
