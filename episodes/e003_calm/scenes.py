"""E003 calm: episode specific scenes (QR code parking scam, older viewers).

Calm motion language: one idea per screen, holds of 1.5 to 2.5 s with a slow push,
soft crossfades between scenes (no whips), eased moves without big overshoot,
and the detail that matters lifted out of the phone into a large callout card.
"""
import math
import numpy as np
from PIL import Image
from fpm.templates.base import *
import qr_sprites as S

ENTER, EXIT = 0.6, 0.38
DELAY = 0.12  # incoming scene waits for the outgoing one to clear (no double exposure)
PHX, PHY = CX, 830


def ein(t, t0, d=ENTER): return eio(P(t, t0, d))
def enter(t, t0, d=0.55): return eio(P(t, t0 + DELAY, d))


def scrim(b, col, a):
    """Soft band behind the brand bug while a zoomed object passes under it."""
    if a <= 0.01: return
    def mk():
        al = (np.clip(1 - (np.arange(440) - 170) / 270, 0, 1) ** 1.6 * 230).astype(np.uint8)
        im = Image.new('RGBA', (W, 440), col + (0,)); im.putalpha(Image.fromarray(np.repeat(al[:, None], W, 1)))
        return im
    full = Image.new('RGBA', (W, H), (0, 0, 0, 0)); full.paste(fade(cache(('scrim', col), mk), a), (0, 0))
    b.alpha_composite(full)


def soft_pop(t, t0, d=0.45): return eoback(P(t, t0, d), 0.9) if t >= t0 else 0.0


def draw_meter(b, gx, gy, g, d=0, a=1.0, outline=0.0, dashed=0.0):
    if a <= 0.004: return
    put(b, S.meter_body(), gx, gy, g, a)
    sy = gy + S.METER_STICK_DY * g
    put(b, S.sticker_under(), gx, sy, g, a)
    put(b, S.sticker_top(d, outline, dashed), gx, sy, g, a)


def stk(gx, gy, g, lx, ly):
    return gx + (lx - S.STW / 2) * g, gy + S.METER_STICK_DY * g + (ly - S.STH / 2) * g


def draw_phone(b, x, y, sc, screen, a=1.0, extra=None):
    if a <= 0.004: return
    put(b, shadow_spr(S.PW, S.PH, 66, 40, 100), x, y + 30 * sc, sc, a, ss=0.25)
    put(b, S.phone_frame(), x + 3 * sc, y, sc, a)
    if screen is not None: put(b, screen, x, y, sc, a)
    if extra: extra()
    put(b, S.island(), x, y - (S.PH / 2 - 40) * sc, sc, a)


def scr(x, y, sc, lx, ly): return x + (lx - S.SW / 2) * sc, y + (ly - S.SH / 2) * sc


def ring_pulse(b, t, t0, x, y, r0, r1, col, d=0.9):
    if t0 is not None and t0 <= t < t0 + d:
        q = P(t, t0, d)
        put(b, S.ring(r0 + (r1 - r0) * eo3(q), col, 7), x, y, 1.0, (1 - q) * 0.9)


# ------------------------------------------------------------------ big callout cards
CW_ = 880

def url_callout(red=0.0, xbtn=0.0):
    red = round(red, 1); xbtn = round(xbtn, 1)
    def mk():
        w, h = CW_, 230
        im = canvas(w, h); p = Pen(im)
        p.text(48, 58, 'Web address', ('SemiBold', 32), MUTED, anchor='lm')
        bc = lerpc((236, 238, 242), (253, 228, 228), red)
        p.rr(30, 96, w - 30, 196, 30, fill=bc)
        c = lerpc(INK, RED, red)
        p.rr(62, 136, 84, 162, 4, fill=c); p.arc((65, 120, 81, 146), 180, 360, c, 4)
        fs = 54
        while p.tw('citypark-pay.co/zone4', ('Bold', fs)) > w - 104 - 60 - (90 if xbtn > 0 else 0): fs -= 1
        p.text(104, 147, 'citypark-pay.co/zone4', ('Bold', fs), c, anchor='lm')
        if xbtn > 0:
            r = 34 * xbtn; X = w - 80
            p.circ(X, 146, r, fill=INK); k = 12 * xbtn
            p.line([(X - k, 146 - k), (X + k, 146 + k)], WHITE, 6); p.line([(X + k, 146 - k), (X - k, 146 + k)], WHITE, 6)
        return im
    return cache(('urlc', red, xbtn), mk)


