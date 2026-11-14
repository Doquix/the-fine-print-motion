"""Reusable sprite library. Every sprite is cached by a key of quantized state.
All text is a parameter so templates can be reused across episodes."""
from .engine import *

CW = 880        # standard card width
PW, PH = 560, 1080   # phone
MW, MH = 880, 330    # modal

def star_pts(cx, cy, R, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts

# ---------------- phone ----------------
DEFAULT_ROWS = (('Rated headphones', '+$4.20'), ('Boosted smart watch', '+$6.80'),
                ('Rated camera kit', '+$5.10'), ('Boosted desk lamp', '+$7.40'))

def phone_spr(press=0.0, dim=0.0, balance='$100.00', button='Withdraw', title='TASK DASHBOARD', rows=DEFAULT_ROWS):
    press = round(press, 1); dim = round(dim, 1); rows = tuple(tuple(r) for r in rows)
    def mk():
        im = canvas(PW, PH); p = Pen(im)
        p.rr(0, 0, PW, PH, 86, fill=(20, 24, 34))
        p.rr(5, 5, PW - 5, PH - 5, 81, outline=(70, 78, 96), width=3)
        p.rr(20, 20, PW - 20, PH - 20, 68, fill=(12, 20, 40))
        p.rr(PW / 2 - 72, 40, PW / 2 + 72, 76, 18, fill=(4, 6, 10))
        p.text(56, 122, title, ('Bold', 22), (140, 156, 188), anchor='lm', sp=3)
        p.circ(PW - 150, 122, 6, fill=(80, 210, 130))
        p.text(PW - 56, 122, 'Online', ('SemiBold', 22), (120, 200, 150), anchor='rm')
        p.line([(56, 160), (PW - 56, 160)], (38, 54, 86), 2)
        p.text(PW / 2, 228, 'Available earnings', ('Medium', 30), (170, 184, 208), anchor='mm')
        p.text(PW / 2, 330, balance, ('Bold', 108, True), WHITE, anchor='mm', feat=['tnum'])
        bs = 1 - 0.07 * press; bw, bh, by = 430 * bs, 112 * bs, 492
        p.rr(PW / 2 - bw / 2, by - bh / 2, PW / 2 + bw / 2, by + bh / 2, 28 * bs, fill=lerpc(ORANGE, (214, 140, 22), press))
        p.text(PW / 2, by, button, ('Bold', 42 * bs), INK, anchor='mm')
        p.text(56, 610, 'Recent activity', ('SemiBold', 26), (150, 164, 192), anchor='lm')
        for i, (a, b) in enumerate(rows[:4]):
            y = 652 + i * 94
            p.rr(46, y, PW - 46, y + 80, 20, fill=(22, 34, 62))
            p.circ(86, y + 40, 17, fill=(46, 170, 104))
            p.check(86, y + 41, 1.0, WHITE, 4)
            p.text(118, y + 40, a, ('Medium', 25), (208, 216, 232), anchor='lm')
            p.text(PW - 66, y + 40, b, ('Bold', 25), (100, 214, 146), anchor='rm')
        if dim > 0:
            ov = canvas(PW, PH); Pen(ov).rr(20, 20, PW - 20, PH - 20, 68, fill=(0, 0, 0, int(170 * dim)))
            im.alpha_composite(ov)
        return im
    return cache(('phone', press, dim, balance, button, title, rows), mk)

PHONE_BUTTON_Y = 492  # local y of the main button in the phone sprite

def ripple_spr(p):
    p = round(p, 2)
    def mk():
        R = 170; im = canvas(2 * R, 2 * R); pen = Pen(im)
        pen.circ(R, R, 30 + 140 * eo3(p), outline=(255, 255, 255, int(220 * (1 - p))), width=6)
        q = min(1, p * 1.6)
        pen.circ(R, R, 18 + 60 * eo3(q), fill=(255, 255, 255, int(120 * (1 - q))))
        return im
    return cache(('rip', p), mk)

# ---------------- alert modal ----------------
def modal_spr(level=1, ul=1.0, hl=0.0, tag='WITHDRAWAL BLOCKED', title='Deposit required',
              sub='Add funds to withdraw', red_sub='Deposit $100.00 to unlock'):
    ul = round(ul, 2); hl = round(hl, 2)
    def mk():
        im = canvas(MW, MH); p = Pen(im)
        p.rr(0, 0, MW, MH, 40, fill=CARD)
        p.rr(48, 50, 92, 94, 12, fill=(252, 226, 226))
        p.rr(61, 72, 79, 86, 3, fill=RED); p.arc((63, 58, 77, 78), 180, 360, RED, 3)
        p.text(110, 72, tag, ('Bold', 25), RED, anchor='lm', sp=3)
        p.text(48, 152, title, ('Bold', 68), INK, anchor='lm')
        col = ORANGE if level == 1 else RED
        if ul > 0: p.line([(50, 202), (50 + ul * min(530, p.tw(title, ('Bold', 68))), 202)], col, 7)
        if level == 1 or hl <= 0:
            p.text(48, 262, sub, ('Medium', 38), MUTED, anchor='lm')
        else:
            tw = p.tw(red_sub, ('Bold', 40))
            p.rr(36, 232, 36 + (tw + 26) * eo3(hl), 292, 12, fill=(252, 222, 222))
            p.text(48, 262, red_sub, ('Bold', 40), RED, anchor='lm')
        return im
    return cache(('modal', level, ul, hl, tag, title, sub, red_sub), mk)

def magnifier_spr():
    def mk():
        im = canvas(220, 220); p = Pen(im)
        p.line([(140, 140), (200, 200)], ORANGE, 24)
        p.circ(92, 92, 70, fill=(255, 255, 255, 60), outline=ORANGE, width=16)
        p.arc((40, 40, 144, 144), 200, 250, (255, 255, 255, 200), 6)
        return im
    return cache(('mag',), mk)

# ---------------- chat ----------------
def chat_content(h, sub_a, bub, typing, sender='Unknown sender', lines=('Easy remote work', 'Flexible hours', 'Quick money'), accent=2):
    lines = tuple(lines)
    key = ('chat', int(h), round(sub_a, 2), tuple(round(b, 2) for b in bub), typing and (typing[0], round(typing[1], 1)), sender, lines, accent)
    def mk():
        im = canvas(CW, max(h, 150)); p = Pen(im)
        p.circ(84, 75, 30, fill=INK)
        for dx in (-11, 0, 11): p.circ(84 + dx, 75, 4, fill=WHITE)
        yy = 62 if sub_a > 0.01 else 75
        p.text(132, yy, sender, ('Bold', 42), INK, anchor='lm')
        if sub_a > 0.01: p.text(132, 104, 'New message', ('Medium', 28), MUTED + (int(255 * sub_a),), anchor='lm')
        p.text(CW - 50, yy, 'now', ('Medium', 28), MUTED, anchor='rm')
        if h > 200: p.line([(48, 140), (CW - 48, 140)], (214, 208, 198, int(255 * clamp((h - 200) / 200))), 2)
        for i, b in enumerate(bub):
            if b <= 0 or i >= len(lines): continue
            k = 0.55 + 0.45 * eoback(b); a = int(255 * clamp(b * 3))
            y = 225 + i * 120; acc = (i == accent)
            fa = ('SemiBold', 44 * k)
            tw = p.tw(lines[i], fa) + (60 * k if acc else 0)
            hh = 96 * k
            p.rr(48, y - hh / 2, 48 + tw + 64 * k, y + hh / 2, 30 * k, fill=((253, 234, 200) if acc else (224, 232, 246)) + (a,))
            tx = 48 + 32 * k
            if acc:
                p.circ(tx + 22 * k, y, 22 * k, fill=ORANGE + (a,))
                p.text(tx + 22 * k, y + 1, '$', ('Black', 30 * k), INK + (a,), anchor='mm')
                tx += 60 * k
            p.text(tx, y + 2, lines[i], fa, ((150, 90, 0) if acc else INK) + (a,), anchor='lm')
        if typing:
            i, a = typing; y = 225 + i * 120
            p.rr(48, y - 40, 168, y + 40, 30, fill=(224, 232, 246, int(255 * a)))
            for j in range(3): p.circ(80 + j * 28, y, 8, fill=(130, 140, 160, int(255 * a)))
        if h >= 560:
            p.rr(48, h - 100, CW - 48, h - 40, 30, outline=(214, 208, 198), width=2)
            p.text(80, h - 70, 'Reply', ('Medium', 28), (160, 160, 165), anchor='lm')
        return im
    return cache(key, mk)

# ---------------- products ----------------
def product_art(p, kind, x0, y0, x1, y1):
    for i in range(int(y0), int(y1)):
        f = (i - y0) / (y1 - y0)
        p.d.line([(x0 * SS, i * SS), (x1 * SS, i * SS)], fill=lerpc((214, 222, 236), (178, 190, 212), f), width=SS)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 10
    p.el(cx - 170, y1 - 60, cx + 170, y1 - 30, fill=(150, 162, 186))
    if kind == 'headphones':
        p.arc((cx - 150, cy - 160, cx + 150, cy + 140), 195, 345, (30, 38, 56), 28)
        for s in (-1, 1):
            x = cx + s * 140
            p.rr(x - 38, cy - 20, x + 38, cy + 120, 30, fill=(34, 44, 66))
            p.rr(x - 22 - s * 8, cy, x + 22 - s * 8, cy + 100, 18, fill=(56, 70, 98))
    elif kind == 'watch':
        p.rr(cx - 55, cy - 175, cx + 55, cy + 175, 26, fill=(44, 52, 72))
        p.circ(cx, cy, 118, fill=(205, 210, 220)); p.circ(cx, cy, 104, fill=(24, 30, 46))
        p.line([(cx, cy), (cx, cy - 66)], WHITE, 7); p.line([(cx, cy), (cx + 48, cy + 18)], ORANGE, 7)
        p.rr(cx + 112, cy - 18, cx + 134, cy + 18, 6, fill=(205, 210, 220))
    elif kind == 'camera':
        p.rr(cx - 70, cy - 150, cx + 40, cy - 90, 14, fill=(30, 38, 56))
        p.rr(cx - 190, cy - 110, cx + 190, cy + 125, 32, fill=(36, 44, 64))
        p.circ(cx, cy + 8, 96, fill=(205, 210, 220)); p.circ(cx, cy + 8, 82, fill=(20, 26, 40))
        p.circ(cx, cy + 8, 52, fill=(52, 76, 120)); p.circ(cx - 18, cy - 12, 12, fill=(220, 230, 255))
        p.rr(cx + 120, cy - 90, cx + 160, cy - 66, 6, fill=ORANGE)
    elif kind == 'phone':
        p.rr(cx - 95, cy - 170, cx + 95, cy + 170, 30, fill=(30, 38, 56))
        p.rr(cx - 80, cy - 150, cx + 80, cy + 150, 20, fill=(70, 100, 160))
        p.rr(cx - 30, cy - 142, cx + 30, cy - 130, 6, fill=(20, 26, 40))
    else:  # generic box
        p.rr(cx - 150, cy - 120, cx + 150, cy + 120, 24, fill=(180, 140, 90))
        p.rr(cx - 150, cy - 30, cx + 150, cy - 10, 4, fill=(150, 110, 60))

PH_CARD = 880
def product_content(kind, name, n, total, stars, btn_a, btn_press, boosted, header='Product rating', btn='Boost listing', done='Listing boosted'):
    stars = tuple(round(s, 2) for s in stars)
    key = ('prod', kind, name, n, total, stars, round(btn_a, 2), round(btn_press, 1), round(boosted, 2), header, btn, done)
    def mk():
        im = canvas(CW, PH_CARD); p = Pen(im)
        p.text(48, 62, f'TASK {n} OF {total}', ('Bold', 25), (200, 130, 10), anchor='lm', sp=3)
        p.text(CW - 48, 62, header, ('Medium', 28), MUTED, anchor='rm')
        tmp = canvas(CW, PH_CARD); product_art(Pen(tmp), kind, 48, 100, CW - 48, 500)
        m = canvas(CW, PH_CARD); Pen(m).rr(48, 100, CW - 48, 500, 26, fill=(255, 255, 255, 255))
        im.paste(tmp, (0, 0), m.getchannel('A'))
        p.text(48, 566, name, ('Bold', 50), INK, anchor='lm')
        for i, s in enumerate(stars):
            cx = 80 + i * 84; cy = 650
            p.poly(star_pts(cx, cy, 34, 15), (222, 214, 200))
            if s > 0:
                k = 0.4 + 0.6 * eoback(s); p.poly(star_pts(cx, cy, 34 * k, 15 * k), ORANGE)
        if btn_a > 0:
            bs = 1 - 0.06 * btn_press; y = 776; bw = (CW - 96) * bs; bh = 100 * bs
            a = int(255 * btn_a)
            p.rr(CW / 2 - bw / 2, y - bh / 2, CW / 2 + bw / 2, y + bh / 2, 28, fill=lerpc(ORANGE, (200, 238, 214), boosted) + (a,))
            if boosted < 0.5:
                p.text(CW / 2, y, btn, ('Bold', 42 * bs), INK + (a,), anchor='mm')
            else:
                tw = p.tw(done, ('Bold', 42))
                p.check(CW / 2 - tw / 2 - 20, y, 1.8, (20, 120, 64), 6)
                p.text(CW / 2 + 20, y, done, ('Bold', 42), (20, 110, 60), anchor='mm')
        return im
    return cache(key, mk)

# ---------------- dashboard / odometer ----------------
DH = 680
SPARK = [(i / 24, (i / 24) ** 0.85 + 0.06 * math.sin(i * 1.9) * (i > 0) - 0.02 * (i % 3 == 0)) for i in range(25)]

def odometer(p, cx, cy, v, fa, fill, prefix='$'):
    f = p.font(fa)
    dw = f.getlength('0', features=['tnum']) / SS
    sw = f.getlength(prefix) / SS; pw = f.getlength('.') / SS
    c = max(0.0, v * 100); ints = int(c // 100)
    n = max(1, len(str(ints)))
    k = n + 2; rem = c % (10 ** k)
    lead_f = rem - (10 ** k - 1) if rem > 10 ** k - 1 else 0.0
    wn = sw + n * dw + pw + 2 * dw
    total = wn + dw * lead_f
    x = cx - total / 2
    lh = fa[1] * 1.05
    layer = canvas(wn + dw + 40, lh); lp = Pen(layer); ymid = lh / 2
    lp.text(10, ymid, prefix, fa, fill, anchor='lm')
    xx = 10 + sw
    positions = list(range(n + 2, -1, -1)) if lead_f > 0 else list(range(n + 1, -1, -1))
    for kk in positions:
        xk = c / (10 ** kk); d = int(xk) % 10
        fr = xk - int(xk) if kk == 0 else clamp(c % (10 ** kk) - (10 ** kk - 1))
        cur = '' if (kk == positions[0] and d == 0 and kk > 2) else str(d)
        lp.text(xx + dw / 2, ymid - fr * lh, cur, fa, fill, anchor='mm', feat=['tnum'])
        if fr > 0: lp.text(xx + dw / 2, ymid + (1 - fr) * lh, str((d + 1) % 10), fa, fill, anchor='mm', feat=['tnum'])
        xx += dw
        if kk == 2: lp.text(xx, ymid, '.', fa, fill, anchor='lm'); xx += pw
    gh = layer.height; g = np.ones(gh, np.float32); e = int(gh * 0.16)
    g[:e] = np.linspace(0, 1, e); g[-e:] = np.linspace(1, 0, e)
    m = Image.fromarray((np.tile(g[:, None], (1, layer.width)) * 255).astype(np.uint8))
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'), m))
    p.img.alpha_composite(layer, (int((x - 10) * SS), int((cy - lh / 2) * SS)))

def dash_content(v, nchk=0, chk_pop=1.0, total_chk=5, gray=0.0, glow=0.0, compact=False, title='TASK DASHBOARD',
                 label='Available earnings', chk_label='Tasks completed', vmax=100.0):
    h = 400 if compact else DH
    im = canvas(CW, h); p = Pen(im)
    tc = lerpc((150, 166, 198), (150, 150, 150), gray)
    p.text(48, 62, title, ('Bold', 25), tc, anchor='lm', sp=3)
    p.circ(CW - 160, 62, 7, fill=lerpc((80, 210, 130), (130, 130, 130), gray))
    p.text(CW - 48, 62, 'Online', ('SemiBold', 26), lerpc((120, 200, 150), (140, 140, 140), gray), anchor='rm')
    p.text(CW / 2, 150, label, ('Medium', 36), lerpc((176, 190, 214), (160, 160, 160), gray), anchor='mm')
    if glow > 0:
        g = canvas(CW, h); Pen(g).el(CW / 2 - 300, 190, CW / 2 + 300, 360, fill=(245, 166, 35, int(70 * glow)))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    odometer(p, CW / 2, 272, v, ('Bold', 150, True), lerpc(WHITE, (190, 190, 190), gray))
    if compact: return im
    x0, x1, y0, y1 = 60, CW - 60, 530, 370
    prog = clamp(v / vmax); pts = []
    for (fx, fy) in SPARK:
        if fx > prog: break
        pts.append((x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)))
    if prog > 0 and len(pts) < len(SPARK):
        i = len(pts); a0, a1 = SPARK[i - 1], SPARK[i]
        fy = lerp(a0[1], a1[1], (prog - a0[0]) / (a1[0] - a0[0]))
        pts.append((x0 + prog * (x1 - x0), y0 + fy * (y1 - y0)))
    p.line([(x0, y0), (x1, y0)], (44, 60, 96), 2)
    if len(pts) >= 2:
        fl = canvas(CW, h); Pen(fl).poly(pts + [(pts[-1][0], y0), (x0, y0)], (245, 166, 35, 46)); im.alpha_composite(fl)
        p.line(pts, ORANGE, 6)
        ex, ey = pts[-1]; p.circ(ex, ey, 18, fill=(245, 166, 35, 70)); p.circ(ex, ey, 9, fill=ORANGE)
    p.text(48, 612, chk_label, ('Medium', 30), (150, 166, 198), anchor='lm')
    for i in range(total_chk):
        cx = CW - 80 - (total_chk - 1 - i) * 66; cy = 612
        if i < nchk:
            k = eoback(chk_pop) if i == nchk - 1 else 1
            p.circ(cx, cy, 24 * k, fill=ORANGE); p.check(cx, cy + 1, 1.2 * k, INK, 5)
        else:
            p.circ(cx, cy, 24, outline=(60, 78, 116), width=3)
    return im

def chip_spr(txt, col=GREEN):
    def mk():
        im = canvas(240, 80); p = Pen(im)
        tw = p.tw(txt, ('Bold', 38))
        p.rr(120 - tw / 2 - 26, 4, 120 + tw / 2 + 26, 76, 36, fill=col)
        p.text(120, 41, txt, ('Bold', 38), INK, anchor='mm')
        return im
    return cache(('chip', txt, col), mk)

# ---------------- payment / meter ----------------
def notif_content(hl=0.0, ring=0.0, title='Payment received', amount='$5.00', rest='sent to your bank'):
    key = ('notif', round(hl, 2), round(ring, 2), title, amount, rest)
    def mk():
        im = canvas(CW, 180); p = Pen(im)
        if ring > 0:
            for j in range(2):
                q = clamp(ring * 1.3 - j * 0.3)
                if 0 < q < 1: p.circ(96, 90, 40 + 50 * eo3(q), outline=(46, 190, 110, int(200 * (1 - q))), width=5)
        p.circ(96, 90, 40, fill=GREEN); p.check(96, 92, 2.0, WHITE, 7)
        p.text(164, 70, title, ('Bold', 44), INK, anchor='lm')
        if hl > 0:
            tw = p.tw(amount, ('Bold', 30)); p.rr(158, 100, 158 + (tw + 16) * eo3(hl), 140, 10, fill=(200, 238, 214))
        p.text(166, 120, amount, ('Bold', 30), (20, 120, 64), anchor='lm')
        p.text(166 + p.tw(amount + ' ', ('Bold', 30)), 120, rest, ('Medium', 30), MUTED, anchor='lm')
        p.text(CW - 48, 70, 'now', ('Medium', 28), MUTED, anchor='rm')
        return im
    return cache(key, mk)

def meter_content(f, label='Your trust', col=GREEN):
    key = ('meter', round(f, 3), label, col)
    def mk():
        im = canvas(CW, 190); p = Pen(im)
        p.text(48, 62, label, ('SemiBold', 36), INK, anchor='lm')
        p.text(CW - 48, 62, f'{int(round(f * 100))}%', ('Bold', 40), (20, 120, 64) if col == GREEN else col, anchor='rm', feat=['tnum'])
        p.rr(48, 112, CW - 48, 142, 15, fill=(226, 220, 210))
        if f > 0.02: p.rr(48, 112, 48 + (CW - 96) * f, 142, 15, fill=col)
        return im
    return cache(key, mk)

# ---------------- coin ----------------
def coin_spr(back=False, glyph='B'):
    def mk():
        R = 190; im = canvas(2 * R, 2 * R); p = Pen(im)
        for i in range(40):
            f = i / 39
            p.circ(R, R, R - i * 1.2, fill=lerpc((178, 108, 14), (252, 196, 72), f) if not back else lerpc((140, 84, 10), (210, 150, 40), f))
        p.circ(R, R, R - 34, outline=(170, 100, 10), width=6)
        p.circ(R, R, R - 46, fill=(246, 180, 52) if not back else (196, 136, 34))
        if not back:
            p.text(R + 4, R + 6, glyph, ('Black', 190, True), (150, 86, 6), anchor='mm')
            if glyph == 'B':
                for dx in (-22, 18):
                    p.line([(R + dx, R - 118), (R + dx, R - 88)], (150, 86, 6), 14)
                    p.line([(R + dx, R + 92), (R + dx, R + 122)], (150, 86, 6), 14)
        p.arc((26, 26, 2 * R - 26, 2 * R - 26), 200, 260, (255, 240, 200, 180), 8)
        return im
    return cache(('coin', back, glyph), mk)

def glow_ring_spr(q):
    q = round(q, 2)
    def mk():
        im = canvas(600, 600); Pen(im).circ(300, 300, 200 + 90 * q, outline=(252, 196, 72, int(150 * (1 - q))), width=5)
        return im
    return cache(('gring', q), mk)

def label_spr(txt, fa, col, sp=0):
    def mk():
        f = F(fa[0], fa[1] * SS, fa[2] if len(fa) > 2 else False)
        tw = (sum(f.getlength(c) for c in txt) / SS + sp * (len(txt) - 1)) if sp else f.getlength(txt) / SS
        im = canvas(tw + 40, fa[1] * 1.5)
        Pen(im).text(20 + tw / 2, fa[1] * 0.75, txt, fa, col, anchor='mm', sp=sp)
        return im
    return cache(('lbl', txt, fa, col, sp), mk)

# ---------------- wallet ----------------
def wallet_icon(p, x, y, k=1.0):
    p.circ(x, y, 30 * k, fill=ORANGE)
    p.rr(x - 15 * k, y - 10 * k, x + 15 * k, y + 11 * k, 5 * k, fill=INK)
    p.rr(x + 3 * k, y - 4 * k, x + 15 * k, y + 5 * k, 3 * k, fill=ORANGE)

def wallet_content(status, spin, expect, title='Your wallet', row='Outgoing deposit', amount='-$100.00',
                   expect_label='Expected back', expect_amount='$200.00', proc='Processing', done='Submitted'):
    key = ('wal', status, round(spin, 1) if status == 'proc' else 0, round(expect, 2), title, row, amount, expect_label, expect_amount)
    def mk():
        h = 450; im = canvas(CW, h); p = Pen(im)
        wallet_icon(p, 84, 72)
        p.text(132, 72, title, ('Bold', 44), INK, anchor='lm')
        p.line([(48, 136), (CW - 48, 136)], (214, 208, 198), 2)
        p.text(48, 200, row, ('SemiBold', 40), INK, anchor='lm')
        p.text(CW - 48, 200, amount, ('Bold', 46), RED, anchor='rm', feat=['tnum'])
        if status == 'proc':
            a0 = spin * 360; p.arc((48, 262, 92, 306), a0, a0 + 260, (200, 130, 10), 6)
            p.text(110, 284, proc, ('Medium', 34), MUTED, anchor='lm')
        else:
            p.circ(70, 284, 22, fill=GREEN); p.check(70, 285, 1.1, WHITE, 5)
            p.text(110, 284, done, ('SemiBold', 34), (20, 120, 64), anchor='lm')
        if expect > 0 and expect_label:
            a = int(255 * clamp(expect * 2)); y = 374
            p.rr(40, y - 40, CW - 40, y + 40, 20, fill=(253, 238, 210, a))
            x = 50
            while x < CW - 60:
                for yy in (y - 40, y + 40): p.line([(x, yy), (min(x + 18, CW - 60), yy)], (230, 160, 40, a), 2)
                x += 30
            p.text(64, y, expect_label, ('Medium', 34), (150, 95, 10, a), anchor='lm')
            p.text(CW - 64, y, expect_amount, ('Bold', 40), (200, 120, 0, a), anchor='rm', feat=['tnum'])
            if expect < 1:
                sx = lerp(40, CW - 40, expect)
                sh = canvas(CW, h); Pen(sh).poly([(sx - 60, y - 40), (sx, y - 40), (sx - 40, y + 40), (sx - 100, y + 40)], (255, 255, 255, 140))
                im.alpha_composite(sh)
        return im
    return cache(key, mk)

def mini_wallet(title, amount, col, flash=0.0):
    key = ('miniw', title, amount, col, round(flash, 2))
    def mk():
        w, h = 410, 250; im = canvas(w, h); p = Pen(im)
        p.rr(0, 0, w, h, 34, fill=lerpc(DARKCARD, (40, 120, 80), flash))
        p.rr(1, 1, w - 1, h - 1, 34, outline=(52, 72, 112), width=2)
        wallet_icon(p, 64, 64, 0.85)
        p.text(108, 64, title, ('Bold', 32), WHITE, anchor='lm')
        p.text(w / 2, 168, amount, ('Bold', 64, True), col, anchor='mm', feat=['tnum'])
        return im
    return cache(key, mk)

# ---------------- stamps / crack ----------------
def stamp_spr(txt):
    def mk():
        fa = ('Black', 150, True); f = F('Black', 150 * SS, True)
        w, h = f.getlength(txt) / SS + 110, 230
        im = canvas(w, h); p = Pen(im)
        p.rr(10, 10, w - 10, h - 10, 30, fill=(214, 40, 48))
        p.rr(24, 24, w - 24, h - 24, 22, outline=(255, 235, 235), width=6)
        p.text(w / 2, h / 2 + 6, txt, fa, WHITE, anchor='mm')
        n = np.random.default_rng(len(txt)).random((int(h * SS / 6), int(w * SS / 6)))
        m = Image.fromarray(((n > 0.10) * 255).astype(np.uint8)).resize(im.size, Image.NEAREST).filter(ImageFilter.GaussianBlur(1.2))
        im.putalpha(ImageChops.multiply(im.getchannel('A'), m))
        return im
    return cache(('stamp', txt), mk)

def _crack_paths(ox, oy, seed=3):
    rng = random.Random(seed); paths = []
    for i in range(9):
        ang = i * 2 * math.pi / 9 + rng.uniform(-0.3, 0.3)
        pts = [(ox, oy)]; x, y = ox, oy; L = rng.uniform(160, 420)
        for s in range(6):
            ang += rng.uniform(-0.45, 0.45); x += math.cos(ang) * L / 6; y += math.sin(ang) * L / 6
            pts.append((x, y))
        paths.append(pts)
    return paths
_CP = _crack_paths(MW * 0.55, MH * 0.5)
def crack_spr(prog):
    prog = round(prog, 2)
    def mk():
        im = canvas(MW, MH); p = Pen(im)
        for pts in _CP:
            n = max(2, int(len(pts) * prog))
            seg = [(clamp(x, 4, MW - 4), clamp(y, 4, MH - 4)) for x, y in pts[:n]]
            if len(seg) >= 2: p.line(seg, (255, 255, 255, 220), 6); p.line(seg, (40, 20, 24, 230), 3)
        mask = canvas(MW, MH); Pen(mask).rr(0, 0, MW, MH, 40, fill=(255, 255, 255, 255))
        im.putalpha(ImageChops.multiply(im.getchannel('A'), mask.getchannel('A')))
        return im
    return cache(('crack', prog), mk)

def glitch(im, off, seed):
    if not PROFILE['glitch']: return im
    r, g, bb, a = im.split()
    out = Image.merge('RGBA', (ImageChops.offset(r, off, 0), g, ImageChops.offset(bb, -off, 0), a))
    rnd = random.Random(seed)
    for _ in range(5):
        y = rnd.randrange(0, im.height - 60); hh = rnd.randrange(16, 60); dx = rnd.randrange(-40, 40)
        out.paste(out.crop((0, y, im.width, y + hh)), (dx, y))
    return out

# ---------------- source card ----------------
def source_content(hl, org='FEDERAL TRADE COMMISSION', lines=('How to spot and', 'avoid task scams'), phrase='task scams',
                   footer_l='Consumer advice', footer_r='consumer.ftc.gov'):
    lines = tuple(lines)
    key = ('src', round(hl, 2), org, lines, phrase, footer_l, footer_r)
    def mk():
        h = 560; im = canvas(CW, h); p = Pen(im)
        p.rr(0, 0, CW, 96, 38, fill=NAVY); p.d.rectangle([0, 60 * SS, CW * SS, 96 * SS], fill=NAVY)
        p.circ(70, 48, 24, outline=(220, 200, 150), width=4)
        p.text(112, 48, org, ('Bold', 26), WHITE, anchor='lm', sp=3)
        fa = ('Bold', 74)
        for i, ln in enumerate(lines[:2]):
            y = 196 + i * 94
            j = ln.find(phrase) if phrase else -1
            if j >= 0 and hl > 0:
                x0 = 48 + p.tw(ln[:j], fa); tw = p.tw(phrase, fa)
                p.rr(x0 - 10, y - 42, x0 - 10 + (tw + 20) * eo3(hl), y + 40, 14, fill=(250, 200, 110))
            p.text(48, y, ln, fa, INK, anchor='lm')
        p.line([(48, 400), (CW - 48, 400)], (214, 208, 198), 2)
        p.text(48, 462, footer_l, ('SemiBold', 32), INK, anchor='lm')
        p.text(CW - 48, 462, footer_r, ('Medium', 30), MUTED, anchor='rm')
        return im
    return cache(key, mk)

# ---------------- brand ----------------
def logo_icon():
    def mk():
        im = canvas(280, 320); p = Pen(im)
        p.rr(30, 14, 230, 300, 26, fill=CARD)
        p.poly([(180, 14), (230, 14), (230, 64)], RED)
        for y, x1 in ((222, 190), (250, 170), (276, 140)): p.line([(64, y), (x1, y)], INK, 10)
        p.line([(196, 170), (250, 228)], ORANGE, 24)
        p.circ(150, 118, 74, fill=WHITE, outline=ORANGE, width=18)
        p.el(98, 94, 202, 142, fill=INK)
        p.circ(150, 118, 20, fill=WHITE); p.circ(150, 118, 10, fill=INK)
        return im
    return cache(('logo',), mk)

def brand_bug(dark_text, show='THE FINE PRINT', series='SCAM FILES'):
    def mk():
        im = canvas(W, 75); p = Pen(im)
        c = INK if dark_text else (236, 238, 244)
        m = (90, 96, 112) if dark_text else (150, 160, 182)
        p.text(70, 30, show, ('Bold', 28), c, anchor='lm', sp=3)
        p.text(W - 70, 30, series, ('Bold', 28), (214, 140, 16) if dark_text else ORANGE, anchor='rm', sp=3)
        p.line([(70, 62), (W - 70, 62)], m + (120,), 2)
        return im
    return cache(('bug', dark_text, show, series), mk)

def caption_spr(txt, kw):
    size = PROFILE['cap_size']
    def mk():
        fa = ('Bold', size); f = F('Bold', size * SS)
        pad = round(size * 0.7)
        w, h = f.getlength(txt) / SS + 2 * pad, round(size * 1.92)
        im = canvas(w, h); p = Pen(im)
        p.rr(0, 0, w, h, h * 0.26, fill=(10, 15, 30, 236))
        x = pad; i = txt.find(kw) if kw else -1
        parts = [(txt, WHITE)] if i < 0 else [(txt[:i], WHITE), (kw, ORANGE), (txt[i + len(kw):], WHITE)]
        for s, col in parts:
            if s: p.text(x, h / 2 + 2, s, fa, col, anchor='lm'); x += f.getlength(s) / SS
        return im
    return cache(('cap', txt, kw, size), mk)
