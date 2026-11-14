import math, random
from collections import OrderedDict
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 30
SS = 2
CX, CY = 540, 820
FD = '/usr/share/fonts/opentype/inter/'

INK = (15, 23, 42); MUTED = (104, 112, 130); ORANGE = (245, 166, 35)
RED = (232, 68, 74); GREEN = (46, 190, 110); CARD = (247, 243, 236)
DARKCARD = (25, 38, 68); WHITE = (255, 255, 255); NAVY = (12, 20, 40)
GOLD = (240, 168, 40)

# ---------------- audience profile ----------------
# Chosen per episode with "profile" in beats.json. "calm" is for older viewers:
# gentler camera, no glitch or motion blur, softer flashes, bigger captions,
# and a mix with less music, fewer high frequency SFX and more voice.
PROFILES = {
    'standard': dict(drift=1.0, punch=1.0, shake=1.0, blur=1.0, flash=1.0, glitch=True, cap_size=52,
                     sfx_gain=0.5, music_gain=0.42, duck=0.55, sfx_lowpass=None, sfx_skip=()),
    'calm': dict(drift=0.5, punch=0.4, shake=0.15, blur=0.0, flash=0.3, glitch=False, cap_size=66,
                 sfx_gain=0.3, music_gain=0.22, duck=0.7, sfx_lowpass=4500, sfx_skip=('tick', 'shimmer', 'glitch', 'marker')),
}
PROFILE = dict(PROFILES['standard'], name='standard')
def set_profile(name):
    if name not in PROFILES: raise ValueError(f'unknown profile {name}; use one of {list(PROFILES)}')
    PROFILE.clear(); PROFILE.update(PROFILES[name]); PROFILE['name'] = name

# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def P(t, t0, d): return clamp((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)
def lerp(a, b, x): return a + (b - a) * x
def lerpc(c1, c2, x): return tuple(int(round(lerp(a, b, x))) for a, b in zip(c1, c2))
def eo3(x): return 1 - (1 - x) ** 3
def ei3(x): return x ** 3
def eio(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eoexpo(x): return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)
def eoback(x, s=1.9):
    x -= 1
    return 1 + x * x * ((s + 1) * x + s)
def spring(dt, f=1.9, z=6.5):
    if dt <= 0: return 0.0
    return 1 - math.exp(-z * dt) * math.cos(2 * math.pi * f * dt)

# ---------------- fonts / cache ----------------
_F = {}
def F(w, size, disp=False):
    k = (w, int(round(size)), disp)
    if k not in _F:
        _F[k] = ImageFont.truetype(FD + ('InterDisplay-' if disp else 'Inter-') + w + '.otf', k[1])
    return _F[k]

_C = OrderedDict()
def cache(key, fn, maxn=70):
    if key in _C:
        _C.move_to_end(key); return _C[key]
    v = fn(); _C[key] = v
    if len(_C) > maxn: _C.popitem(last=False)
    return v

def canvas(w, h): return Image.new('RGBA', (max(1, int(round(w * SS))), max(1, int(round(h * SS)))), (0, 0, 0, 0))