def number_callout(n=0, cursor=True, field=1.0):
    def mk():
        w, h = CW_, 250
        im = canvas(w, h); p = Pen(im)
        p.text(48, 58, 'Card number', ('SemiBold', 32), MUTED, anchor='lm')
        p.rr(30, 96, w - 30, 210, 30, fill=WHITE, outline=lerpc((206, 210, 220), ORANGE, field), width=4)
        if n == 0:
            p.text(70, 154, '1234 5678 9012 3456', ('SemiBold', 62), (196, 200, 210), anchor='lm', feat=['tnum']); cx = 66
        else:
            s = S.CARDNUM[:n]; s = ' '.join(s[i:i + 4] for i in range(0, len(s), 4))
            p.text(70, 154, s, ('Bold', 64), INK, anchor='lm', feat=['tnum'])
            cx = 74 + p.tw(s, ('Bold', 64), feat=['tnum'])
        if cursor and n < 16: p.rr(cx, 122, cx + 5, 186, 2, fill=ORANGE)
        return im
    return cache(('numc', n, cursor, round(field, 1)), mk)


def scam_big(rows=0):
    def mk():
        w, h = CW_, 420
        im = canvas(w, h); p = Pen(im)
        p.circ(56, 58, 11, fill=RED)
        p.text(80, 58, 'SENT TO THE SCAMMER', ('Bold', 32), RED, anchor='lm', sp=3)
        data = [('Card', '4821 7730 1956 0042'), ('Expires', '08 / 29'), ('Security code', '417')]
        for i, (k, v) in enumerate(data[:rows]):
            y = 130 + i * 92
            p.text(48, y, k, ('Medium', 30), (170, 160, 180), anchor='lm')
            p.text(w - 48, y, v, ('Bold', 42), WHITE, anchor='rm', feat=['tnum'])
            if i < 2: p.line([(48, y + 46), (w - 48, y + 46)], (60, 44, 66), 2)
        return im
    return cache(('scamb', rows), mk)


def status_big(rows=1.0, pulse=0.0):
    rows = round(rows, 1); pulse = round(pulse, 1)
    def mk():
        w, h = CW_, 440
        im = canvas(w, h); p = Pen(im)
        p.text(48, 62, 'PARKING', ('Bold', 30), MUTED, anchor='lm', sp=4)
        p.text(48, 126, 'Zone 4 · Space 112', ('Bold', 52), INK, anchor='lm')
        lay = canvas(w, h); q = Pen(lay)
        A = int(255 * clamp(rows * 2))
        q.rr(30, 184, w - 30, 300, 26, fill=WHITE + (A,))
        q.text(64, 242, 'Paid', ('SemiBold', 38), MUTED + (A,), anchor='lm')
        q.text(w - 64, 242, 'No', ('Bold', 46), RED + (A,), anchor='rm')
        A = int(255 * clamp(rows * 2 - 1))
        q.rr(30, 316, w - 30, 412, 26, fill=WHITE + (A,))
        q.text(64, 364, 'Time left', ('SemiBold', 38), MUTED + (A,), anchor='lm')
        q.text(w - 64, 364, '0:00', ('Bold', 46), lerpc(INK, RED, pulse) + (A,), anchor='rm', feat=['tnum'])
        im.alpha_composite(lay)
        return im
    return cache(('statb', rows, pulse), mk)


