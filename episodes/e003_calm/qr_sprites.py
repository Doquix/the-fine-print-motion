import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from fpm.engine import *

LIGHTG = (226, 230, 236)
SCREEN_BG = (246, 247, 250)
SW, SH = 434, 904          # phone screen
PW, PH = 470, 940          # phone body
STW, STH = 360, 400        # top sticker
UNW, UNH = 340, 380        # underneath sticker
TNUM = ['tnum']

# ---------------------------------------------------------------- QR
def _qr_matrix(seed, n=25):
    rng = np.random.default_rng(seed)
    m = rng.random((n, n)) < 0.47
    def finder(r, c):
        m[r:r + 8, c:c + 8] = False
        m[r:r + 7, c:c + 7] = True
        m[r + 1:r + 6, c + 1:c + 6] = False
        m[r + 2:r + 5, c + 2:c + 5] = True
    finder(0, 0); finder(0, n - 7); finder(n - 7, 0)
    m[0:8, 7] = False; m[7, 0:8] = False
    m[0:8, n - 8] = False; m[7, n - 8:n] = False
    m[n - 8, 0:8] = False; m[n - 8:n, 7] = False
    m[n - 9:n - 4, n - 9:n - 4] = False
    m[n - 9:n - 4, n - 9] = True; m[n - 9:n - 4, n - 5] = True
    m[n - 9, n - 9:n - 4] = True; m[n - 5, n - 9:n - 4] = True
    m[n - 7, n - 7] = True
    return m

def draw_qr(p, x, y, size, seed, fg=INK):
    m = _qr_matrix(seed); n = m.shape[0]; c = size / n
    for r in range(n):
        for k in range(n):
            if m[r, k]:
                p.rr(x + k * c, y + r * c, x + (k + 1) * c + 0.6, y + (r + 1) * c + 0.6, c * 0.18, fill=fg)

# ---------------------------------------------------------------- meter
def meter_body():
    def mk():
        w, h = 520, 1000
        im = canvas(w, h); p = Pen(im)
        p.rr(150, 860, 370, 1000, 10, fill=(38, 44, 58))                  # post
        p.rr(0, 0, w, 900, 64, fill=(44, 52, 70))
        p.rr(10, 10, w - 10, 890, 56, fill=(58, 68, 90))
        p.rr(10, 10, w - 10, 70, 30, fill=(70, 82, 106))
        # display
        p.rr(60, 90, w - 60, 270, 26, fill=(20, 26, 36))
        p.rr(76, 106, w - 76, 254, 18, fill=(28, 52, 46))
        p.text(w / 2, 150, 'ZONE 4', ('Bold', 40, True), (130, 240, 190), anchor='mm', sp=4)
        p.text(w / 2, 212, 'PAY HERE', ('SemiBold', 28), (100, 200, 160), anchor='mm', sp=6)
        # label plate where sticker sits (sticker center at local y 580)
        p.rr(70, 360, w - 70, 800, 22, fill=(36, 44, 60))
        # slots
        p.rr(90, 820, 230, 846, 12, fill=(20, 24, 32))
        p.rr(290, 820, 430, 846, 12, fill=(20, 24, 32))
        p.text(w / 2, 312, 'PAY BY PHONE  ·  CARD  ·  COIN', ('SemiBold', 20), (150, 160, 182), anchor='mm', sp=2)
        return im
    return cache('meter', mk)
METER_STICK_DY = 80   # sticker center offset from meter center (meter center = local 500)

# ---------------------------------------------------------------- stickers
def sticker_under():
    def mk():
        pad = 20
        im = canvas(UNW + 2 * pad, UNH + 2 * pad); p = Pen(im)
        p.rr(pad, pad, pad + UNW, pad + UNH, 18, fill=(236, 242, 250))
        p.rr(pad, pad, pad + UNW, pad + 70, 18, fill=(30, 74, 140))
        p.rr(pad, pad + 40, pad + UNW, pad + 70, 0, fill=(30, 74, 140))
        p.circ(pad + 44, pad + 35, 18, fill=WHITE)
        p.circ(pad + 44, pad + 35, 11, fill=(30, 74, 140))
        p.text(pad + 74, pad + 35, 'CITY PARKING', ('Bold', 24), WHITE, anchor='lm', sp=2)
        p.rr(pad + 60, pad + 92, pad + UNW - 60, pad + 312, 10, fill=WHITE)
        draw_qr(p, pad + 70, pad + 102, 200, 11, (20, 40, 80))
        p.text(pad + UNW / 2, pad + 344, 'Pay by phone · Zone 4', ('SemiBold', 22), (40, 60, 100), anchor='mm')
        return im
    return cache('under', mk)