class Pen:
    def __init__(s, img):
        s.img = img; s.d = ImageDraw.Draw(img)
    def _b(s, x0, y0, x1, y1): return [x0 * SS, y0 * SS, x1 * SS, y1 * SS]
    def rr(s, x0, y0, x1, y1, r, fill=None, outline=None, width=0):
        if x1 - x0 < 1 or y1 - y0 < 1: return
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        s.d.rounded_rectangle(s._b(x0, y0, x1, y1), r * SS, fill=fill, outline=outline, width=int(width * SS))
    def el(s, x0, y0, x1, y1, fill=None, outline=None, width=0):
        s.d.ellipse(s._b(x0, y0, x1, y1), fill=fill, outline=outline, width=int(width * SS))
    def circ(s, x, y, r, **k): s.el(x - r, y - r, x + r, y + r, **k)
    def line(s, pts, fill, width, joint='curve'):
        s.d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=max(1, int(width * SS)), joint=joint)
        r = width * SS / 2
        for x, y in (pts[0], pts[-1]):
            s.d.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], fill=fill)
    def poly(s, pts, fill): s.d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)
    def arc(s, box, a0, a1, fill, width): s.d.arc(s._b(*box), a0, a1, fill=fill, width=int(width * SS))
    def font(s, fa): return F(fa[0], fa[1] * SS, fa[2] if len(fa) > 2 else False)
    def tw(s, t, fa, sp=0, feat=None):
        f = s.font(fa)
        if sp: return sum(f.getlength(c) for c in t) / SS + sp * (len(t) - 1)
        return f.getlength(t, features=feat) / SS
    def text(s, x, y, t, fa, fill, anchor='la', sp=0, feat=None):
        f = s.font(fa)
        if not sp:
            s.d.text((x * SS, y * SS), t, font=f, fill=fill, anchor=anchor, features=feat); return
        tw = s.tw(t, fa, sp)
        h = anchor[0]
        x0 = x - (tw / 2 if h == 'm' else tw if h == 'r' else 0)
        va = 'l' + anchor[1]
        for c in t:
            s.d.text((x0 * SS, y * SS), c, font=f, fill=fill, anchor=va)
            x0 += f.getlength(c) / SS + sp
    def check(s, x, y, k, fill, width):
        s.line([(x - 9 * k, y), (x - 2.5 * k, y + 7 * k), (x + 10 * k, y - 7 * k)], fill, width, joint='curve')

# ---------------- camera ----------------
class Cam:
    punch = []; shake = []; extra = None
    s = 1.0; ox = 0.0; oy = 0.0
    def set(c, t):
        dr = PROFILE['drift']
        sc = 1.025 + 0.018 * dr * math.sin(2 * math.pi * t / 7.3)
        ox = 9 * dr * math.sin(2 * math.pi * t / 9.1)
        oy = 7 * dr * math.sin(2 * math.pi * t / 6.7 + 1)
        for t0, amt in c.punch:
            if t >= t0:
                p = t - t0
                sc += amt * PROFILE['punch'] * eoexpo(clamp(p / 0.1)) * math.exp(-max(0.0, p - 0.1) * 2.0)
        for t0, amp, dur in c.shake:
            if t0 <= t < t0 + dur:
                k = (1 - (t - t0) / dur) ** 2 * PROFILE['shake']
                ox += amp * k * math.sin(2 * math.pi * 23 * (t - t0))
                oy += amp * k * math.cos(2 * math.pi * 19 * (t - t0) + .5)
        if c.extra: sc, ox, oy = c.extra(t, sc, ox, oy)
        c.s, c.ox, c.oy = sc, ox, oy
    def map(c, x, y, k):
        return CX + (x - CX) * c.s + c.ox, CY + (y - CY) * c.s + c.oy, k * c.s
CAM = Cam()

# ---------------- compositing ----------------
def paste(base, im, cx, cy):
    x = int(round(cx - im.width / 2)); y = int(round(cy - im.height / 2))
    sx = max(0, -x); sy = max(0, -y)
    ex = min(im.width, W - x); ey = min(im.height, H - y)
    if ex <= sx or ey <= sy: return
    base.alpha_composite(im, (x + sx, y + sy), (sx, sy, ex, ey))

def fade(im, a):
    if a >= 0.997: return im
    im = im.copy()
    im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    return im

def put(base, spr, x, y, sc=1.0, a=1.0, rot=0.0, ss=SS, cam=True, sx=1.0):
    if a <= 0.004 or sc <= 0.01: return
    if cam: x, y, sc = CAM.map(x, y, sc)
    k = sc / ss
    w = max(1, int(round(spr.width * k * sx))); h = max(1, int(round(spr.height * k)))
    if w > 4000 or h > 5000: return
    im = spr if (w, h) == spr.size else spr.resize((w, h), Image.BILINEAR, reducing_gap=2.0)
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    paste(base, fade(im, a), x, y)

