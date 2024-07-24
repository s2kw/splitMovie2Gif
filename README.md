


# 使い方
venvで動作させると良いです。

コマンドラインで下記を入力して動作させます。インプットとアウトプットの指定は必須です。
```bash
python main.py
``` 


```
'input_file', help='Path to the input video file'
'output_dir', help='Path to the output directory'
'--type', choices=['gif', 'mp4'], default='gif', help='Output file type (default: gif)'
'--duration', type=int, default=15, help='Duration of each segment in seconds (default: 15)'
'--fps', type=int, help='Frames per second (default: same as input)'
'--scale', type=int, help='Output width in pixels (default: same as input)'
'--no-audio', action='store_true', help='Remove audio from MP4 output (ignored for GIF)'
```

gifは超時間がかかるがmp4は早い。


# main.py
動画ファイルをぶつ切りにします。

```
python main.py input_video.mp4 output_directory --type gif --duration 15 --fps 10 --scale 640
python main.py input_video.mp4 output_directory --type mp4 --duration 1 --fps 20 --scale 640
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


---
# combine_videos.py
複数のファイルを1つの動画にするスクリプトです。

このスクリプトは、入力ファイルがMP4形式であることを前提としています。他の形式の場合、追加の処理が必要になる可能性があります。
フェード効果の開始時間は、A動画の長さから自動的に計算されます。
出力ファイルの品質設定（-crf 23など）は、必要に応じて調整できます。



```python
python combine_videos.py A1.mp4 A2.mp4 A3.mp4 B.mp4 output_directory --fade 2.0
```


---
# create_video_from_image_and_audio.py
画像ファイルと音源ファイルから動画を出力するスクリプトです

画像ファイルと音声ファイル(WAV)を入力として受け取ります。
出力動画の幅または高さ（またはその両方）を指定できます。指定がない場合は元の画像サイズを使用します。
動画の長さは音声ファイルの長さに自動的に合わせられます。
FFmpegを使用して動画を生成します。
出力動画はH.264でエンコードされ、音声はAACでエンコードされます。
アスペクト比を保持し、必要に応じて黒いパディングを追加します。


```python
python create_video_from_image_and_audio.py image.jpg audio.wav output.mp4 --width 1280 --height 720
```