def search_bar(q):
    def mk():
        w, h = CW_, 130
        im = canvas(w, h); p = Pen(im)
        p.circ(70, 65, 20, outline=MUTED, width=5); p.line([(84, 79), (100, 95)], MUTED, 5)
        txt = S.QUERY[:q]
        if txt:
            p.text(126, 66, txt, ('SemiBold', 46), INK, anchor='lm'); cx = 130 + p.tw(txt, ('SemiBold', 46))
        else:
            p.text(126, 66, 'Search', ('SemiBold', 46), (186, 190, 200), anchor='lm'); cx = 126
        if q < len(S.QUERY): p.rr(cx, 40, cx + 4, 92, 2, fill=(60, 120, 230))
        return im
    return cache(('sbar', q), mk)


def result_app(badge=0.0, tap=0.0):
    badge = round(badge, 1); tap = round(tap, 1)
    def mk():
        w, h = CW_, 250
        im = canvas(w, h); p = Pen(im)
        p.rr(40, 40, 170, 170, 34, fill=(30, 74, 140))
        p.circ(105, 105, 36, fill=WHITE); p.circ(105, 105, 21, fill=(30, 74, 140))
        p.text(200, 78, 'City Parking', ('Bold', 50), INK, anchor='lm')
        p.text(200, 132, 'Parking payment app', ('Medium', 34), MUTED, anchor='lm')
        if badge > 0:
            bs = eoback(badge, 0.9); bx, by = 200, 168
            p.rr(bx, by, bx + 250 * bs, by + 58, 29, fill=(222, 246, 232))
            if bs > .6:
                p.poly([(bx + 24, by + 13), (bx + 48, by + 13), (bx + 48, by + 31), (bx + 36, by + 47), (bx + 24, by + 31)], (20, 150, 80))
                p.check(bx + 36, by + 28, 0.8, WHITE, 3)
                p.text(bx + 64, by + 30, 'OFFICIAL', ('Bold', 28), (20, 130, 70), anchor='lm', sp=3)
        if tap > 0:
            p.circ(w - 90, 105, 40 * tap, fill=GREEN); p.check(w - 90, 105, 1.9 * tap, WHITE, 8)
        return im
    return cache(('rapp', badge, tap), mk)


def result_web():
    def mk():
        w, h = CW_, 200
        im = canvas(w, h); p = Pen(im)
        g = (20, 120, 64)
        p.rr(48, 62, 76, 92, 5, fill=g); p.arc((52, 42, 72, 74), 180, 360, g, 5)
        p.text(100, 78, 'yourcity.gov/parking', ('Bold', 48), g, anchor='lm')
        p.text(48, 142, 'Pay for parking · City website', ('Medium', 34), MUTED, anchor='lm')
        return im
    return cache('rweb', mk)


def check_row(text, q):
    q = round(q, 2)
    def mk():
        w, h = CW_, 120
        im = canvas(w, h); p = Pen(im)
        r = 32 * eoback(q, 0.9)
        if r > 1:
            p.circ(70, 60, r, fill=GREEN); p.check(70, 60, 1.5 * min(1, q * 1.4), WHITE, 7)
        p.text(128, 62, text, ('Bold', 46), INK + (int(255 * clamp(q * 2)),), anchor='lm')
        return im
    return cache(('crow', text, q), mk)


