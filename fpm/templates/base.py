"""Template base classes.

A scene = one template instance placed on the timeline by the beat sheet.
  start  : resolved time the scene begins (its intro or morph starts here)
  end    : the next scene's start (or the episode end)
  p      : params; any key listed in TIMES is resolved as a time anchor
Scenes report events (sfx, punch, shake, flash, blur, creep) so sound and camera
always come from the same timing table as the picture.

Handoffs
  exit_card()  -> dict describing the card this scene leaves on screen
                  (x, y, w, h, r, fill, border, sc, content, overlay)
  takes_prev   -> True if this scene consumes the previous scene's card
                  (morphs from it, pins it, or turns it into something else).
                  The previous scene then stops drawing at this scene's start.
"""
from ..engine import *
from ..sprites import *


class Scene:
    name = 'scene'
    TIMES = ()          # param keys that are time anchors
    DEFAULTS = {}
    bg_default = None
    hide_bug = False
    hide_captions = False
    post = 0.45         # how long the scene keeps drawing after its end (exit animation)
    takes_prev = False

    def __init__(self, spec, tl):
        self.tl = tl
        self.spec = spec
        self.start = tl.time(spec['start'])
        self.end = None
        self.p = dict(self.DEFAULTS)
        self.p.update(spec.get('p', {}))
        self.bg = spec.get('bg', self.bg_default)
        self.bg_from = spec.get('bg_from')
        self.prev = self.next = None
        self.src = None   # previous scene's exit card when takes_prev

    # ---- lifecycle
    def resolve(self):
        for k in self.TIMES:
            v = self.p.get(k)
            if v is None: continue
            self.p[k] = [self.tl.time(x) for x in v] if isinstance(v, list) else self.tl.time(v)
        if self.takes_prev and self.prev is not None:
            self.src = self.prev.exit_card()
            if self.src is None: self.takes_prev_effective = False
        self.setup()

    def setup(self): pass

    def handed_off(self):
        return self.next is not None and getattr(self.next, 'takes_prev', False) and self.next.src is not None

    def until(self):
        return self.next.start if self.handed_off() else self.end + self.post

    def active(self, t): return self.start - 0.001 <= t <= self.until()

    def draw(self, b, t): pass
    def events(self): return []
    def exit_card(self): return None
    def bg_origin(self): return (CX, CY)

    # helpers
    def q(self, key, dur, t):
        v = self.p.get(key)
        return 0.0 if v is None else P(t, v, dur)


class CardScene(Scene):
    """One card on screen. Subclasses implement card(t) and content(t).
    Intro: morph from the previous card if takes_prev, else enter animation.
    Exit: if the next scene takes the card it stops at next.start, else exit animation."""
    MORPH = 0.34
    enter = 'rise'       # rise | drop | slide_right | pop | none
    exit = 'fall'        # fall | drop | slide_left | fade | shrink
    takes_prev = True    # card scenes morph from a previous card by default

    def __init__(self, spec, tl):
        super().__init__(spec, tl)
        self.enter = spec.get('enter', self.p.get('enter', self.enter))
        self.exit = spec.get('exit', self.p.get('exit', self.exit))
        if 'morph' in spec: self.takes_prev = bool(spec['morph'])

    def card(self, t):
        return dict(x=CX, y=820, w=CW, h=600, r=38, fill=CARD, border=None, a=1.0, sc=1.0)

    def content(self, t): return canvas(CW, 10)
    def overlay(self, b, t, c): pass

    def geom(self, t):
        c = dict(self.card(t)); c.setdefault('a', 1.0); c.setdefault('sc', 1.0); c.setdefault('border', None)
        cont = [(self.content(t), 1.0)]
        src = self.src
        if src is not None and t < self.start + self.MORPH:
            m = eio(P(t, self.start, self.MORPH))
            for k in ('x', 'y', 'w', 'h', 'r', 'sc'): c[k] = lerp(src[k], c[k], m)
            c['fill'] = lerpc(src['fill'], c['fill'], m)
            c['border'] = c['border'] if m > .5 else src.get('border')
            cont = [(src['content'], 1 - clamp(m * 2.2)), (cont[0][0], clamp(m * 2 - 1))]
        elif src is None and self.enter != 'none':
            k = spring(t - self.start, 1.7, 7)
            if self.enter == 'rise': c['y'] = lerp(1750, c['y'], k)
            elif self.enter == 'drop': c['y'] = lerp(-420, c['y'], k)
            elif self.enter == 'slide_right': c['x'] = lerp(1700, c['x'], k)
            elif self.enter == 'pop': c['sc'] *= 0.55 + 0.45 * k
            c['a'] *= clamp((t - self.start) / .08)
        te = self.end - self.spec.get('exit_lead', 0)
        if not self.handed_off() and t > te:
            qx = P(t, te, 0.26)
            if self.exit == 'fall': c['y'] += 1400 * qx * qx
            elif self.exit == 'drop': c['y'] += 1300 * qx * qx
            elif self.exit == 'slide_left': c['x'] -= 1150 * eio(qx)
            elif self.exit == 'fade': c['a'] *= 1 - qx
            elif self.exit == 'shrink': c['sc'] *= 1 - 0.15 * qx; c['a'] *= 1 - qx
        return c, cont

    def draw(self, b, t):
        c, cont = self.geom(t)
        draw_card(b, c['x'], c['y'], c['w'], c['h'], c['r'], c['fill'], cont, c['sc'], c['a'], border=c['border'])
        self.overlay(b, t, c)

    def exit_card(self):
        t = self.end
        c = dict(self.card(t)); c.setdefault('sc', 1.0); c.setdefault('border', None)
        c['content'] = self.content(t)
        c['overlay'] = getattr(self, 'pinned_overlay', None)
        return c

    def intro_events(self):
        """Default whoosh for a card arriving without a morph."""
        if self.src is not None:
            return [('sfx', self.start, 'whoosh', .7, 0, dict(d=.3, f0=500, f1=3000, g=.3))]
        return [('sfx', self.start, 'whoosh', .8, 0, dict(d=.35, f0=300, f1=2500))]


def draw_pinned(b, src, t, t0, sc_to=0.6, y_to=560, dur=.42, dy_extra=0.0, a=1.0):
    """Draw a previous scene's card shrinking into a pinned slot at the top."""
    m = eio(P(t, t0, dur))
    sc = lerp(src['sc'], sc_to, m); y = lerp(src['y'], y_to, m) + dy_extra
    x = src['x']
    draw_card(b, x, y, src['w'], src['h'], src['r'], src['fill'], [(src['content'], 1)], sc, a, border=src.get('border'))
    if src.get('overlay'): src['overlay'](b, x, y, sc, a)
    return x, y, sc
