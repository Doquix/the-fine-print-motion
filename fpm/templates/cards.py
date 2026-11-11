from .base import *


class NotifChat(CardScene):
    """Notification banner drops in, then expands into a chat card; message bubbles pop in with typing dots."""
    name = 'notif_chat'
    TIMES = ('banner', 'expand', 'bubbles')
    DEFAULTS = dict(sender='Unknown sender', lines=['Easy remote work', 'Flexible hours', 'Quick money'], accent=-1)
    bg_default = 'cream'
    enter = 'none'
    takes_prev = False

    def setup(self):
        p = self.p
        p.setdefault('banner', self.start + .25)
        if p.get('expand') is None: p['expand'] = (p['bubbles'][0] - .2) if p.get('bubbles') else p['banner'] + 1.2
        if p['accent'] < 0: p['accent'] = len(p['lines']) - 1

    def card(self, t):
        p = self.p
        k = spring(t - p['banner'], 1.7, 6.5)
        if t < p['expand']:
            h, top = 150, lerp(-200, 505, k)
        else:
            m = eio(P(t, p['expand'], .38)); h = lerp(150, 660, m); top = lerp(505, 470, m)
        return dict(x=CX, y=top + h / 2, w=CW, h=h, r=38, fill=CARD, a=clamp((t - p['banner']) / .06))

    def content(self, t):
        p = self.p
        h = self.card(t)['h']
        sub = 1 - clamp(eio(P(t, p['expand'], .38)) * 3) if t >= p['expand'] else 1
        bubs = p.get('bubbles') or []
        bub = [eo3(P(t, bt, .28)) if t >= bt else 0 for bt in bubs]
        typing = None
        for i, bt in enumerate(bubs):
            if bt - .32 <= t < bt and t > p['expand'] + .3: typing = (i, clamp((t - bt + .32) / .08))
        return chat_content(h, sub, bub, typing, p['sender'], p['lines'], p['accent'])

    def events(self):
        p = self.p
        ev = [('sfx', p['banner'] + .05, 'ping', 1.0, 0, {}), ('sfx', p['expand'], 'whoosh', .6, 0, dict(d=.25, f0=600, f1=2500, g=.25))]
        for i, bt in enumerate(p.get('bubbles') or []):
            last = i == len(p['bubbles']) - 1
            ev += [('sfx', bt, 'pop', 1.0, (-.2, 0, .2, 0)[i % 4], dict(p=1 + .12 * i)), ('punch', bt, .025 if last else .015)]
        return ev


