from .base import *


class TrustPayment(Scene):
    """Pins the previous card small at the top, then a payment notification and a filling meter (trust, credit...)."""
    name = 'trust_payment'
    TIMES = ('notif', 'small', 'meter_in', 'meter')
    DEFAULTS = dict(title='Payment received', amount='$5.00', rest='sent to your bank', meter_label='Your trust',
                    meter_from=0.12, meter_to=0.92)
    bg_default = 'green'
    takes_prev = True
    post = 0.5

    def setup(self):
        p = self.p
        p.setdefault('notif', self.start + .12)

    def bg_origin(self): return (CX, 560)

    def draw(self, b, t):
        p = self.p
        fall = P(t, self.end - self.spec.get('exit_lead', 0.3), .32)
        def fy(d=0): return 1500 * clamp(fall * 1.2 - d) ** 2
        if self.src is not None:
            draw_pinned(b, self.src, t, self.start, dy_extra=fy())
        k = spring(t - p['notif'], 1.8, 7)
        sm = p.get('small')
        bump = 1 + 0.04 * math.sin(math.pi * P(t, sm, .25)) if sm is not None else 1
        hl = eo3(P(t, sm, .3)) if sm is not None else 0
        ring = P(t, sm, .9) if sm is not None and t >= sm else 0
        draw_card(b, CX, lerp(1500, 890, k) + fy(.08), CW, 180, 36, CARD,
                  [(notif_content(hl, ring, p['title'], p['amount'], p['rest']), 1)], bump, clamp((t - p['notif']) / .1))
        mi = p.get('meter_in')
        if mi is not None and t >= mi:
            k2 = spring(t - mi, 1.8, 7)
            f = lerp(p['meter_from'], p['meter_to'], eo3(P(t, p['meter'], .7))) if p.get('meter') is not None else p['meter_from']
            draw_card(b, CX, lerp(1500, 1120, k2) + fy(.16), CW, 190, 36, CARD, [(meter_content(f, p['meter_label']), 1)], 1, clamp((t - mi) / .1))

    def events(self):
        p = self.p
        ev = [('sfx', self.start, 'whoosh', .8, 0, dict(d=.35, f0=300, f1=2500)), ('sfx', p['notif'] + .05, 'ping', 1.0, 0, {})]
        if p.get('small') is not None: ev += [('sfx', p['small'], 'chime', .9, 0, {}), ('punch', p['small'], .02)]
        if p.get('meter') is not None: ev += [('sfx', p['meter'] + i * .085, 'tick', .5, 0, dict(p=1.2 + i * .08)) for i in range(8)]
        ev.append(('sfx', self.end - self.spec.get('exit_lead', 0.3), 'whoosh', 1.0, 0, dict(d=.45, f0=3000, f1=200, g=.5)))
        return ev


