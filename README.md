


# 使い方
Split video into GIF or MP4 segments

'input_file', help='Path to the input video file'
'output_dir', help='Path to the output directory'
'--type', choices=['gif', 'mp4'], default='gif', help='Output file type (default: gif)'
'--duration', type=int, default=15, help='Duration of each segment in seconds (default: 15)'
'--fps', type=int, help='Frames per second (default: same as input)'
'--scale', type=int, help='Output width in pixels (default: same as input)'
'--no-audio', action='store_true', help='Remove audio from MP4 output (ignored for GIF)'

gifは超時間がかかるがmp4は早い。


# command
```
python main.py input_video.mp4 output_directory --type gif --duration 15 --fps 10 --scale 640
```

## sample 1
originFile/20240705.mp4を加工します。
mp4形式で出力します。
15秒単位で切ります。
10fpsに短縮します。
640サイズにスケールします。省略するとオリジナルと同じ画面サイズになります。

```
python main.py originFile/20240705.mp4 out --type mp4 --duration 15 --fps 10 --scale 640
```

## sample 2
input_video.mp4 を加工します。
out_directory/ 下の出力します。
mp4形式で出力します。
15秒単位(default)で分割します。
fpsはオリジナルを踏襲。
画像サイズは縦横はオリジナルを踏襲。

```
python main.py input_video.mp4 output_directory --type mp4
```

## sample 3
input_video.mp4 を加工します。
out_directory/ 下の出力します。
mp4形式で出力します。
15秒単位(default)で分割します。
fpsはオリジナルを踏襲。
画像サイズは縦横はオリジナルを踏襲。
--no-audioで音声無しオプションを付与し出力動画から音声を抜きます。

```
python main.py input_video.mp4 output_directory --type mp4 --no-audio
```



