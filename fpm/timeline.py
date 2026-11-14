"""Beat sheet -> timeline.

Time anchors (anywhere a time is expected):
  3.25            absolute seconds
  c9              start of caption 9 (0 based)      c9e  end of caption 9
  w18:own money   estimated time of the phrase inside caption 18 (by character position)
  end             episode end
  any of the above + or - an offset:  c9+0.76   w7:boost-0.1
"""
import json, os, re
from .engine import *
from .sprites import brand_bug, caption_spr
from .templates import REGISTRY


class Timeline:
    def __init__(self, beats_path):
        self.dir = os.path.dirname(os.path.abspath(beats_path))
        self.beats = B = json.load(open(beats_path))
        set_profile(B.get('profile', 'standard'))
        self.caps = B['caps_inline'] if 'caps_inline' in B else json.load(open(self.path(B.get('captions', 'caps.json'))))
        self.dur = float(B['duration']) if 'duration' in B else self._vo_len() + 0.2
        self.show = B.get('show', 'THE FINE PRINT'); self.series = B.get('series', 'SCAM FILES')
        self.now = 0.0
        self.scenes = []
        for sp in B['scenes']:
            cls = REGISTRY[sp['t']]
            self.scenes.append(cls(sp, self))
        for i, s in enumerate(self.scenes):
            s.prev = self.scenes[i - 1] if i else None
            s.next = self.scenes[i + 1] if i + 1 < len(self.scenes) else None
            s.end = s.next.start if s.next else self.dur
        for s in self.scenes: s.resolve()
        self.compile()

    def path(self, p): return p if os.path.isabs(p) else os.path.join(self.dir, p)

    def _vo_len(self):
        import soundfile as sf
        info = sf.info(self.path(self.beats.get('vo', 'vo_tight.flac')))
        return info.frames / info.samplerate

    # ---------- anchors
    def time(self, v):
        if isinstance(v, (int, float)): return float(v)
        v = str(v).strip(); off = 0.0
        if not re.fullmatch(r'[+-]?\d*\.?\d+', v):
            m = re.search(r'\s*([+-])\s*(\d*\.?\d+)\s*$', v)
            if m:
                off = float(m.group(2)) * (1 if m.group(1) == '+' else -1); v = v[:m.start()].strip()
        if re.fullmatch(r'\d*\.?\d+', v): return float(v) + off
        if v == 'end': return self.dur + off
        m = re.fullmatch(r'c(\d+)(e?)', v)
        if m:
            c = self.caps[int(m.group(1))]; return (c['e'] if m.group(2) else c['s']) + off
        m = re.fullmatch(r'w(\d+):(.+)', v)
        if m:
            c = self.caps[int(m.group(1))]; txt = c['t']; i = txt.lower().find(m.group(2).strip().lower())
            if i < 0: raise ValueError(f'phrase "{m.group(2)}" not in caption {m.group(1)}: {txt}')
            return c['s'] + (c['e'] - c['s']) * i / max(1, len(txt)) + off
        raise ValueError(f'bad time anchor: {v}')

    # ---------- compile events
    def compile(self):
        self.events = []
        for s in self.scenes: self.events += s.events()
        CAM.punch = [(e[1], e[2]) for e in self.events if e[0] == 'punch']
        CAM.shake = [(e[1], e[2], e[3]) for e in self.events if e[0] == 'shake']
        self.flashes = [(t0, col, amax * PROFILE['flash'], d) for t0, col, amax, d in (e[1:] for e in self.events if e[0] == 'flash')]
        self.blurs = [(t0, d, a * PROFILE['blur']) for t0, d, a in (e[1:] for e in self.events if e[0] == 'blur')]
        self.creeps = [e[1:] for e in self.events if e[0] == 'creep']
        z = [e[1:] for e in self.events if e[0] == 'zoom']
        self.zoom = z[-1] if z else None
        def extra(t, sc, ox, oy):
            for t0, t1, t2, amt in self.creeps:
                if t0 < t < t1: sc += amt * eio(P(t, t0, t1 - t0))
                elif t1 <= t < t2 + .1: sc += amt
            if self.zoom and t > self.zoom[0]:
                q = ei3(P(t, self.zoom[0], self.zoom[1] - self.zoom[0])); sc *= 1 + 5 * q; oy += 500 * q
            return sc, ox, oy
        CAM.extra = extra
        # backgrounds
        self.bgs = []
        for s in self.scenes:
            if not s.bg: continue
            if self.bgs and self.bgs[-1][1] == s.bg: continue
            org = s.bg_from or s.bg_origin()
            org = {'bottom': (CX, H), 'top': (CX, 0), 'center': (CX, CY), 'left': (0, CY), 'right': (W, CY)}.get(org, org) if isinstance(org, str) else tuple(org)
            t0 = 0.0 if not self.bgs else s.start + s.spec.get('bg_delay', 0.05)
            self.bgs.append((t0, s.bg, org, s.spec.get('bg_mode', 'radial'), s.spec.get('bg_dur', 0.42)))
        if not self.bgs: self.bgs = [(0.0, 'navy', (CX, CY), 'radial', .42)]
        # caption visibility
        hide_txt = set(self.beats.get('hide_captions', []))
        self.cap_hidden = set()
        for i, c in enumerate(self.caps):
            if c['t'] in hide_txt: self.cap_hidden.add(i)
            for s in self.scenes:
                if s.hide_captions and s.start - .05 <= c['s'] < s.until(): self.cap_hidden.add(i)
                if s.name == 'block_modal' and s.p.get('hide_stop_caption') and s.p.get('stop') is not None and abs(c['s'] - s.p['stop']) < .3:
                    self.cap_hidden.add(i)
        # music sections
        self.music = [(self.time(a), m) for a, m in self.beats.get('music', [[0, 'tension']])]

    # ---------- per frame
    def bg_at(self, t):
        i = max(j for j, b in enumerate(self.bgs) if b[0] <= t)
        t0, name, org, mode, dur = self.bgs[i]
        p = P(t, t0, dur)
        if i == 0 or p >= 1: return bg_full(name).copy(), name
        prev = self.bgs[i - 1][1]
        if mode == 'fade':
            return Image.blend(bg_full(prev), bg_full(name), eio(p)), (name if p > .5 else prev)
        m = radial_mask(org[0], org[1], eio(p))
        return Image.composite(bg_full(name), bg_full(prev), m), (name if p > .5 else prev)

    def ui(self, b, t, bgname):
        if not any(s.hide_bug and s.active(t) for s in self.scenes):
            bug = brand_bug(bgname in LIGHT, self.show, self.series)
            put(b, bug, CX, 222 + bug.height / SS / 2, cam=False)
        for i, c in enumerate(self.caps):
            if i in self.cap_hidden: continue
            nxt = self.caps[i + 1]['s'] if i + 1 < len(self.caps) else 1e9
            end = min(c['e'] + .06, nxt)
            if not (c['s'] - .02 <= t < end): continue
            q = 1.0 if i == 0 else P(t, c['s'] - .02, .16)
            oa = 1 - P(t, end - .07, .07) if nxt - c['e'] > .12 else 1
            spr = caption_spr(c['t'], c.get('k', ''))
            fit = min(1.0, 960 / (spr.width / SS))
            put(b, spr, CX, 1430, fit * (0.88 + 0.12 * eoback(q)), clamp(q * 3) * oa, cam=False)

    def frame(self, t):
        self.now = t
        CAM.set(t)
        bgi, bgname = self.bg_at(t)
        b = bgi.convert('RGBA')
        for s in self.scenes:
            if s.active(t): s.draw(b, t)
        for t0, col, amax, d in self.flashes:
            if t0 <= t < t0 + d:
                b = Image.blend(b, Image.new('RGBA', (W, H), tuple(col) + (255,)), amax * (1 - P(t, t0, d)) ** 2)
        self.ui(b, t, bgname)
        img = b.convert('RGB')
        if self.zoom and t > self.zoom[0] + .1:
            img = Image.blend(img, bg_full('navy'), ei3(P(t, self.zoom[0] + .1, self.zoom[1] - self.zoom[0] - .1)))
        amt = 0
        for t0, d, a in self.blurs:
            if t0 <= t < t0 + d: amt = max(amt, math.sin(math.pi * P(t, t0, d)) * a)
        if self.zoom and t > self.zoom[0]: amt = max(amt, 70 * P(t, self.zoom[0], self.zoom[1] - self.zoom[0]))
        if amt >= 2:
            a = np.asarray(img).astype(np.float32); acc = a.copy()
            for k in range(1, 6): acc += np.roll(a, int(amt * k / 5), axis=0)
            img = Image.fromarray((acc / 6).astype(np.uint8))
        return img