# ------------------------------------------------------------------ scenes
class QrScan(Scene):
    """Meter with a QR sticker; brackets lock, a link preview appears, then grows into the phone page."""
    name = 'qr_scan'
    TIMES = ('lock', 'pill', 'tap', 'morph')
    bg_default = 'navy'
    post = 0.0

    def draw(self, b, t):
        p = self.p
        m = eio(P(t, p['morph'], 0.6))
        g = 0.82 + 0.04 * P(t, 0, p['morph'])               # slow push
        gx, gy = CX, 845
        draw_meter(b, gx, gy, g * (1 + 0.5 * m), 0, 1 - m)
        # hook: say what this is in the very first frame (also the thumbnail frame)
        put(b, S.tag('SCAM ALERT  ·  PARKING QR CODES', ORANGE, INK, 30), CX, 368 - 30 * eio(P(t, p['morph'] - .3, .4)), 1.0,
            1 - eio(P(t, p['morph'] - .3, .4)))
        sx, sy = gx, gy + S.METER_STICK_DY * g
        lk = eo3(P(t, p['lock'], 0.45))
        put(b, S.brackets(lerp(430, 340, lk) * g / 0.82, GREEN if t >= p['lock'] else WHITE), sx, sy, 1.0, ein(t, 0.15, 0.4) * (1 - m))
        if t < p['lock'] + 0.1:
            yy = sy + lerp(-150, 150, eio(P(t, 0.25, p['lock'] - 0.25)))
            put(b, S.scanline(320), sx, yy, 1.0, P(t, 0.25, 0.15) * (1 - P(t, p['lock'], 0.15)))
        ring_pulse(b, t, p['lock'], sx, sy, 180, 300, GREEN)
        if t >= p['pill']:
            pill = S.link_pill('citypark-pay.co')
            pw, ph = pill.width / SS, pill.height / SS
            px, py = CX, 1255
            if m <= 0:
                put(b, pill, px, py + 40 * (1 - ein(t, p['pill'], .5)), 1.0, ein(t, p['pill'], .4))
                if t >= p['tap']: put(b, S.ripple(P(t, p['tap'], 0.6)), px + 130, py, 1.0)
            else:
                m1 = eio(P(t, p['morph'], 0.3)); m2 = eio(P(t, p['morph'] + 0.22, 0.5))
                s0 = 0.34; s_ = lerp(s0, 1.0, m2)
                w = lerp(pw, S.SW * s0, m1) * s_ / s0; h = lerp(ph, S.SH * s0, m1) * s_ / s0
                x = lerp(px, PHX, m2); y = lerp(py, PHY, m2)
                put(b, S.phone_frame(), x + 3 * s_, y, s_, m1)
                put(b, bg_spr(w, h, 48 * s_, S.SCREEN_BG), x, y, 1.0)
                put(b, pill, x, y, 1.0, 1 - m1)
                m = m2
                if m > 0.3: put(b, S.pay_screen(1), x, y, s_, clamp(m * 2 - 0.6))

    def events(self):
        p = self.p
        return [('sfx', 0.0, 'whoosh', .5, 0, dict(d=.5, f0=300, f1=1500, g=.25)),
                ('sfx', p['lock'], 'ping', .7, 0, {}), ('punch', p['lock'], .015),
                ('sfx', p['pill'], 'pop', .7, 0, dict(p=.9)), ('sfx', p['tap'], 'tap', .9, 0, {}),
                ('sfx', p['morph'], 'whoosh', .6, 0, dict(d=.6, f0=300, f1=2000, g=.3))]


class QrPayPage(Scene):
    """Phone with the payment page; the card field lifts out as a big callout."""
    name = 'qr_pay_page'
    TIMES = ('field',)
    bg_default = 'cream'
    post = EXIT

    def draw(self, b, t):
        p = self.p
        out = eio(P(t, self.end, EXIT))
        lift = eio(P(t, p['field'], 0.7))
        sc = lerp(1.0, 0.72, lift); y = lerp(PHY, 650, lift) + 120 * out
        a = 1 - out
        fx, fy = scr(PHX, y, sc, S.SW / 2, 533)
        draw_phone(b, PHX, y, sc, S.pay_screen(1, lift, 0, 0, False), a)
        if lift > 0:
            cy = lerp(fy, 1170, lift) + 120 * out
            csc = lerp(0.45, 1.0, lift)
            draw_card(b, CX, cy, CW_, 250, 34, CARD, [(number_callout(0, int(t * 2.2) % 2 == 0), 1)], csc, a * clamp(lift * 3))

    def events(self):
        p = self.p
        return [('sfx', p['field'], 'whoosh', .5, 0, dict(d=.5, f0=400, f1=2400, g=.25)), ('sfx', p['field'] + .55, 'pop', .6, 0, {})]


