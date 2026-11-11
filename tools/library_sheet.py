"""Render one hero frame per template into a labeled catalog: python tools/library_sheet.py library.png"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PIL import Image, ImageDraw
from fpm.timeline import Timeline
from fpm.engine import F, W, H

DEMO = [
    ('phone_tap', dict(tap=.5, block=.9, underline=1.4, level=1, exit='fade'), 2.4, 'Phone, tap, alert pops (level 1/2)'),
    ('notif_chat', dict(banner=.2, expand=.9, bubbles=[1.1, 1.5, 1.9]), 2.6, 'Banner grows into chat, bubbles'),
    ('task_carousel', dict(stars=.4, button=.9, boost=1.3, swipes=[]), 2.0, 'Task cards: stars, boost tap, swipes'),
    ('counter_climb', dict(keys=[[.3, 0], [2.0, 100]], more=2.4), 2.6, 'Odometer balance, growth line, checks'),
    ('trust_payment', dict(notif=.2, small=1.0, meter_in=1.2, meter=1.5), 2.6, 'Payment notification and meter'),
    ('coin_request', dict(), 2.0, 'Card morphs into a spinning coin'),
    ('wallet_send', dict(done=1.2, expect=1.6), 2.6, 'Wallet: processing, submitted, promise'),
    ('stamp_reveal', dict(stamp=1.2, word='FAKE'), 2.4, 'Balance card, stamp slam, glitch'),
    ('money_flow', dict(send=1.4), 2.4, 'Two wallets, coin travels'),
    ('source_card', dict(highlight=1.2), 2.4, 'Official source, highlighter'),
    ('block_modal', dict(level=3, magnifier=.5, stop=1.6), 2.3, 'Callback alert, STOP stamp, cracks'),
    ('kinetic_line', dict(), 2.6, 'Word by word kinetic line'),
    ('logo_outro', dict(tag=1.4), 2.6, 'Logo, wordmark, tagline, loop out'),
]

def main(out):
    tw, th = 300, int(300 * H / W); cols = 5; lab = 70
    rows = (len(DEMO) + cols - 1) // cols
    S = Image.new('RGB', (cols * tw, rows * (th + lab)), (14, 18, 30)); d = ImageDraw.Draw(S)
    tmp = tempfile.mkdtemp()
    for i, (name, p, ht, desc) in enumerate(DEMO):
        beats = dict(duration=4.0, caps_inline=[], scenes=[dict(t=name, start=0, p=p)])
        path = os.path.join(tmp, f'{name}.json'); json.dump(beats, open(path, 'w'))
        fr = Timeline(path).frame(ht).resize((tw, th), Image.BILINEAR)
        x, y = (i % cols) * tw, (i // cols) * (th + lab)
        S.paste(fr, (x, y))
        d.text((x + 12, y + th + 10), name, font=F('Bold', 24), fill=(245, 166, 35))
        d.text((x + 12, y + th + 40), desc, font=F('Medium', 16), fill=(200, 206, 220))
    S.save(out); print('wrote', out)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'library.png')