def _clip_half(poly, f):
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        fa, fb = f(a), f(b)
        if fa <= 0: out.append(a)
        if (fa < 0) != (fb < 0) and fa != fb:
            t = fa / (fa - fb)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out

def sticker_top(d, outline=0.0, dashed=0.0):
    d = int(round(d / 5) * 5); outline = round(outline, 1); dashed = round(dashed, 1)
    def mk():
        pad = 40; w, h = STW, STH
        im = canvas(w + 2 * pad, h + 2 * pad); p = Pen(im)
        rect = [(0, 0), (w, 0), (w, h), (0, h)]
        f = lambda q: (w - q[0]) + q[1] - d          # <0 means peeled region
        keep = _clip_half(rect, lambda q: -f(q))
        gone = _clip_half(rect, f) if d > 0 else []
        # sticker face on its own layer, masked to the kept polygon
        face = canvas(w, h); fp = Pen(face)
        fp.rr(0, 0, w, h, 18, fill=WHITE)
        fp.rr(0, h - 84, w, h, 18, fill=ORANGE)
        fp.rr(0, h - 84, w, h - 60, 0, fill=ORANGE)
        fp.text(w / 2, h - 42, 'SCAN TO PAY', ('Black', 36, True), WHITE, anchor='mm', sp=3)
        fp.text(w / 2, 34, 'FAST PARKING', ('Bold', 22), INK, anchor='mm', sp=4)
        draw_qr(fp, 60, 60, 240, 3, INK)
        if d > 0:
            mask = Image.new('L', face.size, 0)
            ImageDraw.Draw(mask).polygon([(x * SS, y * SS) for x, y in keep], fill=255)
            mask = ImageChops.multiply(mask, face.getchannel('A'))
            face.putalpha(mask)
        # shadow under whole sticker (thin) and under flap
        sh = Image.new('L', im.size, 0); sd = ImageDraw.Draw(sh)
        sd.polygon([((x + pad + 3) * SS, (y + pad + 6) * SS) for x, y in keep], fill=110)
        if len(gone) >= 3:
            flap = [(q[0] + f(q), q[1] - f(q)) for q in gone]
            sd.polygon([((x + pad + 14) * SS, (y + pad + 16) * SS) for x, y in flap], fill=120)
        sh = sh.filter(ImageFilter.GaussianBlur(9 * SS))
        shim = Image.new('RGBA', im.size, (0, 0, 0, 0)); shim.putalpha(sh)
        im.alpha_composite(shim)
        im.alpha_composite(face, (pad * SS, pad * SS))
        if len(gone) >= 3:
            flap = [(q[0] + f(q), q[1] - f(q)) for q in gone]
            pts = [(x + pad, y + pad) for x, y in flap]
            p.poly(pts, (214, 214, 206))
            # gloss band along the fold
            fx0, fy0 = w - d + pad, pad
            p.line([(max(pad, fx0), pad + max(0, d - w)), (w + pad, pad + min(d, h))], (250, 250, 246), 5)
        if outline > 0:
            col = RED + (int(255 * outline),)
            p.d.line([((x + pad) * SS, (y + pad) * SS) for x, y in keep + keep[:1]], fill=col, width=int(8 * SS), joint='curve')
        if dashed > 0:
            col = ORANGE + (int(255 * dashed),)
            per = keep + keep[:1]
            for i in range(len(per) - 1):
                (x0, y0), (x1, y1) = per[i], per[i + 1]
                L = math.hypot(x1 - x0, y1 - y0); nseg = max(1, int(L / 26))
                for k in range(nseg):
                    a0 = k / nseg; a1 = (k + 0.55) / nseg
                    p.line([(pad + x0 + (x1 - x0) * a0, pad + y0 + (y1 - y0) * a0),
                            (pad + x0 + (x1 - x0) * a1, pad + y0 + (y1 - y0) * a1)], col, 7)
        return im
    return cache(('stk', d, outline, dashed), mk, maxn=90)

