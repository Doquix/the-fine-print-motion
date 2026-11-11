from .base import *


class PhoneTap(Scene):
    """Phone showing a balance; a tap on the main button; optional alert modal that pops over it.
    level 1: neutral modal with an underline. level 2: red text swap plus magnifier (escalation).
    exit: whip_up (phone and modal fly up with motion blur) | handoff (modal is handed to the next
    scene, phone fades) | fade."""
    name = 'phone_tap'
    TIMES = ('tap', 'block', 'underline', 'red', 'magnifier')
    DEFAULTS = dict(balance='$100.00', button='Withdraw', title='TASK DASHBOARD', rows=None,
                    enter='spring', exit='whip_up', level=1,
                    modal=dict(tag='WITHDRAWAL BLOCKED', title='Deposit required',
                               sub='Add funds to withdraw', red_sub='Deposit $100.00 to unlock'))
    bg_default = 'navy'
    post = 0.3

    def setup(self):
        p = self.p
        self.rows = p['rows'] or DEFAULT_ROWS
        self.m = dict(DEFAULTS_MODAL); self.m.update(p.get('modal') or {})

    def until(self):
        return self.end + self.post

    def phone_geom(self, t):
        p = self.p
        if p['enter'] == 'spring':
            intro = spring(t - self.start + 0.12, 1.6, 6); rot = -9 * (1 - intro)
            psc = 0.86 + 0.06 * intro; y = 840
        else:
            k = spring(t - self.start, 1.5, 6); rot = 10 * (1 - k); psc = 0.92; y = lerp(2000, 840, k)
        dimp = eo3(P(t, p['block'], .25)) if p.get('block') is not None else 0
        psc -= 0.06 * dimp
        a = 1.0; dy = 0.0
        if t > self.end:
            q = P(t, self.end, .25)
            if p['exit'] == 'whip_up': dy = -1300 * ei3(q)
            else: psc *= 1 - 0.2 * q; a = 1 - q
        return y + dy, psc, rot, dimp, a, dy

    def modal_sprite(self, t):
        p = self.p
        ul = eo3(P(t, p['underline'], .35)) if p.get('underline') is not None else (eo3(P(t, p['block'] + .25, .3)) if p['level'] >= 2 else 0)
        hl = eo3(P(t, p['red'], .3)) if p.get('red') is not None else 0
        return modal_spr(p['level'], ul, hl, self.m['tag'], self.m['title'], self.m['sub'], self.m['red_sub'])

    def draw(self, b, t):
        p = self.p
        y, psc, rot, dimp, a, dy = self.phone_geom(t)
        tap = p.get('tap')
        press = clamp(1 - abs(t - tap - .06) / .09) if tap is not None and tap - .05 < t < tap + .2 else 0
        put(b, shadow_spr(PW, PH, 86), CX, y + 30, psc, a, rot, ss=.25)
        put(b, phone_spr(press, dimp, p['balance'], p['button'], p['title'], self.rows), CX, y, psc, a, rot)
        if tap is not None and tap <= t < tap + .5:
            put(b, ripple_spr(P(t, tap, .5)), CX, y + (PHONE_BUTTON_Y - PH / 2) * psc, psc)
        blk = p.get('block')
        modal_on = blk is not None and t >= blk and not (self.handed_off() and t >= self.end)
        if modal_on:
            k = spring(t - blk, 1.8, 7)
            draw_card(b, CX, 800 + (1 - k) * 60 + dy, MW, MH, 40, CARD, [(self.modal_sprite(t), 1)],
                      0.55 + 0.45 * k, clamp((t - blk) / .08))
        mg = p.get('magnifier')
        if mg is not None and t >= mg and not (self.handed_off() and t >= self.end):
            q = eo3(P(t, mg, .4))
            mx = lerp(1250, 780, q) + 12 * math.sin(t * 3); my = lerp(1100, 885, q) + 8 * math.cos(t * 2.4) + dy
            put(b, magnifier_spr(), mx, my, 1.0, a if not self.handed_off() else 1)

    def exit_card(self):
        if self.p.get('block') is None: return None
        return dict(x=CX, y=800, w=MW, h=MH, r=40, fill=CARD, border=None, sc=1.0,
                    content=self.modal_sprite(self.end), overlay=None)

    def events(self):
        p = self.p; ev = []
        if p['enter'] == 'spring': ev.append(('sfx', self.start, 'thud', .7, 0, dict(g=.6)))
        else: ev.append(('sfx', self.start + .05, 'whoosh', .8, 0, dict(d=.35, f0=200, f1=1800, g=.35)))
        if p.get('tap') is not None: ev.append(('sfx', p['tap'], 'tap', 1.0, 0, {}))
        if p.get('block') is not None:
            b0 = p['block']
            ev += [('sfx', b0, 'buzz', .9, 0, {}), ('sfx', b0, 'thud', .8, 0, {}), ('punch', b0, .05),
                   ('shake', b0, 16, .3), ('flash', b0, RED, .28, .35)]
        if p.get('underline') is not None: ev.append(('sfx', p['underline'], 'whoosh', .7, 0, dict(d=.18, f0=2000, f1=6000, g=.2)))
        if p.get('magnifier') is not None: ev.append(('sfx', p['magnifier'], 'whoosh', .7, .5, dict(d=.3, f0=1000, f1=4000, g=.25)))
        if p.get('red') is not None: ev += [('sfx', p['red'], 'glitch', .9, 0, {}), ('sfx', p['red'], 'thud', .6, 0, dict(g=.6)), ('punch', p['red'], .07)]
        if p['exit'] == 'whip_up':
            ev += [('sfx', self.end - .08, 'whoosh', 1.0, 0, dict(d=.4, f0=250, f1=4000)), ('blur', self.end, .3, 60)]
        return ev


DEFAULTS_MODAL = dict(tag='WITHDRAWAL BLOCKED', title='Deposit required',
                      sub='Add funds to withdraw', red_sub='Deposit $100.00 to unlock')