def shadow_spr(w, h, r, blur=34, alpha=95):
    q = 4
    key = ('sh', int(w) // 6, int(h) // 6, int(r), blur, alpha)
    def mk():
        pad = blur * 2
        im = Image.new('L', (int((w + 2 * pad) / q), int((h + 2 * pad) / q)), 0)
        ImageDraw.Draw(im).rounded_rectangle([pad / q, pad / q, (pad + w) / q, (pad + h) / q], r / q, fill=alpha)
        im = im.filter(ImageFilter.GaussianBlur(blur / q / 2))
        out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.putalpha(im)
        return out
    return cache(key, mk)

def bg_spr(w, h, r, fill, border=None):
    key = ('bg', int(w), int(h), int(r), fill, border)
    def mk():
        im = canvas(w, h); p = Pen(im)
        p.rr(0, 0, w, h, r, fill=fill)
        if border: p.rr(1, 1, w - 1, h - 1, r, outline=border, width=2)
        return im
    return cache(key, mk)

def draw_card(base, x, y, w, h, r=38, fill=CARD, contents=(), sc=1.0, a=1.0, border=None, shadow=True, rot=0.0):
    if a <= 0.004: return
    if shadow:
        sh = shadow_spr(w, h, r)
        put(base, sh, x, y + 22 * sc, sc, a, rot, ss=0.25)
    put(base, bg_spr(w, h, r, fill, border), x, y, sc, a, rot)
    top = y - h / 2 * sc
    for spr, ca in contents:
        if ca <= 0.004: continue
        hc = spr.height / SS
        put(base, spr, x, top + hc / 2 * sc, sc, a * ca, rot)

# ---------------- backgrounds ----------------
BGC = {'navy': ((9, 15, 32), (32, 54, 100)), 'cream': ((226, 217, 200), (252, 248, 240)),
       'green': ((5, 28, 22), (20, 98, 68)), 'purple': ((14, 10, 32), (62, 40, 112)),
       'amber': ((24, 13, 7), (118, 66, 18)), 'paper': ((230, 224, 212), (253, 250, 244)),
       'redwarn': ((14, 8, 18), (128, 22, 34))}
LIGHT = {'cream', 'paper'}
_BG = {}
def bg_full(name):
    if name not in _BG:
        b, g = BGC[name]
        lw, lh = 135, 240
        yy, xx = np.mgrid[0:lh, 0:lw]
        nx = (xx / lw - 0.5) * 1.0; ny = (yy / lh - 0.42) * 1.78
        d = np.sqrt(nx ** 2 + ny ** 2)
        gl = np.exp(-(d / 0.62) ** 2)[..., None]
        vig = (1 - 0.32 * np.clip(np.sqrt(((xx / lw - .5) * 1.0) ** 2 + ((yy / lh - .5) * 1.78) ** 2) / 0.9, 0, 1) ** 2)[..., None]
        arr = (np.array(b) + (np.array(g) - np.array(b)) * gl) * vig
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        # very light static grain for texture
        rng = np.random.default_rng(7)
        n = (rng.standard_normal((H, W, 1)) * 2.2)
        im = Image.fromarray(np.clip(np.asarray(im).astype(np.float32) + n, 0, 255).astype(np.uint8))
        _BG[name] = im
    return _BG[name]

def radial_mask(ox, oy, p):
    lw, lh = 135, 240
    yy, xx = np.mgrid[0:lh, 0:lw]
    d = np.sqrt((xx * 8 - ox) ** 2 + (yy * 8 - oy) ** 2)
    maxd = max(math.hypot(ox - a, oy - b) for a in (0, W) for b in (0, H)) + 160
    r = p * maxd
    m = np.clip((r - d) / 140 + 0.5, 0, 1)
    return Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