# ---------------------------------------------------------------- viewfinder
def brackets(size, col):
    size = int(round(size / 4) * 4)
    def mk():
        s = size; L = s * 0.2; im = canvas(s + 20, s + 20); p = Pen(im)
        o = 10
        for (x, y, dx, dy) in [(o, o, 1, 1), (o + s, o, -1, 1), (o, o + s, 1, -1), (o + s, o + s, -1, -1)]:
            p.line([(x, y + dy * L), (x, y), (x + dx * L, y)], col, 10, joint=None)
        return im
    return cache(('brk', size, col), mk)

def scanline(w):
    def mk():
        im = canvas(w, 40); p = Pen(im)
        for i in range(10):
            p.rr(0, 20 - i * 2, w, 20 + i * 2, 4, fill=ORANGE + (int(26 - i * 2.5),))
        p.rr(0, 18, w, 22, 2, fill=ORANGE + (255,))
        return im
    return cache(('scan', w), mk)

def link_pill(text, mode='neutral', hl=0.0):
    hl = round(hl, 2)
    def mk():
        fa = ('SemiBold', 30); w = 150 + Pen(canvas(1, 1)).tw(text, fa); h = 92
        im = canvas(w, h); p = Pen(im)
        p.rr(0, 0, w, h, 46, fill=(255, 255, 255, 245))
        # link icon
        ic = GREEN if mode == 'ok' else (RED if mode == 'bad' else (60, 120, 230))
        p.circ(52, h / 2, 26, fill=ic)
        p.arc((38, h / 2 - 14, 58, h / 2 + 2), 180, 360, WHITE, 4)
        p.line([(42, h / 2 - 6), (42, h / 2 + 8)], WHITE, 4); p.line([(54, h / 2 - 6), (54, h / 2 + 8)], WHITE, 4)
        p.text(92, h / 2 - 16, 'Open link', ('Medium', 20), MUTED, anchor='lm')
        tw = p.tw(text, fa)
        if hl > 0:
            p.rr(88, h / 2 + 2, 88 + (tw + 10) * hl, h / 2 + 34, 8, fill=lerpc(WHITE, ORANGE, 0.5))
        p.text(92, h / 2 + 18, text, fa, INK, anchor='lm')
        return im
    return cache(('pill', text, mode, hl), mk)

# ---------------------------------------------------------------- phone
def phone_frame(dim=0.0):
    dim = round(dim, 1)
    def mk():
        im = canvas(PW + 12, PH); p = Pen(im)
        p.rr(0, 160, 10, 230, 4, fill=(30, 34, 46)); p.rr(PW + 2, 200, PW + 12, 300, 4, fill=(30, 34, 46))
        p.rr(6, 0, PW + 6, PH, 66, fill=(16, 20, 30))
        p.rr(10, 4, PW + 2, PH - 4, 62, outline=(132, 142, 164), width=4)
        return im
    return cache(('pf', dim), mk)

def island():
    def mk():
        im = canvas(130, 38); Pen(im).rr(0, 0, 130, 38, 19, fill=(8, 10, 14)); return im
    return cache('isl', mk)

def screen_mask():
    def mk():
        m = Image.new('L', (SW * SS, SH * SS), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, SW * SS - 1, SH * SS - 1], 48 * SS, fill=255)
        return m
    return cache('smask', mk)

def _status(p, dark=False):
    c = INK if not dark else WHITE
    p.text(46, 34, '9:41', ('SemiBold', 24), c, anchor='lm')
    p.rr(SW - 92, 26, SW - 52, 42, 5, outline=c, width=2); p.rr(SW - 89, 29, SW - 62, 39, 3, fill=c)
    for i in range(4): p.rr(SW - 140 + i * 9, 40 - i * 4 - 4, SW - 134 + i * 9, 42, 1, fill=c)

def _finish(im):
    im.putalpha(ImageChops.multiply(im.getchannel('A'), screen_mask()))
    return im

