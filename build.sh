#!/bin/bash
# End to end build: frames (parallel) -> audio mix -> loudness master -> mux -> QC.
# usage: ./build.sh episodes/e001 [output.mp4]
set -euo pipefail
cd "$(dirname "$0")"
EP=${1:?episode folder}; B=$EP/beats.json; OUT=${2:-$EP/final.mp4}
FR=$(python3 -m fpm.render "$B" info | head -1 | awk '{print $4}')
J=$(nproc); STEP=$(( (FR + J - 1) / J ))
echo "== rendering $FR frames on $J cores"
rm -f "$EP"/seg_*.mp4
for ((i=0; i<J; i++)); do
  A=$((i*STEP)); Z=$(( (i+1)*STEP < FR ? (i+1)*STEP : FR ))
  python3 -m fpm.render "$B" seg $A $Z | ffmpeg -hide_banner -loglevel error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - \
    -c:v libx264 -preset veryfast -crf 17 -pix_fmt yuv420p -g 30 "$EP/seg_$i.mp4" &
done
wait
( for ((i=0; i<J; i++)); do echo "file seg_$i.mp4"; done ) > "$EP/segs.txt"
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$EP/segs.txt" -c copy "$EP/video.mp4"
echo "== audio"
python3 -m fpm.audio "$B"
echo "== master (-14 LUFS, -1.5 dBTP) and mux"
M=$(ffmpeg -hide_banner -i "$EP/mix_raw.wav" -af loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p' |
  python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
ffmpeg -hide_banner -loglevel error -y -i "$EP/video.mp4" -i "$EP/mix_raw.wav" \
  -af "loudnorm=I=-14:TP=-1.5:LRA=9:$M:linear=true,aresample=48000" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 \
  -movflags +faststart -shortest "$OUT"
rm -f "$EP"/seg_*.mp4 "$EP/segs.txt"
echo "== QC"
ffmpeg -hide_banner -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" || true
FZ=$(ffmpeg -hide_banner -i "$OUT" -vf "freezedetect=n=0.003:d=0.8" -map 0:v -f null - 2>&1 | grep -oE "freeze_duration: [0-9.]+" | awk '{s+=$2} END {printf "%.1f", s+0}')
echo "frozen time (>0.8s holds): ${FZ}s  (target < 2s)"
ffmpeg -hide_banner -loglevel error -y -i "$OUT" -vf "fps=2,scale=180:320,tile=10x10" -frames:v 1 "$EP/qc_sheet.png"
echo "done -> $OUT  (contact sheet: $EP/qc_sheet.png)"