class QrPeel(Scene):
    """Back at the meter: slow push, zoom to the corner, the corner lifts, then the sticker peels to reveal the real code."""
    name = 'qr_peel'
    TIMES = ('corner', 'peel', 'reveal', 'qr', 'top')
    bg_default = 'navy'
    post = EXIT

    def geo(self, t):
        p = self.p
        k = enter(t, self.start, 0.6)
        g = lerp(0.9, 1.0, k) + 0.06 * P(t, self.start, p['corner'] - self.start)
        gx, gy = CX, 800
        z = eio(P(t, p['corner'] - 0.2, 0.9))
        if z > 0:
            gz = 1.8; gx = lerp(gx, 760 - 180 * gz, z); gy = lerp(gy, 600 + 120 * gz, z); g = lerp(g, gz, z)
        r = eio(P(t, p['reveal'] - 0.1, 0.9))
        if r > 0:
            gr = 1.6; gx = lerp(gx, CX, r); gy = lerp(gy, 830 - S.METER_STICK_DY * gr, r); g = lerp(g, gr, r)
        g *= 1 + 0.03 * P(t, p['reveal'] + 0.8, self.end - p['reveal'])   # keep drifting in during the hold
        d = 0.0
        if t >= p['corner']: d = 40 * eo3(P(t, p['corner'], 0.6))
        if t >= p['peel']: d = lerp(40, 90, eo3(P(t, p['peel'], 0.6)))
        if t >= p['reveal']: d = lerp(90, 330, eio(P(t, p['reveal'], 1.0)))
        return gx, gy, g, d

    def draw(self, b, t):
        p = self.p
        gx, gy, g, d = self.geo(t)
        out = eio(P(t, self.end, EXIT)); a = enter(t, self.start, .5) * (1 - out)
        gy -= 200 * out
        ol = eo3(P(t, p['top'], 0.5)) if t >= p['top'] else 0
        draw_meter(b, gx, gy, g, d, a, ol)
        scrim(b, (9, 15, 32), clamp((g - 1.1) / 0.4) * a)
        cx, cy = stk(gx, gy, g, S.STW - 6, 6)
        ring_pulse(b, t, p['peel'], cx, cy, 50, 200, ORANGE, 1.0)
        if t >= p['qr']:
            qx, qy = stk(gx, gy, g, 255, 110)
            put(b, S.brackets(lerp(200, 160, eo3(P(t, p['qr'], .5))) * g, GREEN), qx, qy, 1.0, a * P(t, p['qr'], .3))
            ring_pulse(b, t, p['qr'] + 0.4, qx, qy, 120, 260, GREEN, 1.0)
        if t >= p['top']:
            tx, ty = stk(gx, gy, g, 120, 400)
            put(b, S.tag('TOP STICKER', RED, size=34), tx, ty + 70 + 20 * (1 - eo3(P(t, p['top'], .5))), 1.0, a * P(t, p['top'], .4), -3)

    def events(self):
        p = self.p
        return [('sfx', self.start, 'whoosh', .5, 0, dict(d=.6, f0=1500, f1=300, g=.25)),
                ('sfx', p['corner'] - .2, 'whoosh', .4, 0, dict(d=.8, f0=300, f1=1200, g=.2)),
                ('sfx', p['corner'], 'pop', .4, 0, dict(p=.7)), ('sfx', p['peel'], 'pop', .5, 0, dict(p=.8)),
                ('sfx', p['reveal'], 'thud', .7, 0, dict(g=.6)), ('sfx', p['reveal'] + .05, 'whoosh', .5, 0, dict(d=.8, f0=2000, f1=500, g=.25)),
                ('punch', p['reveal'], .03), ('sfx', p['qr'], 'ping', .7, 0, {}),
                ('sfx', p['top'], 'buzz', .5, 0, {}), ('punch', p['top'], .015)]