CARDNUM = '4821773019560042'
def pay_screen(reveal=1.0, field=0.0, n=0, url_red=0.0, cursor=True, xbtn=0.0):
    reveal = round(reveal, 1); field = round(field, 1); url_red = round(url_red, 1); xbtn = round(xbtn, 1)
    def mk():
        im = canvas(SW, SH); p = Pen(im)
        p.rr(0, 0, SW, SH, 0, fill=SCREEN_BG)
        _status(p)
        base = im; im = canvas(SW, SH); p = Pen(im)
        ub = lerpc((234, 236, 241), (253, 226, 226), url_red)
        p.rr(18, 66, SW - 18, 122, 18, fill=ub)
        uc = lerpc(MUTED, RED, url_red)
        p.rr(40, 86, 54, 102, 3, fill=uc); p.arc((42, 76, 52, 94), 180, 360, uc, 3)
        p.text(66, 94, 'citypark-pay.co/zone4', ('Medium' if url_red < .5 else 'Bold', 24), uc, anchor='lm')
        if xbtn > 0:
            r = 22 * xbtn
            p.circ(SW - 52, 94, r, fill=INK)
            k = 8 * xbtn
            p.line([(SW - 52 - k, 94 - k), (SW - 52 + k, 94 + k)], WHITE, 4)
            p.line([(SW - 52 + k, 94 - k), (SW - 52 - k, 94 + k)], WHITE, 4)
        a = lambda i: int(255 * clamp(reveal * 5 - i))
        if reveal > 0:
            A = a(0)
            p.rr(30, 160, 82, 212, 14, fill=NAVY + (A,))
            p.text(56, 186, 'P', ('Black', 32, True), WHITE + (A,), anchor='mm')
            p.text(98, 186, 'Parking Payment', ('Bold', 32), INK + (A,), anchor='lm')
            A = a(1)
            p.rr(24, 240, SW - 24, 410, 26, fill=WHITE + (A,))
            p.text(52, 286, 'Zone 4 · Space 112', ('Medium', 24), MUTED + (A,), anchor='lm')
            p.text(52, 352, '2 hours', ('Bold', 44), INK + (A,), anchor='lm')
            p.text(SW - 52, 352, '$6.00', ('Bold', 44), INK + (A,), anchor='rm', feat=TNUM)
            A = a(2)
            p.text(30, 462, 'Card number', ('Bold', 26), INK + (A,), anchor='lm')
            bc = lerpc((206, 210, 220), ORANGE, field)
            if field > 0:
                p.rr(14, 482, SW - 14, 584, 24, fill=lerpc(SCREEN_BG, ORANGE, 0.3 * field) + (A,))
            p.rr(24, 492, SW - 24, 574, 18, fill=WHITE + (A,), outline=bc + (A,), width=2 + 2 * field)
            if n == 0:
                p.text(48, 533, '1234 5678 9012 3456', ('Medium', 30), (190, 194, 204, A), anchor='lm', feat=TNUM)
                cx = 46
            else:
                s = CARDNUM[:n]; s = ' '.join(s[i:i + 4] for i in range(0, len(s), 4))
                p.text(48, 533, s, ('SemiBold', 32), INK + (A,), anchor='lm', feat=TNUM)
                cx = 50 + p.tw(s, ('SemiBold', 32), feat=TNUM)
            if cursor and field > 0.5:
                p.rr(cx + 2, 512, cx + 5, 554, 1, fill=ORANGE)
            A = a(3)
            for x0, x1, t in ((24, 205, 'MM / YY'), (229, SW - 24, 'CVC')):
                p.rr(x0, 610, x1, 684, 18, fill=WHITE + (A,), outline=(206, 210, 220, A), width=2)
                p.text(x0 + 24, 647, t, ('Medium', 26), (190, 194, 204, A), anchor='lm')
            A = a(4)
            p.rr(24, 730, SW - 24, 814, 22, fill=ORANGE + (A,))
            p.text(SW / 2, 772, 'Pay $6.00', ('Bold', 32), WHITE + (A,), anchor='mm', feat=TNUM)
            p.text(SW / 2, 856, 'Secure checkout', ('Medium', 22), MUTED + (A,), anchor='mm')
        base.alpha_composite(im)
        return _finish(base)
    return cache(('pay', reveal, field, n, url_red, cursor, xbtn), mk)

