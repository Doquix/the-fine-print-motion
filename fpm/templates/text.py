from .base import *


class KineticLine(Scene):
    """Big kinetic line, word by word slams (Inter Display Black). lines: [["Never","pay"],["to","get","paid."]].
    accent: words drawn in orange. times: optional explicit word times, else spread over the first 55% of the scene."""
    name = 'kinetic_line'
    TIMES = ('times', 'underline')
    DEFAULTS = dict(lines=[['Never', 'pay'], ['to', 'get', 'paid.']], accent=['paid.'], size=156, underline=None, spread=0.55)
    bg_default = 'navy'
    hide_bug = True
    hide_captions = True
    post = 0.0

    def setup(self):
        p = self.p
        words = [w for ln in p['lines'] for w in ln]
        if not p.get('times'):
            span = (self.end - self.start) * p['spread']
            chars = [len(w) + 1 for w in words]; tot = sum(chars); acc = 0; ts = []
            for c in chars: ts.append(self.start + span * acc / tot); acc += c
            p['times'] = ts
        if p.get('underline') is None: p['underline'] = p['times'][-1] + .22
        self.words = words

    def until(self): return self.end + .3

    def draw(self, b, t):
        p = self.p
        size = p['size']; fa = ('Black', size, True); f = F('Black', size * SS, True)
        sp = f.getlength(' ') / SS
        out = eio(P(t, self.end - .14, .22))
        i = 0
        nlines = len(p['lines'])
        top = 790 - (nlines - 1) * 175 / 2
        for li, ln in enumerate(p['lines']):
            widths = [f.getlength(w) / SS for w in ln]
            total = sum(widths) + sp * (len(ln) - 1)
            x = CX - total / 2; y = top + li * 175 - out * 260
            for w, wd in zip(ln, widths):
                t0 = p['times'][i]
                if t >= t0:
                    q = P(t, t0, .16)
                    col = ORANGE if w in p['accent'] else WHITE
                    put(b, label_spr(w, fa, col), x + wd / 2, y, lerp(1.6, 1, eo3(q)) * (1 - .3 * out), clamp(q * 4) * (1 - out))
                x += wd + sp; i += 1
            if li == nlines - 1 and t >= p['underline']:
                q = eo3(P(t, p['underline'], .3))
                ul = canvas(total, 14); Pen(ul).rr(0, 0, total * q, 14, 7, fill=ORANGE)
                put(b, ul, CX, y + 100, 1, 1 - out)

    def events(self):
        p = self.p
        ev = []
        for i, tw in enumerate(p['times']):
            ev += [('sfx', tw, 'thud', .7, 0, dict(g=.55)), ('sfx', tw, 'tick', .4, 0, dict(p=.7 + .1 * i)), ('punch', tw, .015)]
        ev.append(('sfx', p['underline'], 'whoosh', .7, 0, dict(d=.25, f0=2000, f1=6000, g=.2)))
        return ev


class LogoOutro(Scene):
    """Logo icon pop with ring, staggered wordmark, tagline, then a zoom and fade to navy for a clean loop."""
    name = 'logo_outro'
    TIMES = ('tag',)
    DEFAULTS = dict(title='THE FINE PRINT', tagline='The hidden cost of everything.', zoom=0.38)
    bg_default = 'navy'
    hide_bug = True
    hide_captions = True
    post = 0.0

    def until(self): return self.end + 1

    def draw(self, b, t):
        p = self.p; L = self.start + .06
        k = P(t, L, .38)
        put(b, logo_icon(), CX, 700, 0.4 + 0.6 * eoback(k), clamp(k * 4))
        if t < L + .8:
            q = P(t, L, .7)
            ring = canvas(600, 600); Pen(ring).circ(300, 300, 150 + 140 * eo3(q), outline=(245, 166, 35, int(200 * (1 - q))), width=6)
            put(b, ring, CX, 700)
        fa = ('Black', 92, True); f = F('Black', 92 * SS, True); spc = 6
        txt = p['title']
        tw = sum(f.getlength(c) for c in txt) / SS + spc * (len(txt) - 1)
        x = CX - tw / 2
        for i, c in enumerate(txt):
            cw = f.getlength(c) / SS
            q = eo3(P(t, L + .06 + i * .028, .22))
            if c != ' ' and q > 0: put(b, label_spr(c, fa, WHITE), x + cw / 2, 930 + 50 * (1 - q), 1, q)
            x += cw + spc
        if p.get('tag') is not None:
            q = eo3(P(t, p['tag'], .4))
            put(b, label_spr(p['tagline'], ('Medium', 42), (170, 182, 206)), CX, 1015 + 30 * (1 - q), 1, q)

    def events(self):
        p = self.p; L = self.start; z0 = self.end - p['zoom']
        ev = [('sfx', L, 'whoosh', .6, 0, dict(d=.3, f0=3000, f1=400, g=.3)), ('sfx', L + .05, 'chime', .9, 0, {}),
              ('sfx', z0, 'whoosh', 1.0, 0, dict(d=.4, f0=300, f1=4000, g=.45)), ('zoom', z0, self.end)]
        if p.get('tag') is not None: ev.append(('sfx', p['tag'], 'shimmer', .7, 0, dict(d=1.0)))
        return ev