class QrFake(Scene):
    """The phone returns with the fake page; the web address lifts out big and gets a FAKE stamp."""
    name = 'qr_fake'
    TIMES = ('lift', 'stamp')
    bg_default = 'purple'
    post = EXIT

    def draw(self, b, t):
        p = self.p
        k = enter(t, self.start, 0.6); out = eio(P(t, self.end, EXIT))
        lift = eio(P(t, p['lift'], 0.8))
        sc = lerp(1.0, 0.68, lift); y = lerp(PHY + 250 * (1 - k), 990, lift)
        a = clamp(k * 1.5) * (1 - out)
        draw_phone(b, PHX, y - 120 * out, sc, S.pay_screen(1, 0, 0, lerp(0.3, 1, lift), False), a)
        if lift > 0:
            ux, uy = scr(PHX, y, sc, 200, 94)
            cy = lerp(uy, 470, lift) - 120 * out
            draw_card(b, CX, cy, CW_, 230, 34, CARD, [(url_callout(lift), 1)], lerp(0.45, 1.0, lift), a * clamp(lift * 3))
            if t >= p['stamp']:
                q = P(t, p['stamp'], 0.3)
                put(b, S.stamp('FAKE', 100), CX + 250, cy + 150, lerp(1.35, 1.0, eo3(q)) * (1 + 0.02 * math.sin((t - p['stamp']) * 2)), a * clamp(q * 2), -7)

    def events(self):
        p = self.p
        return [('sfx', self.start, 'whoosh', .5, 0, dict(d=.6, f0=300, f1=1500, g=.25)),
                ('sfx', p['lift'], 'whoosh', .5, 0, dict(d=.6, f0=400, f1=2400, g=.25)), ('sfx', p['lift'] + .6, 'pop', .6, 0, {}),
                ('sfx', p['stamp'], 'stamp', .7, 0, {}), ('punch', p['stamp'], .04), ('shake', p['stamp'], 6, .2)]


class QrCapture(Scene):
    """Card number types in big; the digits drift down into the scammer's card; then the meter is still unpaid."""
    name = 'qr_capture'
    TIMES = ('type_end', 'scammer', 'details', 'status', 'unpaid')
    bg_default = 'redwarn'
    post = EXIT

    def draw(self, b, t):
        p = self.p
        k = enter(t, self.start, 0.55); out = eio(P(t, self.end, EXIT))
        sw = eio(P(t, p['status'], 0.8))                       # swap to the status card
        n = int(16 * P(t, self.start + 0.5, p['type_end'] - self.start - 0.5))
        a1 = clamp(k * 1.5) * (1 - sw)
        y1 = lerp(470, 520, eio(P(t, p['scammer'] - 0.1, 0.7))) + 60 * (1 - k) - 200 * sw
        draw_card(b, CX, y1, CW_, 250, 34, CARD, [(number_callout(n, int(t * 2.2) % 2 == 0), 1)], 1.0, a1)
        if t >= p['scammer']:
            ys = 1000 - 200 * sw; q = ein(t, p['scammer'] + 0.2, 0.6)
            rows = 0
            for i, c in enumerate(['4821', '7730', '1956', '0042']):
                t0 = p['scammer'] + 0.35 + i * 0.16; e = eio(P(t, t0, 0.8))
                if e >= 1: rows = 1
                if 0 < e < 1:
                    fx = CX - 300 + i * 150; fy = y1 + 30
                    put(b, S.chip(c), lerp(fx, CX - 120 + i * 80, e), lerp(fy, ys - 60, e), 1.0 - 0.3 * e, a1 * (1 - e * 0.6))
            if t >= p['details']: rows = 1 + int(P(t, p['details'], 0.7) * 2.99)
            draw_card(b, CX, ys + 40 * (1 - q), CW_, 420, 34, (24, 14, 26), [(scam_big(rows), 1)], 1.0, q * (1 - sw))
        if sw > 0:
            pulse = 0.5 + 0.5 * math.sin((t - p['unpaid']) * 4) if t >= p['unpaid'] else 0
            y = lerp(1100, 780, sw) - 120 * out
            draw_card(b, CX, y, CW_, 440, 38, CARD, [(status_big(P(t, p['status'] + .3, .8), pulse), 1)], 1.0, sw * (1 - out))
            if t >= p['unpaid']:
                q = P(t, p['unpaid'], 0.3)
                put(b, S.stamp('UNPAID', 120), CX, y + 290, lerp(1.35, 1.0, eo3(q)), clamp(q * 2) * (1 - out), 5)

    def events(self):
        p = self.p
        ev = [('sfx', self.start, 'whoosh', .5, 0, dict(d=.6, f0=300, f1=1500, g=.25))]
        for i in range(16):
            ev.append(('sfx', self.start + 0.5 + (p['type_end'] - self.start - 0.5) * i / 16, 'tap', .35, 0, {}))
        ev += [('sfx', p['scammer'] + .2, 'whoosh', .5, 0, dict(d=.6, f0=1500, f1=400, g=.25))]
        for i in range(4): ev.append(('sfx', p['scammer'] + 1.15 + i * .16, 'coin', .3, 0, {}))
        ev += [('sfx', p['details'], 'buzz', .45, 0, {}),
               ('sfx', p['status'], 'whoosh', .5, 0, dict(d=.6, f0=300, f1=1500, g=.25)),
               ('sfx', p['unpaid'], 'stamp', .75, 0, {}), ('punch', p['unpaid'], .05), ('shake', p['unpaid'], 8, .25)]
        return ev