def closed_screen(p_chk=1.0):
    p_chk = round(p_chk, 1)
    def mk():
        im = canvas(SW, SH); p = Pen(im)
        p.rr(0, 0, SW, SH, 0, fill=SCREEN_BG); _status(p)
        base = im; im = canvas(SW, SH); p = Pen(im)
        r = 70 * eoback(p_chk) if p_chk > 0 else 0
        if r > 1:
            p.circ(SW / 2, 400, r, fill=GREEN)
            p.check(SW / 2, 400, 3.2 * p_chk, WHITE, 12)
        p.text(SW / 2, 530, 'Page closed', ('Bold', 34), INK + (int(255 * p_chk),), anchor='mm')
        p.text(SW / 2, 578, 'Nothing was entered', ('Medium', 24), MUTED + (int(255 * p_chk),), anchor='mm')
        base.alpha_composite(im)
        return _finish(base)
    return cache(('closed', p_chk), mk)

QUERY = 'city parking payment'
def search_screen(nq=0, r1=0.0, r2=0.0, badge=0.0, row=0.0, tap=0.0):
    r1, r2, badge, row, tap = (round(v, 1) for v in (r1, r2, badge, row, tap))
    def mk():
        im = canvas(SW, SH); p = Pen(im)
        p.rr(0, 0, SW, SH, 0, fill=SCREEN_BG); _status(p)
        p.rr(18, 70, SW - 18, 134, 32, fill=WHITE, outline=(206, 210, 220), width=2)
        p.circ(56, 100, 11, outline=MUTED, width=3); p.line([(64, 108), (72, 116)], MUTED, 3)
        q = QUERY[:nq]
        if q:
            p.text(84, 102, q, ('Medium', 27), INK, anchor='lm')
            cx = 86 + p.tw(q, ('Medium', 27))
        else:
            p.text(84, 102, 'Search', ('Medium', 27), (180, 184, 194), anchor='lm'); cx = 84
        if nq < len(QUERY): p.rr(cx, 86, cx + 3, 118, 1, fill=(60, 120, 230))
        base = im; im = canvas(SW, SH); p = Pen(im)
        if r1 > 0:
            A = int(255 * r1); y = 170 + 30 * (1 - r1)
            p.rr(18, y, SW - 18, y + 250, 26, fill=WHITE + (A,), outline=(GREEN + (A,)) if tap > 0 else None, width=4 * tap)
            p.rr(40, y + 26, 128, y + 114, 22, fill=(30, 74, 140, A))
            p.circ(84, y + 70, 24, fill=WHITE + (A,)); p.circ(84, y + 70, 14, fill=(30, 74, 140, A))
            p.text(146, y + 52, 'City Parking', ('Bold', 30), INK + (A,), anchor='lm')
            p.text(146, y + 92, 'Parking payment app', ('Medium', 22), MUTED + (A,), anchor='lm')
            if badge > 0:
                bs = eoback(badge)
                bx, by = 40, y + 150
                p.rr(bx, by, bx + 196 * bs, by + 52, 26, fill=(222, 246, 232, A))
                if bs > .6:
                    p.text(bx + 58, by + 27, 'OFFICIAL', ('Bold', 22), (20, 130, 70, A), anchor='lm', sp=2)
                    # shield
                    p.poly([(bx + 22, by + 12), (bx + 42, by + 12), (bx + 42, by + 28), (bx + 32, by + 42), (bx + 22, by + 28)], (20, 150, 80, A))
                    p.check(bx + 32, by + 25, 0.7, WHITE, 3)
            if row > 0:
                p.rr(SW - 148, y + 152, SW - 40, y + 202, 25, fill=(60, 120, 230, int(A * row)))
                p.text(SW - 94, y + 177, 'Get', ('Bold', 24), WHITE + (int(A * row),), anchor='mm')
        if r2 > 0:
            A = int(255 * r2); y = 450 + 30 * (1 - r2)
            p.rr(18, y, SW - 18, y + 170, 26, fill=WHITE + (A,))
            p.rr(44, y + 46, 62, y + 66, 4, fill=(20, 130, 70, A)); p.arc((46, y + 32, 60, y + 54), 180, 360, (20, 130, 70, A), 3)
            p.text(78, y + 56, 'yourcity.gov/parking', ('Bold', 27), (20, 110, 60, A), anchor='lm')
            p.text(44, y + 106, 'Pay for parking · City website', ('Medium', 22), MUTED + (A,), anchor='lm')
        base.alpha_composite(im)
        return _finish(base)
    return cache(('srch', nq, r1, r2, badge, row, tap), mk)

