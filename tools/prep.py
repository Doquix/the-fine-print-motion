"""Prepare an episode from a voiceover and a script.

  python tools/prep.py VO_FILE SCRIPT.txt EPISODE_DIR [--keep 0.20]

SCRIPT.txt: one caption per line, in spoken order.
  *word*   marks the keyword shown in orange (one per line, optional)
  |        at the start of a line keeps a longer dramatic pause (0.45 s) before it
  # ...    comment lines are ignored

Writes EPISODE_DIR/vo_tight.flac (48 kHz mono, pauses trimmed), caps.json and caps_review.txt.
Alignment uses pauses in the speech plus character counts (no speech recognition needed),
so check caps_review.txt and fix any line that landed in the wrong place.
"""
import sys, os, json, re, subprocess, argparse
import numpy as np, soundfile as sf


def load(path):
    tmp = '/tmp/_prep_in.wav'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', path, '-ac', '1', '-ar', '48000', tmp], check=True)
    a, sr = sf.read(tmp); return a, sr


def frames_db(a, sr, hop=0.01):
    h = int(sr * hop)
    e = np.array([np.sqrt(np.mean(a[i:i + h] ** 2)) for i in range(0, len(a) - h, h)]) + 1e-9
    return 20 * np.log10(e)


def silent_runs(db, thr, min_len):
    runs = []; s = None
    for i, v in enumerate(db < thr):
        if v and s is None: s = i
        if (not v or i == len(db) - 1) and s is not None:
            if (i - s) * 0.01 >= min_len: runs.append((s * 0.01, i * 0.01))
            s = None
    return runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('vo'); ap.add_argument('script'); ap.add_argument('out')
    ap.add_argument('--keep', type=float, default=0.20)
    ap.add_argument('--dramatic', type=float, default=0.45)
    A = ap.parse_args()
    os.makedirs(A.out, exist_ok=True)

    lines = []
    for ln in open(A.script, encoding='utf8'):
        ln = ln.strip()
        if not ln or ln.startswith('#'): continue
        dram = ln.startswith('|'); ln = ln.lstrip('|').strip()
        m = re.search(r'\*(.+?)\*', ln)
        lines.append(dict(t=ln.replace('*', ''), k=m.group(1) if m else '', dram=dram))

    a, sr = load(A.vo)
    db = frames_db(a, sr)
    floor = np.percentile(db, 8); med = np.percentile(db, 50)
    thr = max(floor + 10, med - 24)

    # ---- pass 1: alignment on the raw audio.
    # Candidate line breaks: every pause (cheap, longer pauses cheaper) or any point inside speech every 0.05 s
    # (more expensive). Dynamic programming picks the breaks so each line's share of speech time matches its
    # share of characters.
    runs = silent_runs(db, thr, 0.05)
    speech_end = len(a) / sr
    lead = runs[0][1] if runs and runs[0][0] == 0 else 0.0
    tail = runs[-1][0] if runs and runs[-1][1] >= speech_end - 0.02 else speech_end
    inner = [r for r in runs if r[0] > lead and r[1] < tail]
    sp = (db >= thr).astype(float); cumS = np.concatenate([[0], np.cumsum(sp)]) * 0.01
    def S(t): return cumS[min(len(cumS) - 1, max(0, int(round(t / 0.01))))]
    ST = S(tail) - S(lead)
    cands = [(lead, lead, 0.0)]  # (end of previous line, start of next line, penalty)
    for g0, g1 in inner:
        cands.append((g0, g1, 1.0e-4 * 0.8 * (1 - min(g1 - g0, 0.5) / 0.5)))
    t = lead + 0.05
    gaps = inner
    while t < tail - 0.05:
        if not any(g0 - 0.03 <= t <= g1 + 0.03 for g0, g1 in gaps): cands.append((t, t, 1.3e-4))
        t += 0.05
    cands.sort(key=lambda c: c[0]); cands.append((tail, tail, 0.0))
    N = len(lines); K = len(cands)
    chars = np.array([max(4, len(l['t'])) for l in lines], float); cs = chars / chars.sum()
    Sa = np.array([S(c[1]) for c in cands]); Sb = np.array([S(c[0]) for c in cands]); pen = np.array([c[2] for c in cands])
    INF = 1e18; dp = np.full((N + 1, K), INF); bk = np.zeros((N + 1, K), int); dp[0, 0] = 0
    for i in range(1, N + 1):
        last = i == N
        for j in range(1, K):
            if last and j != K - 1: continue
            prev = dp[i - 1, :j]
            share = (Sb[j] - Sa[:j]) / ST
            cost = prev + (share - cs[i - 1]) ** 2 + (0 if last else pen[j])
            cost[share <= 0.002] = INF
            k = int(np.argmin(cost)); dp[i, j] = cost[k]; bk[i, j] = k
    spans = []; j = K - 1
    for i in range(N, 0, -1):
        k = bk[i, j]; spans.append((cands[k][1], cands[j][0])); j = k
    spans = spans[::-1]
    M = len(inner) + 1

    # ---- trim pauses; dramatic lines keep a longer pause before them
    starts = {round(s, 2): l['dram'] for (s, e), l in zip(spans, lines)}
    keep_map = []
    for s0, e0 in inner:
        k = A.dramatic if starts.get(round(e0, 2)) else A.keep
        keep_map.append((s0, e0, k))
    out = []; cur = max(0.0, lead - 0.05); tn = 0.0; M_ = [(cur, 0.0)]
    for s0, e0, k in keep_map:
        if e0 - s0 <= k: continue
        ca, cb = s0 + k / 2, e0 - k / 2
        out.append(a[int(cur * sr):int(ca * sr)]); tn += ca - cur; M_ += [(ca, tn), (cb, tn)]; cur = cb
    endt = min(speech_end, tail + 0.15)
    out.append(a[int(cur * sr):int(endt * sr)]); tn += endt - cur; M_.append((endt, tn))
    y = np.concatenate(out)
    pk = np.max(np.abs(y)) + 1e-9
    sf.write(os.path.join(A.out, 'vo_tight.flac'), (y / pk * 0.9).astype(np.float32), sr, subtype='PCM_24')

    def tm(t):
        for (a0, b0), (a1, b1) in zip(M_, M_[1:]):
            if a0 <= t <= a1: return b0 if a1 == a0 else b0 + (t - a0) * (b1 - b0) / (a1 - a0)
        return M_[-1][1] if t > M_[-1][0] else 0.0

    caps = [dict(s=round(tm(s), 3), e=round(tm(e), 3), t=l['t'], k=l['k']) for (s, e), l in zip(spans, lines)]
    json.dump(caps, open(os.path.join(A.out, 'caps.json'), 'w'), indent=0)
    with open(os.path.join(A.out, 'caps_review.txt'), 'w') as f:
        for i, c in enumerate(caps): f.write(f"c{i:<3d} {c['s']:7.2f} {c['e']:7.2f}  {c['t']}\n")
    print(f'{len(caps)} captions, {M} speech chunks, VO {len(a)/sr:.2f}s -> {len(y)/sr:.2f}s')
    print(open(os.path.join(A.out, 'caps_review.txt')).read())


if __name__ == '__main__':
    main()