class QrCovered(Scene):
    """The sticker again with a dashed outline and magnifier; then the phone: tap X, the page closes."""
    name = 'qr_covered'
    TIMES = ('covered', 'phone', 'close')
    bg_default = 'paper'
    post = EXIT

    def draw(self, b, t):
        p = self.p
        k = enter(t, self.start, 0.6); out = eio(P(t, self.end, EXIT))
        mx = eio(P(t, p['phone'], 0.4))          # meter clears first
        ph = eio(P(t, p['phone'] + 0.3, 0.6))    # then the phone rises
        g = 1.45 + 0.05 * P(t, self.start, p['phone'] - self.start)
        gx = CX; gy = 820 - S.METER_STICK_DY * g + 120 * (1 - k) - 260 * mx
        if mx < 1:
            draw_meter(b, gx, gy, g, 70, k * (1 - mx), 0, eo3(P(t, p['covered'], .5)) if t >= p['covered'] else 0)
            if t >= p['covered']:
                cx, cy = stk(gx, gy, g, S.STW - 40, 40)
                put(b, S.magnifier(), cx + 40, cy + 40, soft_pop(t, p['covered'] + .2, .5), 1 - mx)
            scrim(b, BGC['paper'][1], k * (1 - mx))
        if t >= p['phone'] + 0.3:
            y = lerp(1500, 860, ph) - 120 * out
            a = clamp(ph * 1.5) * (1 - out)
            xb = soft_pop(t, p['close'], .4)
            col = eio(P(t, p['close'] + .45, 0.4))
            sc = 1.0
            pay = S.pay_screen(1, 0, 0, 1, False, xb)
            closed = S.closed_screen(P(t, p['close'] + .65, .4))
            def ex():
                X, Y = scr(PHX, y, sc, S.SW - 52, 94)
                if col > 0: put(b, pay, lerp(PHX, X, col), lerp(y, Y, col), 1 - 0.85 * col, a * (1 - col))
                if t >= p['close'] + .25: put(b, S.ripple(P(t, p['close'] + .25, .5)), X, Y, 1.0, a)
            draw_phone(b, PHX, y, sc, closed if col > 0 else pay, a, ex)

    def events(self):
        p = self.p
        return [('sfx', self.start, 'whoosh', .5, 0, dict(d=.6, f0=300, f1=1500, g=.25)),
                ('sfx', p['covered'] + .2, 'pop', .6, 0, {}),
                ('sfx', p['phone'], 'whoosh', .5, 0, dict(d=.6, f0=300, f1=1500, g=.25)),
                ('sfx', p['close'], 'pop', .6, 0, dict(p=1.2)), ('sfx', p['close'] + .25, 'tap', .9, 0, {}),
                ('sfx', p['close'] + .45, 'whoosh', .4, 0, dict(d=.4, f0=2000, f1=400, g=.2)), ('sfx', p['close'] + .65, 'chime', .7, 0, {})]


