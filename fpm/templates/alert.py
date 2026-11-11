from .base import *
from .phone import DEFAULTS_MODAL


class BlockModal(Scene):
    """Standalone alert modal (use for callbacks). level 1 neutral, 2 red text, 3 red text plus STOP stamp and cracks.
    creep: slow camera push from that time until the stamp. Exit zoom_through flies the camera through the card."""
    name = 'block_modal'
    TIMES = ('magnifier', 'stop', 'creep')
    DEFAULTS = dict(level=3, word='STOP', exit='zoom_through', modal=None, hide_stop_caption=True)
    bg_default = 'redwarn'
    post = 0.25

    def setup(self):
        self.m = dict(DEFAULTS_MODAL); self.m.update(self.p.get('modal') or {})

    def draw(self, b, t):
        p = self.p
        k = spring(t - self.start - .05, 1.8, 7)
        zoom = ei3(P(t, self.end - .08, .2)) if p['exit'] == 'zoom_through' else 0
        fade = P(t, self.end, .25) if p['exit'] == 'fade' else 0
        sc = (0.55 + 0.45 * k) * (1 + 2.5 * zoom)
        a = clamp((t - self.start - .05) / .08) * (1 - zoom) * (1 - fade)
        y = 820 + (1 - k) * 60
        lvl = min(p['level'], 2)
        spr = modal_spr(lvl, 1, 1 if lvl >= 2 else 0, self.m['tag'], self.m['title'], self.m['sub'], self.m['red_sub'])
        draw_card(b, CX, y, MW, MH, 40, CARD, [(spr, 1)], sc, a)
        st = p.get('stop')
        if p['level'] >= 3 and st is not None and t >= st - .1:
            if t >= st: put(b, crack_spr(eo3(P(t, st, .14))), CX, y, sc, a)
            q = P(t, st - .1, .1)
            put(b, stamp_spr(p['word']), CX, y + 10, lerp(2.8, 1.2, ei3(q)) * sc, clamp(q * 3) * (1 - zoom) * (1 - fade), -8)
        mg = p.get('magnifier')
        if mg is not None and t >= mg:
            q = eo3(P(t, mg, .45)); kick = ei3(P(t, st, .4)) if st is not None else 0
            mx = lerp(1250, 790, q) + 14 * math.sin(t * 2.6) + kick * 700
            my = lerp(1150, 905, q) + 10 * math.cos(t * 2.1) - kick * 300
            put(b, magnifier_spr(), mx, my, 1, a, kick * -200)

    def events(self):
        p = self.p; s = self.start
        ev = [('sfx', s, 'whoosh', .9, 0, dict(d=.4, f0=200, f1=1500, g=.4)), ('sfx', s + .05, 'thud', .8, 0, dict(g=.8)),
              ('punch', s + .05, .03)]
        if p.get('magnifier') is not None: ev.append(('sfx', p['magnifier'], 'whoosh', .7, .5, dict(d=.3, f0=1000, f1=4000, g=.25)))
        st = p.get('stop')
        if p['level'] >= 3 and st is not None:
            ev += [('sfx', st - 1.7, 'riser', .9, 0, dict(d=1.7)), ('sfx', st, 'hit', 1.0, 0, {}), ('punch', st, .12),
                   ('shake', st, 30, .45), ('flash', st, RED, .45, .5)]
            if p.get('creep') is not None: ev.append(('creep', p['creep'], st, self.end, .07))
        if p['exit'] == 'zoom_through':
            ev += [('sfx', self.end - .1, 'whoosh', .9, 0, dict(d=.3, f0=500, f1=4000, g=.4)), ('blur', self.end - .08, .2, 40)]
        return ev
