"""Audio: SFX library (synthesized), music bed from the beat sheet's mood sections, ducking, mix.
python -m fpm.audio BEATS  -> writes mix_raw.wav next to the beat sheet."""
import sys, os, math
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, sawtooth
from .timeline import Timeline
from .engine import PROFILE

SR = 48000
rng = np.random.default_rng(11)

def t_(d): return np.arange(int(d * SR)) / SR
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def dec(d, tau): t = t_(d); return np.exp(-t / tau)
def att(x, a=0.003):
    n = int(a * SR); x = x.copy(); x[:n] *= np.linspace(0, 1, n); return x
def noise(d): return rng.standard_normal(int(d * SR))
def norm(x, peak=1.0): m = np.max(np.abs(x)) + 1e-9; return x / m * peak
def sweep(f0, f1, d, curve=2.0):
    t = t_(d); f = f0 + (f1 - f0) * (t / d) ** (1 / curve if f1 > f0 else curve)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)

# ---------------- SFX ----------------
def s_tap():
    c = hp(noise(.012), 2500) * dec(.012, .002)
    b = np.sin(2 * np.pi * 190 * t_(.06)) * dec(.06, .015)
    x = np.zeros(int(.06 * SR)); x[:len(c)] += c * .7; x += b * .8
    return norm(x, .55)
def s_ping():
    t = t_(.7); x = (np.sin(2 * np.pi * 1568 * t) * .6 + np.sin(2 * np.pi * 2349 * t) * .35 + np.sin(2 * np.pi * 3136 * t) * .1) * dec(.7, .16)
    y = np.zeros(int(.82 * SR)); y[:len(x)] += x
    x2 = np.sin(2 * np.pi * 2093 * t) * .5 * dec(.7, .14); o = int(.09 * SR); y[o:o + len(x2)] += x2[:len(y) - o]
    return norm(att(y), .42)
def s_pop(p=1.0): return norm(att(sweep(950 * p, 380 * p, .07)) * dec(.07, .025), .5)
def s_tick(p=1.0):
    t = t_(.03); return norm(np.sin(2 * np.pi * 2600 * p * t) * dec(.03, .006) + hp(noise(.03), 4000) * dec(.03, .002) * .4, .28)
def s_buzz():
    t = t_(.42)
    sq = np.sign(np.sin(2 * np.pi * 98 * t)) + np.sign(np.sin(2 * np.pi * 103.5 * t))
    env = ((t < .17) | ((t > .22) & (t < .40))).astype(float)
    env = lp(env, 60, 1)
    return norm(lp(sq, 1800) * env, .5)
def s_thud(g=1.0):
    t = t_(.45); x = sweep(95, 38, .45, 1.3) * dec(.45, .12) + lp(noise(.45), 500) * dec(.45, .03) * .6
    return norm(att(x, .001), .9 * g)
def s_stamp():
    x = s_thud(1.0); s = bp(noise(.09), 900, 3500) * dec(.09, .02)
    x[:len(s)] += s * .7; return norm(x, .95)
def s_whoosh(d=.35, f0=300, f1=3200, g=.45):
    n = noise(d); t = t_(d)
    env = np.sin(np.pi * (t / d) ** .8) ** 2
    out = np.zeros_like(n); segs = 24; L = len(n) // segs + 1
    for i in range(segs):
        a = i * L; b_ = min(len(n), a + L + 400)
        fc = f0 * (f1 / f0) ** (i / segs)
        y = bp(n[a:b_], fc * .6, min(fc * 1.6, 20000))
        w = np.hanning(len(y)); out[a:b_] += y * w
    return norm(out * env, g)
def s_coin():
    t = t_(.6); x = np.zeros(len(t))
    for f, a, tau in ((2093, .6, .2), (3136, .4, .15), (4310, .3, .1), (5274, .25, .08), (6650, .15, .05)):
        x += a * np.sin(2 * np.pi * f * t) * np.exp(-t / tau)
    y = np.zeros(int(.7 * SR)); y[:len(x)] += x; o = int(.075 * SR); y[o:o + len(x)] += .7 * x[:len(y) - o]
    return norm(att(y, .001), .42)
def s_chime():
    y = np.zeros(int(1.1 * SR))
    for i, f in enumerate((1046.5, 1318.5, 1568, 2093)):
        t = t_(.8); x = (np.sin(2 * np.pi * f * t) + .2 * np.sin(4 * np.pi * f * t)) * np.exp(-t / .25)
        o = int(i * .06 * SR); y[o:o + len(x)] += x
    return norm(att(y), .35)
def s_shimmer(d=1.0):
    t = t_(d); y = np.zeros(len(t))
    for _ in range(14):
        f = rng.uniform(3000, 8000); ph = rng.uniform(0, d * .6)
        e = np.clip((t - ph) / .01, 0, 1) * np.exp(-np.clip(t - ph, 0, None) / .12)
        y += np.sin(2 * np.pi * f * t) * e
    return norm(y, .22)