class QrLookup(Scene):
    """Big search bar, then two large result cards: the official app and the city website."""
    name = 'qr_lookup'
    TIMES = ('typed', 'official', 'web', 'yourself')
    bg_default = 'paper'
    post = EXIT

    def draw(self, b, t):
        p = self.p
        k = enter(t, self.start, 0.55); out = eio(P(t, self.end, EXIT))
        a = k * (1 - out); dy = 80 * (1 - k) - 120 * out
        nq = int(len(S.QUERY) * P(t, self.start + .3, p['typed'] - self.start - .3))
        draw_card(b, CX, 470 + dy, CW_, 130, 65, WHITE, [(search_bar(nq), 1)], 1.0, a)
        r1 = ein(t, p['official'] - .45, .6)
        if r1 > 0:
            draw_card(b, CX, 720 + 50 * (1 - r1) + dy, CW_, 250, 34, WHITE,
                      [(result_app(P(t, p['official'], .5), P(t, p['yourself'], .4)), 1)], 1.0, a * r1,
                      border=GREEN if t >= p['yourself'] else None)
        r2 = ein(t, p['web'] - .2, .6)
        if r2 > 0:
            draw_card(b, CX, 985 + 50 * (1 - r2) + dy, CW_, 200, 34, WHITE, [(result_web(), 1)], 1.0, a * r2)

    def events(self):
        p = self.p
        ev = [('sfx', self.start, 'whoosh', .5, 0, dict(d=.6, f0=300, f1=1500, g=.25))]
        for i in range(10): ev.append(('sfx', self.start + .3 + (p['typed'] - self.start - .3) * i / 10, 'tap', .3, 0, {}))
        ev += [('sfx', p['official'] - .45, 'pop', .6, 0, {}), ('sfx', p['official'], 'coin', .4, 0, {}),
               ('sfx', p['web'] - .2, 'pop', .6, 0, dict(p=1.15)), ('sfx', p['yourself'], 'tap', .9, 0, {}),
               ('sfx', p['yourself'] + .05, 'chime', .8, 0, {}), ('punch', p['yourself'], .015)]
        return ev


class QrChecklist(Scene):
    """Calm close: a title, then three check rows that stay on screen long enough to read twice."""
    name = 'qr_checklist'
    TIMES = ('rows',)
    DEFAULTS = dict(title=['BEFORE', 'YOU', 'PAY'], accent='PAY',
                    items=['Check the web address', 'Sticker on top? Skip it', 'Use the official app'])
    bg_default = 'navy'
    hide_bug = True
    post = EXIT

    def draw(self, b, t):
        p = self.p
        out = eio(P(t, self.end, EXIT)); a = 1 - out
        f = F('Black', 112 * SS, True); sp = f.getlength(' ') / SS
        ws = [f.getlength(w) / SS for w in p['title']]; tot = sum(ws) + sp * (len(ws) - 1); x = CX - tot / 2
        for i, (w, wd) in enumerate(zip(p['title'], ws)):
            q = eo3(P(t, self.start + DELAY + 0.1 + i * 0.22, 0.4))
            put(b, label_spr(w, ('Black', 112, True), ORANGE if w == p['accent'] else WHITE), x + wd / 2, 470 + 30 * (1 - q) - 100 * out, 1.0, q * a)
            x += wd + sp
        c = ein(t, p['rows'][0] - .35, .6)
        if c > 0:
            cont = canvas(CW_, 460)
            for i, (txt, t0) in enumerate(zip(p['items'], p['rows'])):
                spr = check_row(txt, P(t, t0, .5))
                cont.alpha_composite(spr, (0, int((40 + i * 130) * SS)))
            draw_card(b, CX, 860 + 50 * (1 - c) - 100 * out, CW_, 460, 38, CARD, [(cont, 1)], 1.0, c * a)

    def events(self):
        p = self.p
        ev = [('sfx', self.start + DELAY + .1 + i * .22, 'thud', .45, 0, dict(g=.5)) for i in range(len(p['title']))]
        ev.append(('sfx', p['rows'][0] - .35, 'whoosh', .4, 0, dict(d=.5, f0=300, f1=1500, g=.2)))
        for i, t0 in enumerate(p['rows']): ev += [('sfx', t0, 'pop', .6, 0, dict(p=1 + .1 * i)), ('sfx', t0 + .1, 'chime', .35, 0, {})]
        return ev