class TaskCarousel(CardScene):
    """Task cards: stars fill, a boost button gets tapped, then the next tasks swipe in with taps and money chips."""
    name = 'task_carousel'
    TIMES = ('stars', 'button', 'boost', 'swipes')
    DEFAULTS = dict(products=[['headphones', 'Wireless headphones'], ['watch', 'Smart watch'], ['camera', 'Camera kit']],
                    chips=['+$4.20', '+$6.80', '+$5.10'], header='Product rating', btn='Boost listing', done='Listing boosted')
    bg_default = 'cream'

    def card(self, t): return dict(x=CX, y=820, w=CW, h=PH_CARD, r=38, fill=CARD)

    def prod(self, i, t):
        p = self.p; kind, name = p['products'][i]; n = len(p['products'])
        if i == 0 and p.get('stars') is not None:
            st = [eo3(P(t, p['stars'] + .11 * j, .22)) if t >= p['stars'] + .11 * j else 0 for j in range(5)]
            ba = eo3(P(t, p['button'], .2)) if p.get('button') is not None else 0
            bo = p.get('boost')
            pr = clamp(1 - abs(t - bo - .06) / .09) if bo is not None and bo - .05 < t < bo + .2 else 0
            bd = eo3(P(t, bo + .1, .2)) if bo is not None else 0
        else:
            st, ba, pr, bd = [1] * 5, 1, 0, 1
        return product_content(kind, name, i + 1, n, st, ba, pr, bd, p['header'], p['btn'], p['done'])

    def swipe_state(self, t):
        sw = self.p.get('swipes') or []
        idx = 0; o = None
        for i, ts in enumerate(sw):
            q = eio(P(t, ts - .1, .26))
            if q >= 1: idx = i + 1
            elif q > 0: o = (i, q)
        return idx, o

    def content(self, t):
        idx, _ = self.swipe_state(t)
        return self.prod(min(idx, len(self.p['products']) - 1), t)

    def draw(self, b, t):
        idx, o = self.swipe_state(t)
        if o is None:
            super().draw(b, t)
        else:
            i, q = o
            draw_card(b, CX - q * 1100, 820, CW, PH_CARD, 38, CARD, [(self.prod(i, t), 1)])
            draw_card(b, CX + (1 - q) * 1100, 820, CW, PH_CARD, 38, CARD, [(self.prod(i + 1, t), 1)])
            self.overlay(b, t, None)

    def overlay(self, b, t, c):
        p = self.p
        bo = p.get('boost')
        if bo is not None and bo + .05 <= t < bo + .55:
            put(b, ripple_spr(P(t, bo + .05, .5)), CX, 820 - PH_CARD / 2 + 776)
        for i, ts in enumerate(p.get('swipes') or []):
            if ts + .05 <= t < ts + .5: put(b, ripple_spr(P(t, ts + .05, .45)), CX, 820)
            if ts + .1 <= t < ts + .9 and i < len(p['chips']):
                q = P(t, ts + .1, .8)
                put(b, chip_spr(p['chips'][i]), CX + 180, 560 - 260 * eo3(q), 1, 1 - q ** 2)

    def events(self):
        p = self.p; ev = self.intro_events()
        if p.get('stars') is not None:
            ev += [('sfx', p['stars'] + .11 * i, 'tick', 1.0, -.3 + .15 * i, dict(p=1 + .1 * i)) for i in range(5)]
        if p.get('button') is not None: ev.append(('sfx', p['button'], 'pop', .8, 0, dict(p=.9)))
        if p.get('boost') is not None:
            ev += [('sfx', p['boost'], 'tap', 1.0, 0, {}), ('sfx', p['boost'] + .1, 'chime', .8, 0, {}), ('punch', p['boost'], .02)]
        for ts in p.get('swipes') or []:
            ev += [('sfx', ts - .1, 'whoosh', .8, .3, dict(d=.24, f0=800, f1=4000, g=.3)), ('sfx', ts + .05, 'tap', .9, 0, {}),
                   ('sfx', ts + .12, 'coin', .45, 0, {})]
        return ev