def s_riser(d=1.7):
    t = t_(d); n = hp(noise(d), 1500) * (t / d) ** 2.2 * .6
    s = sweep(180, 900, d, 1.0) * (t / d) ** 1.5 * .5
    return norm(n + s, .5)
def s_hit():
    t = t_(1.4); x = sweep(80, 32, 1.4, 1.2) * np.exp(-t / .35) * 1.0 + lp(noise(1.4), 3000) * np.exp(-t / .25) * .45
    st = s_stamp(); x[:len(st)] += st * .6
    return norm(att(x, .001), 1.0)
def s_marker():
    d = .38; t = t_(d); n = bp(noise(d), 2200, 6000) * (0.6 + 0.4 * np.sin(2 * np.pi * 28 * t)) * np.sin(np.pi * t / d)
    return norm(n, .22)
def s_glitch():
    d = .22; t = t_(d); x = np.sign(np.sin(2 * np.pi * rng.uniform(200, 900) * t))
    gate = (np.floor(t * 60) % 2).astype(float); x = x * gate + bp(noise(d), 1000, 6000) * (1 - gate) * .6
    x = np.round(x * 4) / 4
    return norm(x * np.exp(-t / .12), .3)
def s_spin():
    d = .9; t = t_(d); x = bp(noise(d), 3000, 9000) * (0.5 + 0.5 * np.sin(2 * np.pi * (6 + 10 * (1 - t / d)) * t)) * np.exp(-t / .5)
    return norm(x, .18)


SFX = dict(tap=s_tap, ping=s_ping, pop=s_pop, tick=s_tick, buzz=s_buzz, thud=s_thud, stamp=s_stamp, whoosh=s_whoosh,
           coin=s_coin, chime=s_chime, shimmer=s_shimmer, riser=s_riser, hit=s_hit, marker=s_marker, glitch=s_glitch, spin=s_spin)

BPM = 120; BEAT = 60 / BPM
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def pad(notes, d, cutoff=1400, g=.12):
    t = t_(d); x = np.zeros(len(t))
    for m in notes:
        for det in (-0.09, 0, 0.11):
            x += sawtooth(2 * np.pi * hz(m) * (1 + det / 100 * 1) * t + rng.uniform(0, 6))
    x = lp(x, cutoff, 2)
    env = np.minimum(1, t / .25) * np.minimum(1, (d - t) / .25)
    return x * env * g / len(notes)
def pluck(m, d=.45, g=.25):
    t = t_(d); f = hz(m)
    x = (np.sin(2 * np.pi * f * t) + .35 * np.sin(4 * np.pi * f * t) + .1 * np.sin(6 * np.pi * f * t)) * np.exp(-t / .13)
    return att(x, .002) * g
def kick(g=.5):
    t = t_(.3); return sweep(140, 42, .3, 1.5) * np.exp(-t / .09) * g
def hat(g=.08): return hp(noise(.04), 7000) * dec(.04, .01) * g
def bass(m, d, g=.22):
    t = t_(d); x = np.sin(2 * np.pi * hz(m) * t) + .3 * np.sign(np.sin(2 * np.pi * hz(m) * t))
    return lp(x, 400) * np.exp(-t / (d * .7)) * att(np.ones(len(t)), .005) * g