class MoneyFlow(Scene):
    """Pins the previous card at the top, a label, two mini wallets, and a coin that travels left to right."""
    name = 'money_flow'
    TIMES = ('send',)
    DEFAULTS = dict(label='THE ONLY REAL MONEY', left=['Your wallet', '$100.00', '$0.00'],
                    right=["Scammer's wallet", '$0.00', '$100.00'])
    bg_default = None
    takes_prev = True
    post = 0.45

    def draw(self, b, t):
        p = self.p
        leave = eio(P(t, self.end, .38)) if not self.handed_off() else 0
        dx = -1150 * leave
        if self.src is not None:
            s = self.src
            m = eio(P(t, self.start, .42))
            sc = lerp(s['sc'], 0.62, m); y = lerp(s['y'], 470, m); x = s['x'] + dx
            draw_card(b, x, y, s['w'], s['h'], s['r'], s['fill'], [(s['content'], 1)], sc, 1, border=s.get('border'))
            if s.get('overlay'): s['overlay'](b, x, y, sc, 1)
        x = CX + dx
        la = eo3(P(t, self.start + .05, .25))
        put(b, label_spr(p['label'], ('Bold', 32), (200, 120, 0), 4), x, 760, 1, la)
        snd = p.get('send')
        sent = snd is not None and t >= snd + .3
        k1 = spring(t - self.start - .1, 1.8, 7); k2 = spring(t - self.start - .2, 1.8, 7)
        fl = clamp(1 - P(t, snd + .33, .6)) if sent else 0
        L, R2 = p['left'], p['right']
        lw = mini_wallet(L[0], L[2] if sent else L[1], RED if sent else WHITE)
        rw = mini_wallet(R2[0], R2[2] if sent else R2[1], (110, 230, 160) if sent else (150, 160, 180), fl)
        draw_card(b, x - 225, lerp(1500, 950, k1), 410, 250, 34, DARKCARD, [(lw, 1)], 1, clamp(k1 * 3))
        draw_card(b, x + 225, lerp(1500, 950, k2), 410, 250, 34, DARKCARD, [(rw, 1)], 1, clamp(k2 * 3))
        if snd is not None and snd <= t < snd + .45:
            q = eio(P(t, snd, .33))
            for j in range(5, -1, -1):
                qq = clamp(q - j * 0.05)
                put(b, coin_spr(), lerp(x - 225, x + 225, qq), 950 - 190 * math.sin(math.pi * qq), 0.3,
                    (1 - j / 6) * (1 if q < 1 else 1 - P(t, snd + .33, .1)))

    def events(self):
        s = self.start; ev = [('sfx', s, 'whoosh', .7, 0, dict(d=.3, f0=500, f1=3000, g=.3)),
                              ('sfx', s + .1, 'pop', .7, -.3, dict(p=.9)), ('sfx', s + .2, 'pop', .7, .3, dict(p=1.0))]
        snd = self.p.get('send')
        if snd is not None:
            ev += [('sfx', snd, 'whoosh', 1.0, .2, dict(d=.33, f0=600, f1=5000, g=.4)), ('sfx', snd + .33, 'coin', 1.0, .4, {}),
                   ('punch', snd + .33, .03)]
        return ev


class CoinRequest(Scene):
    """The previous card morphs into a spinning coin (lands face on) with a label. If the next scene is a
    wallet_send, the coin flies into its wallet icon."""
    name = 'coin_request'
    DEFAULTS = dict(label='Crypto requested', sub='Bitcoin shown as an example', glyph='B')
    bg_default = 'amber'
    takes_prev = True
    post = 0.4
    M = 0.28

    def bg_origin(self): return (CX, 760)

    def until(self): return self.end + self.post

    def draw(self, b, t):
        p = self.p
        s = self.src
        if s is not None and t < self.start + self.M:
            m = eio(P(t, self.start, self.M))
            draw_card(b, lerp(s['x'], CX, m), lerp(s['y'], 760, m), lerp(s['w'], 380, m), lerp(s['h'], 380, m),
                      lerp(s['r'], 190, m), lerpc(s['fill'], GOLD, m), [(s['content'], 1 - clamp(m * 3))], 1, 1)
            return
        t0 = self.start + (self.M if s is not None else 0)
        ta = t - t0
        th = 2 * math.pi * eo3(clamp(ta / 1.3)) + 0.35 * math.sin(ta * 3.2) * clamp(ta - 1.0)
        c = math.cos(th)
        into = isinstance(self.next, Scene) and self.next.name == 'wallet_send'
        fly = eio(P(t, self.end, .32)) if into else 0
        out = P(t, self.end, .3) if not into else 0
        y = lerp(760, 930 - 450 / 2 + 72, fly) - 160 * math.sin(math.pi * fly)
        x = lerp(CX, CX - CW / 2 + 84, fly)
        sc = lerp(1, 0.17, fly) * (1 if s is not None else spring(ta, 1.8, 7))
        if fly < 1 and out < 1:
            for j in range(3): put(b, glow_ring_spr((ta * 0.9 + j / 3) % 1), CX, 760, 1, (1 - fly) * (1 - out))
            put(b, coin_spr(c < 0, p['glyph']), x, y, sc, 1 - out, 0, sx=max(0.06, abs(c)))
        la = eo3(P(t, t0 + .1, .3)) * (1 - P(t, self.end, .15))
        put(b, label_spr(p['label'], ('Bold', 66), WHITE), CX, 1040 + 40 * (1 - la), 1, la)
        if p['sub']: put(b, label_spr(p['sub'], ('Medium', 32), (214, 190, 150)), CX, 1110 + 40 * (1 - la), 1, la)

    def events(self):
        s = self.start
        return [('sfx', s, 'whoosh', .8, 0, dict(d=.3, f0=400, f1=3000)), ('sfx', s + .26, 'spin', 1.0, 0, {}),
                ('sfx', s + .3, 'shimmer', .9, 0, dict(d=1.2))]