# ---------------------------------------------------------------- cards
def scam_card(rows=0, hl=0.0):
    hl = round(hl, 1)
    def mk():
        w, h = 420, 470
        im = canvas(w, h); p = Pen(im)
        p.rr(0, 0, w, h, 34, fill=(18, 12, 22))
        p.rr(1, 1, w - 1, h - 1, 34, outline=(120, 30, 44), width=3)
        p.circ(40, 50, 9, fill=RED)
        p.text(60, 50, 'CAPTURED', ('Bold', 24), RED, anchor='lm', sp=3)
        p.text(w - 34, 50, 'just now', ('Medium', 20), (150, 140, 160), anchor='rm')
        p.line([(28, 86), (w - 28, 86)], (60, 40, 60), 2)
        data = [('Card', '4821 7730 1956 0042'), ('Exp', '08 / 29'), ('CVC', '417'), ('Billing ZIP', '60614')]
        for i, (k, v) in enumerate(data[:rows]):
            y = 130 + i * 84
            if hl > 0:
                p.rr(20, y - 30, w - 20, y + 34, 14, fill=lerpc((18, 12, 22), RED, 0.35 * hl))
            p.text(36, y - 8, k, ('Medium', 20), (160, 150, 170), anchor='lm')
            p.text(36, y + 18, v, ('Bold', 30), WHITE, anchor='lm', feat=TNUM)
        return im
    return cache(('scam', rows, hl), mk)

def chip(t, col=ORANGE):
    def mk():
        w = 40 + Pen(canvas(1, 1)).tw(t, ('Bold', 30), feat=TNUM)
        im = canvas(w, 58); p = Pen(im)
        p.rr(0, 0, w, 58, 18, fill=col); p.text(w / 2, 30, t, ('Bold', 30), INK, anchor='mm', feat=TNUM)
        return im
    return cache(('chip', t, col), mk)

def status_card(pulse=0.0, rows=1.0):
    pulse = round(pulse, 1); rows = round(rows, 1)
    def mk():
        w, h = 860, 430
        im = canvas(w, h); p = Pen(im)
        p.rr(0, 0, w, h, 40, fill=CARD)
        p.text(48, 62, 'PARKING STATUS', ('Bold', 24), MUTED, anchor='lm', sp=4)
        p.text(48, 122, 'Zone 4 · Space 112', ('Bold', 44), INK, anchor='lm')
        base = im; im = canvas(w, h); p = Pen(im)
        A = int(255 * clamp(rows * 2))
        p.rr(36, 180, w - 36, 290, 24, fill=WHITE + (A,))
        p.text(68, 222, 'Payment received', ('Medium', 26), MUTED + (A,), anchor='lm')
        p.text(68, 260, 'None', ('Bold', 32), RED + (A,), anchor='lm')
        p.text(w - 68, 222, 'Time left', ('Medium', 26), MUTED + (A,), anchor='rm')
        p.text(w - 68, 260, '0:00', ('Bold', 32), lerpc(INK, RED, pulse) + (A,), anchor='rm', feat=TNUM)
        A = int(255 * clamp(rows * 2 - 1))
        p.rr(36, 312, w - 36, 392, 24, fill=(253, 228, 228, A))
        p.text(68, 352, 'Card details sent to', ('Medium', 26), (150, 50, 56, A), anchor='lm')
        p.text(w - 68, 352, 'citypark-pay.co', ('Bold', 26), (200, 40, 50, A), anchor='rm')
        base.alpha_composite(im)
        return base
    return cache(('status', pulse, rows), mk)