def build_music(tl, N):
    mus = np.zeros((N, 2))
    def addm(t0, x, g=1.0, pan=0.0):
        i = int(t0 * SR)
        if i >= N or i < 0: return
        x = x[:N - i]
        l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
        mus[i:i + len(x), 0] += x * g * l * 1.41; mus[i:i + len(x), 1] += x * g * r * 1.41
    secs = tl.music + [(tl.dur, 'end')]
    logo = [s.start for s in tl.scenes if s.name == 'logo_outro']
    for (t0, mode), (t1, _) in zip(secs, secs[1:]):
        d = t1 - t0
        if d <= 0 or mode in ('cut', 'hit', 'silence'): continue
        if mode == 'tension':
            tb = t0
            while tb < t1 - .05:
                addm(tb, pad([45, 52, 57, 60], min(1.6, t1 - tb + .1), 900, .16)); tb += 1.5
            tb = t0
            while tb < t1: addm(tb, bass(33, .24, .26)); tb += BEAT / 2
        elif mode == 'bait':
            prog = [[48, 52, 55, 59], [45, 48, 52, 55], [41, 45, 48, 52], [43, 47, 50, 55]]
            arp = [[72, 76, 79, 83, 79, 76, 72, 76], [69, 72, 76, 79, 76, 72, 69, 72], [65, 69, 72, 76, 72, 69, 65, 69], [67, 71, 74, 79, 74, 71, 67, 71]]
            roots = [36, 33, 29, 31]; tb = t0; bar = 0
            while tb < t1 - .01:
                ci = bar % 4; dd = min(2.0, t1 - tb)
                addm(tb, pad(prog[ci], dd + .1, 1800, .10))
                for i in range(8):
                    tt = tb + i * BEAT / 2
                    if tt >= t1: break
                    addm(tt, pluck(arp[ci][i], .4, .16), 1, (-.35, .35)[i % 2])
                    if i % 2 == 1: addm(tt, hat(.07), 1, .25)
                    else: addm(tt, bass(roots[ci], .24, .2))
                for i in range(4):
                    tt = tb + i * BEAT
                    if tt < t1 and bar >= 1: addm(tt, kick(.45))
                tb += 2.0; bar += 1
        elif mode in ('dark', 'dark_plus'):
            prog2 = [[50, 53, 57, 62], [46, 50, 53, 58], [43, 46, 50, 55], [45, 49, 52, 57]]
            roots2 = [38, 34, 31, 33]; tb = t0; bar = 0; late = mode == 'dark_plus'
            while tb < t1 - .01:
                ci = bar % 4; dd = min(2.0, t1 - tb)
                addm(tb, pad(prog2[ci], dd + .1, 1600 if late else 1100, .14))
                for i in range(16):
                    tt = tb + i * BEAT / 4
                    if tt >= t1: break
                    if i % 2 == 0: addm(tt, bass(roots2[ci], .12, .24))
                    addm(tt, hat(.035 if i % 4 else .06), 1, .3 if i % 2 else -.3)
                    if late and i % 4 == 0: addm(tt, kick(.4))
                tb += 2.0; bar += 1
        elif mode == 'build':
            addm(t0, pad([45, 49, 52, 57, 61], d, 1300, .16))
            tb = t0
            while tb < t1: addm(tb, bass(33, .2, .2 + .1 * (tb - t0) / max(d, .1))); tb += BEAT / 2
            for i in range(24): addm(t1 - 1.5 + i * (1.5 / 24), kick(.18 + .02 * i))
        elif mode == 'resolve':
            addm(t0, pad([41, 48, 53, 57, 60], d, 1500, .13))
            m0 = logo[0] if logo else t0 + 1.8
            for i, m in enumerate([77, 72, 69, 72, 77, 81, 79, 77, 72]): addm(m0 + i * .25, pluck(m, .6, .13), 1, (-.3, .3)[i % 2])
            tb = t0; k = 0
            while tb < t1 - .6:
                if k % 2 == 0: addm(tb, bass(29, .3, .14))
                tb += BEAT / 2; k += 1
    fe = int((tl.dur - 1.0) * SR); mus[fe:] *= np.linspace(1, 0, N - fe)[:, None]
    return mus


def main():
    tl = Timeline(sys.argv[1])
    N = int(tl.dur * SR)
    sfx = np.zeros((N, 2)); n = 0
    for e in tl.events:
        if e[0] != 'sfx': continue
        _, t0, name, g, pan, kw = e
        if name in PROFILE['sfx_skip']: continue
        x = SFX[name](**kw); i = int(t0 * SR)
        if i < 0 or i >= N: continue
        x = x[:N - i]
        l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
        sfx[i:i + len(x), 0] += x * g * l * 1.41; sfx[i:i + len(x), 1] += x * g * r * 1.41; n += 1
    if PROFILE['sfx_lowpass']:   # keep SFX out of the range age related hearing loss hits first
        sfx = np.stack([lp(sfx[:, 0], PROFILE['sfx_lowpass']), lp(sfx[:, 1], PROFILE['sfx_lowpass'])], 1)
    mus = build_music(tl, N)
    vo, sr = sf.read(tl.path(tl.beats.get('vo', 'vo_tight.flac')))
    if vo.ndim > 1: vo = vo.mean(axis=1)
    assert sr == SR, 'VO must be 48 kHz (run tools/prep.py)'
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
    vo = hp(vo, 80)
    speech = np.abs(vo) > 1e-4
    vo = vo * (10 ** (-20 / 20) / np.sqrt(np.mean(vo[speech] ** 2)))
    env = np.sqrt(lp(vo ** 2, 8, 1).clip(0)); env = env / (np.percentile(env[speech], 90) + 1e-9)
    duck = lp(1 - PROFILE['duck'] * np.clip(env, 0, 1), 4, 1)
    mix = vo[:, None] + mus * duck[:, None] * PROFILE['music_gain'] + sfx * PROFILE['sfx_gain']
    out = tl.path('mix_raw.wav')
    sf.write(out, mix.astype(np.float32), SR, subtype='FLOAT')
    print(f'profile {PROFILE["name"]}, sfx cues {n}, peak {np.max(np.abs(mix)):.2f} -> {out}')


if __name__ == '__main__':
    main()