class CounterClimb(CardScene):
    """Dark dashboard with an odometer balance that rolls through keyframes, a growth line and task checks.
    keys: [[time, value], ...]. 'more' spawns floating chips (greed beat)."""
    name = 'counter_climb'
    TIMES = ('checks', 'more')
    DEFAULTS = dict(keys=[], checks=None, chips=['+$25', '+$40', '+$60', '+$18'], title='TASK DASHBOARD',
                    label='Available earnings', chk_label='Tasks completed', total_checks=5, vmax=None)
    bg_default = 'navy'
    exit = 'fade'

    def setup(self):
        p = self.p
        p['keys'] = [[self.tl.time(a), float(v)] for a, v in p['keys']]
        if p['vmax'] is None: p['vmax'] = max(v for _, v in p['keys']) if p['keys'] else 100
        if p['checks'] is None:
            ks = p['keys']; n = p['total_checks']
            t0, t1 = ks[0][0], ks[-1][0]
            p['checks'] = [lerp(t0, t1, (i + 1) / n) for i in range(n)]

    def value(self, t):
        ks = self.p['keys']
        if not ks or t <= ks[0][0]: return ks[0][1] if ks else 0
        for (a, va), (b2, vb) in zip(ks, ks[1:]):
            if a <= t <= b2: return lerp(va, vb, eio(P(t, a, b2 - a)))
        return ks[-1][1]

    def card(self, t): return dict(x=CX, y=800, w=CW, h=DH, r=38, fill=DARKCARD, border=(44, 62, 100))

    def content(self, t):
        p = self.p
        nchk = sum(1 for c in p['checks'] if t >= c)
        pop = P(t, p['checks'][nchk - 1], .25) if nchk else 1
        last = p['keys'][-1][0] if p['keys'] else 0
        glow = clamp(1 - abs(t - last) / .5)
        if p.get('more') is not None and t > p['more']: glow += 0.6 * (0.5 + 0.5 * math.sin((t - p['more']) * 9))
        return dash_content(self.value(t), nchk, pop, p['total_checks'], glow=clamp(glow), title=p['title'],
                            label=p['label'], chk_label=p['chk_label'], vmax=p['vmax'])

    def overlay(self, b, t, c):
        p = self.p; mo = p.get('more')
        if mo is None or t < mo: return
        sc = c['sc']; y = c['y']
        for i, (dx, txt) in enumerate(zip((-250, 230, -60, 300), p['chips'])):
            t0 = mo + i * .16
            if t >= t0:
                q = P(t, t0, .75)
                if q < 1: put(b, chip_spr(txt), CX + dx * sc, y - 120 * sc - 300 * eo3(q), sc, clamp(q * 6) * (1 - q ** 2))

    def events(self):
        p = self.p; ev = self.intro_events()
        ks = p['keys']
        if ks:
            last = None
            for i in range(int(ks[0][0] * 200), int(ks[-1][0] * 200) + 2):
                tt = i / 200; v = self.value(tt); k = int(v // (p['vmax'] / 40))
                if last is not None and k != last: ev.append(('sfx', tt, 'tick', .55, 0, dict(p=1 + v / p['vmax'] * .8)))
                last = k
            for (a, va), (b2, vb) in zip(ks, ks[1:]):
                if vb != va and vb > 0 and (vb % 50 == 0 or b2 == ks[-1][0]):
                    ev += [('sfx', b2, 'coin', .9, 0, {}), ('punch', b2, .03 if b2 != ks[-1][0] else .04)]
            ev.append(('sfx', ks[-1][0], 'shimmer', .7, 0, dict(d=.8)))
        ev += [('sfx', c, 'pop', .6, 0, dict(p=1.3)) for c in p['checks']]
        if p.get('more') is not None:
            ev += [('sfx', p['more'] + i * .16, 'pop', .5, (-.4, .4, -.1, .5)[i], dict(p=1.4 + .1 * i)) for i in range(len(p['chips'][:4]))]
        return ev


class WalletSend(CardScene):
    """Wallet card: outgoing deposit, processing spinner then submitted, then a dashed 'expected back' promise.
    If the previous scene is a coin, the coin flies into this card's wallet icon at start+0.32."""
    name = 'wallet_send'
    TIMES = ('done', 'expect')
    DEFAULTS = dict(title='Your wallet', row='Outgoing deposit', amount='-$100.00', expect_label='Expected back',
                    expect_amount='$200.00', proc='Processing', done_label='Submitted')
    bg_default = None
    takes_prev = False
    exit = 'drop'

    def card(self, t):
        bump = 1 + 0.03 * math.sin(math.pi * P(t, self.start + .32, .2))
        return dict(x=CX, y=930, w=CW, h=450, r=38, fill=CARD, sc=bump)

    def content(self, t):
        p = self.p
        st = 'proc' if p.get('done') is None or t < p['done'] else 'done'
        ex = P(t, p['expect'], .7) if p.get('expect') is not None and t >= p['expect'] else 0
        return wallet_content(st, (t * 1.6) % 1, ex, p['title'], p['row'], p['amount'], p['expect_label'],
                              p['expect_amount'], p['proc'], p['done_label'])

    def events(self):
        p = self.p; s = self.start
        ev = [('sfx', s, 'whoosh', .8, 0, dict(d=.3, f0=400, f1=2500)), ('sfx', s + .32, 'coin', 1.0, 0, {}),
              ('punch', s + .32, .02), ('shake', s + .32, 6, .15)]
        if p.get('done') is not None:
            ev += [('sfx', s + .45 + i * .17, 'tick', .3, 0, dict(p=.8)) for i in range(int((p['done'] - s - .45) / .17))]
            ev.append(('sfx', p['done'], 'pop', .8, 0, dict(p=1.1)))
        if p.get('expect') is not None: ev.append(('sfx', p['expect'], 'shimmer', .9, 0, dict(d=.9)))
        return ev


class StampReveal(CardScene):
    """Compact dark balance card drops in; a solid stamp slams on it (glitch, shake, white flash), card goes gray."""
    name = 'stamp_reveal'
    TIMES = ('stamp',)
    DEFAULTS = dict(value=100.0, word='FAKE', title='TASK DASHBOARD', label='Available earnings')
    bg_default = 'paper'
    takes_prev = False
    enter = 'drop'
    exit = 'fade'

    def card(self, t):
        g = self.gray(t)
        return dict(x=CX, y=640, w=CW, h=400, r=38, fill=lerpc(DARKCARD, (58, 62, 72), g))

    def gray(self, t): return eo3(P(t, self.p['stamp'] + .2, .35)) if self.p.get('stamp') is not None else 0

    def content(self, t):
        p = self.p
        im = dash_content(p['value'], compact=True, gray=self.gray(t), title=p['title'], label=p['label'])
        if p.get('stamp') is not None and p['stamp'] <= t < p['stamp'] + .2: im = glitch(im, 14, int(t * 30))
        return im

    def stamp_draw(self, b, x, y, sc, a=1.0, t=None):
        st = self.p.get('stamp')
        if st is None: return
        t = self.tl.now if t is None else t
        if t < st - .12: return
        q = P(t, st - .12, .12)
        put(b, stamp_spr(self.p['word']), x + 215 * sc, y + 95 * sc, lerp(2.6, 1.0, ei3(q)) * sc * 1.05, clamp(q * 3) * a, -11)

    def overlay(self, b, t, c): self.stamp_draw(b, c['x'], c['y'], c['sc'], c['a'], t)

    def pinned_overlay(self, b, x, y, sc, a=1.0): self.stamp_draw(b, x, y, sc, a)

    def events(self):
        st = self.p.get('stamp'); s = self.start
        ev = [('sfx', s - .05, 'whoosh', 1.0, 0, dict(d=.4, f0=3500, f1=300, g=.45)), ('sfx', s + .15, 'thud', .6, 0, dict(g=.5))]
        if st is not None:
            ev += [('sfx', st, 'stamp', 1.0, 0, {}), ('sfx', st + .02, 'glitch', .8, 0, {}), ('punch', st, .07),
                   ('shake', st, 24, .35), ('flash', st, (255, 255, 255), .25, .2)]
        return ev


class SourceCard(CardScene):
    """Official source card (org bar, two line headline with a highlighter sweep on one phrase, footer)."""
    name = 'source_card'
    TIMES = ('highlight',)
    DEFAULTS = dict(org='FEDERAL TRADE COMMISSION', lines=['How to spot and', 'avoid task scams'], phrase='task scams',
                    footer_l='Consumer advice', footer_r='consumer.ftc.gov')
    bg_default = 'paper'
    takes_prev = False
    enter = 'slide_right'
    exit = 'shrink'

    def card(self, t): return dict(x=CX, y=800, w=CW, h=560, r=38, fill=(252, 250, 246))

    def content(self, t):
        p = self.p
        hl = P(t, p['highlight'], .35) if p.get('highlight') is not None else 0
        return source_content(hl, p['org'], p['lines'], p['phrase'], p['footer_l'], p['footer_r'])

    def events(self):
        ev = [('sfx', self.start, 'whoosh', .9, .3, dict(d=.4, f0=300, f1=2500, g=.4))]
        if self.p.get('highlight') is not None: ev += [('sfx', self.p['highlight'], 'marker', 1.0, 0, {}), ('punch', self.p['highlight'], .02)]
        return ev
