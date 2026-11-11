"""CLI:
  python -m fpm.render BEATS still 0 3.5 12        -> still_<t>.png in the episode folder
  python -m fpm.render BEATS sheet out.png t1 t2 ... -> tiled contact sheet of stills
  python -m fpm.render BEATS seg A B               -> raw rgb24 frames A..B-1 to stdout
  python -m fpm.render BEATS info                  -> duration, frame count, scenes
"""
import sys, os
from .engine import W, H, FPS
from .timeline import Timeline
from PIL import Image


def sheet(tl, out, ts, cols=7, tw=270):
    th = int(tw * H / W)
    rows = (len(ts) + cols - 1) // cols
    S = Image.new('RGB', (cols * tw, rows * th))
    for i, t in enumerate(ts):
        S.paste(tl.frame(float(t)).resize((tw, th), Image.BILINEAR), ((i % cols) * tw, (i // cols) * th))
    S.save(out)


def main():
    beats, mode = sys.argv[1], sys.argv[2]
    tl = Timeline(beats)
    if mode == 'info':
        print(f'duration {tl.dur:.2f}s frames {int(tl.dur * FPS)}')
        for s in tl.scenes: print(f'{s.start:7.2f} {s.end:7.2f}  {s.name:14s} bg={s.bg}')
    elif mode == 'still':
        for t in sys.argv[3:]: tl.frame(float(t)).save(os.path.join(tl.dir, f'still_{t}.png'))
    elif mode == 'sheet':
        sheet(tl, sys.argv[3], sys.argv[4:])
    elif mode == 'seg':
        a, b = int(sys.argv[3]), int(sys.argv[4]); out = sys.stdout.buffer
        for i in range(a, b): out.write(tl.frame(i / FPS).tobytes())


if __name__ == '__main__':
    main()