# ---------------------------------------------------------------- stamps, fx
def stamp(text, size=120):
    def mk():
        f = F('Black', size * SS, True)
        tw = f.getlength(text) / SS
        w, h = tw + 110, size * 1.5
        im = canvas(w, h); p = Pen(im)
        p.rr(0, 0, w, h, 26, fill=RED)
        p.rr(14, 14, w - 14, h - 14, 16, outline=WHITE, width=6)
        p.text(w / 2, h / 2 + 4, text, ('Black', size, True), WHITE, anchor='mm', sp=4)
        rng = np.random.default_rng(len(text) * 7)
        n = rng.random((im.height // 6 + 1, im.width // 6 + 1))
        n = (np.clip((n - 0.18) * 6, 0, 1) * 255).astype(np.uint8)
        nm = Image.fromarray(n).resize(im.size, Image.NEAREST).filter(ImageFilter.GaussianBlur(2))
        im.putalpha(ImageChops.multiply(im.getchannel('A'), nm))
        return im
    return cache(('stamp', text, size), mk)

def ripple(p):
    p = round(p, 2)
    def mk():
        im = canvas(220, 220); pe = Pen(im)
        r = 20 + 80 * eo3(p); a = int(230 * (1 - p))
        pe.circ(110, 110, r, outline=WHITE + (a,), width=8 * (1 - p) + 2)
        if p < .5: pe.circ(110, 110, 26 * (1 - p * 2), fill=WHITE + (int(160 * (1 - p * 2)),))
        return im
    return cache(('rip', p), mk)

def magnifier():
    def mk():
        im = canvas(260, 260); p = Pen(im)
        p.line([(170, 170), (236, 236)], (20, 24, 34), 30)
        p.line([(176, 176), (232, 232)], ORANGE, 18)
        p.circ(110, 110, 88, fill=(255, 255, 255, 40))
        p.circ(110, 110, 88, outline=WHITE, width=14)
        p.circ(110, 110, 96, outline=(20, 24, 34, 120), width=4)
        p.arc((48, 48, 172, 172), 200, 250, WHITE + (180,), 8)
        return im
    return cache('mag', mk)

def ring(r, col, w=8):
    r = int(round(r / 3) * 3)
    def mk():
        im = canvas(2 * r + 20, 2 * r + 20); Pen(im).circ(r + 10, r + 10, r, outline=col, width=w); return im
    return cache(('ring', r, col, w), mk)

def tag(text, fill, fg=WHITE, size=26):
    def mk():
        fa = ('Bold', size); w = Pen(canvas(1, 1)).tw(text, fa, sp=3) + 44; h = size * 2
        im = canvas(w, h); p = Pen(im)
        p.rr(0, 0, w, h, h / 2, fill=fill); p.text(w / 2, h / 2 + 1, text, fa, fg, anchor='mm', sp=3)
        return im
    return cache(('tag', text, fill, fg, size), mk)

def word(t, size, col=WHITE):
    def mk():
        f = F('Black', size * SS, True); w = f.getlength(t) / SS + 20; h = size * 1.35
        im = canvas(w, h); Pen(im).text(w / 2, h / 2, t, ('Black', size, True), col, anchor='mm')
        return im
    return cache(('word', t, size, col), mk)

def word_w(t, size): return F('Black', size * SS, True).getlength(t) / SS

def logo_icon():
    def mk():
        im = canvas(260, 260); p = Pen(im)
        p.rr(30, 10, 190, 220, 24, fill=CARD)
        for i, w in enumerate((110, 120, 90, 120, 70)):
            p.rr(56, 52 + i * 30, 56 + w, 64 + i * 30, 6, fill=(190, 184, 172))
        p.rr(56, 172, 120, 182, 4, fill=ORANGE)
        p.line([(176, 176), (236, 236)], ORANGE, 24)
        p.circ(150, 150, 54, fill=(255, 255, 255, 60)); p.circ(150, 150, 54, outline=ORANGE, width=14)
        return im
    return cache('logo', mk)

def outro_text():
    def mk():
        im = canvas(W, 260); p = Pen(im)
        p.text(W / 2, 60, 'THE FINE PRINT', ('Black', 84, True), WHITE, anchor='mm', sp=4)
        p.text(W / 2, 150, 'Check the link before you pay.', ('Medium', 38), (200, 208, 224), anchor='mm')
        p.text(W / 2, 220, 'SCAM FILES', ('Bold', 28), ORANGE, anchor='mm', sp=6)
        return im
    return cache('otext', mk)
