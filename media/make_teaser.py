"""SPHEREx Voyage teaser, version 2: a curved route around a galaxy, fast jumps
between the five targets, a new ship and a synthesized soundtrack.

Usage: python -I render2.py preview <dir> t1 t2 ...   (still frames)
       python -I render2.py audio <wav>
       python -I render2.py video <ffmpeg.exe> <wav> <out.mp4>
"""
import sys, math, random, subprocess, wave
from pathlib import Path
sys.path.insert(0, r'C:/Users/User/Desktop/Final_projectfile/Research/Paper/.work/deps')
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

MODE = sys.argv[1]
W, H, FPS, DUR = 1920, 1080, 30, 29.5
NF = int(DUR * FPS)
RED, BLUE, WHITE = (252, 61, 33), (11, 61, 145), (245, 247, 252)
CYAN = (120, 210, 255)
F = 'C:/Windows/Fonts/'
def font(name, size): return ImageFont.truetype(F + name, size)
BLACK, REG, MONO = 'seguibl.ttf', 'segoeui.ttf', 'consolab.ttf'

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, p): return a + (b - a) * p
def fade(t, t0, t1, t2, t3): return smooth((t - t0) / (t1 - t0)) * (1 - smooth((t - t2) / (t3 - t2)))

# ---------------------------------------------------------------- motion
DW0, DWL, JL = 3.4, 2.5, 1.1
PER = DWL + JL
US = [0.10, 0.28, 0.46, 0.64, 0.82]
DL = 0.012
T_END = DW0 + 4 * PER + DWL          # 20.3: the last dwell ends
ARRIVE = [DW0 + k * PER for k in range(5)]

def u_of(t):
    if t < 1.2:
        return 0.004 * t
    if t < DW0:
        return lerp(0.0048, US[0] - DL, smooth((t - 1.2) / (DW0 - 1.2)))
    if t < T_END:
        k = int((t - DW0) // PER)
        tau = (t - DW0) - k * PER
        if tau < DWL:
            return US[k] - DL + 2 * DL * tau / DWL
        return lerp(US[k] + DL, US[k + 1] - DL, smooth((tau - DWL) / JL))
    te = t - T_END
    return US[4] + DL + 0.012 * te + 0.5 * clamp(te / 3.3) ** 3 + 0.45 * max(te - 3.3, 0)

def zoom_of(t):
    if t < 1.2:
        return 0.3
    if t < DW0:
        return lerp(0.3, 1.0, smooth((t - 1.2) / (DW0 - 1.2)))
    if t < T_END:
        tau = (t - DW0) % PER
        if tau < DWL:
            return 1.0
        return 1.0 - 0.5 * math.sin(math.pi * (tau - DWL) / JL) ** 1.3
    return lerp(1.0, 0.3, smooth((t - T_END - 0.6) / 2.7))

def P(u):
    a = math.radians(160 + 300 * u)
    r = 1150 + 110 * math.sin(2 * a)
    if u > 1:
        r += 2600 * (u - 1) ** 1.5
    return r * math.cos(a), r * math.sin(a)

def ship_world(t):
    return P(u_of(t))

def speed_of(t):
    a, b = ship_world(t - 0.02), ship_world(t + 0.02)
    return math.hypot(b[0] - a[0], b[1] - a[1]) / 0.04 * (1 - smooth((t - 23.4) / 0.7))

def heading_of(t):
    a, b = ship_world(t - 0.03), ship_world(t + 0.03)
    return math.atan2(b[1] - a[1], b[0] - a[0])

def camera(t):
    z = zoom_of(t)
    k = clamp((z - 0.3) / 0.7) ** 0.8
    sx, sy = ship_world(t)
    return sx * k, sy * k, z, 960.0, lerp(540.0, 430.0, clamp((z - 0.3) / 0.7))

TARGETS = [
    ("BARNARD'S STAR", 'The fastest-moving star in our sky.', 'MOTION  ·  10.4 ARCSEC PER YEAR', (255, 150, 100)),
    ('EPSILON INDI B', 'Twin brown dwarfs, 12 light-years away.', 'MOTION  ·  A BLENDED PAIR', (225, 140, 85)),
    ('WISE 0855', 'One of the coldest worlds known, near 250 K.', 'MOTION  ·  FAINT AND FAST', (200, 120, 170)),
    ('RW AURIGAE', 'A young star that dims without warning.', 'BRIGHTNESS  ·  DEPENDS ON COLOUR', (255, 214, 130)),
    ('R DRACONIS', 'A giant star that pulses every 246 days.', 'BRIGHTNESS  ·  TOO BRIGHT TO MEASURE', (255, 110, 90)),
]
def star_world(k):
    x, y = P(US[k])
    r = math.hypot(x, y)
    side = 1 if k % 2 == 0 else -1
    return x + x / r * 190 * side, y + y / r * 190 * side
STARS = [star_world(k) for k in range(5)]

# ---------------------------------------------------------------- audio
def make_audio(path):
    SR = 44100
    n = int(DUR * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(3)
    ctl_t = np.arange(0, DUR + 0.02, 0.01)
    spd = np.interp(t, ctl_t, [min(speed_of(x) / 1300.0, 2.2) for x in ctl_t])

    def band_noise(lo, hi, seed):
        x = np.random.default_rng(seed).standard_normal(n)
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(n, 1 / SR)
        c, w = math.sqrt(lo * hi), (hi - lo) / 2
        X *= np.exp(-((f - c) / w) ** 2)
        y = np.fft.irfft(X, n)
        return y / (np.abs(y).max() + 1e-9)

    def env(t0, attack, decay):
        e = np.zeros(n)
        i0 = int(t0 * SR)
        m = n - i0
        tt = np.arange(m) / SR
        e[i0:] = np.minimum(tt / attack, 1) * np.exp(-np.maximum(tt - attack, 0) / decay)
        return e

    L = np.zeros(n)
    R = np.zeros(n)
    def add(sig, pan=0.0):
        L[:] += sig * (1 - max(pan, 0))
        R[:] += sig * (1 + min(pan, 0))

    # space drone
    drone = sum(a * np.sin(2 * np.pi * f * t + p) for f, a, p in [(55, .5, 0), (82.6, .32, 1), (110.3, .22, 2), (164.6, .1, 3)])
    drone *= 0.085 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.13 * t))
    add(drone + band_noise(200, 900, 1) * 0.012)
    # engine: a soft, warm swell that follows the ship's speed (pure tones, no buzz)
    k = 1.0 / (0.18 * SR)                       # smooth the speed so the sound glides
    sm = np.empty(n); acc = 0.0
    for a0 in range(0, n, 441):
        acc += (spd[a0] - acc) * min(1.0, k * 441)
        sm[a0:a0 + 441] = acc
    sm = np.clip(sm, 0, 1.8)
    glide = 2 ** (sm * 0.5)                     # rises by up to about ten semitones
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t)
    def tone(f0, detune=1.0):
        return np.sin(2 * np.pi * np.cumsum(f0 * detune * glide * vib) / SR)
    hum = (tone(110) + tone(110, 1.006)) * 0.5 + (tone(165) + tone(165, 0.995)) * 0.28 + tone(220) * 0.2 + tone(330) * 0.08
    add(hum * (0.018 + 0.085 * np.clip(sm, 0, 1.3)))
    # shimmer that blooms during each jump
    shim = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate((440.0, 554.37, 659.25, 880.0))) * 0.25
    add(shim * np.clip(sm - 0.15, 0, 1.2) ** 1.3 * 0.05 * (0.85 + 0.15 * np.sin(2 * np.pi * 0.9 * t)))
    # gentle rush of air: low and soft, with no hiss
    add(band_noise(180, 1100, 2) * np.clip(sm - 0.1, 0, 1.6) ** 1.2 * 0.11, pan=0.15)
    add(band_noise(260, 1500, 4) * np.clip(sm - 0.1, 0, 1.6) ** 1.2 * 0.09, pan=-0.15)
    # arrival chimes
    notes = [440.0, 523.25, 587.33, 659.25, 783.99]
    for k, t0 in enumerate(ARRIVE):
        for j, (mult, amp, dly) in enumerate([(1, .2, 0.12), (1.5, .14, 0.27), (2, .07, 0.27)]):
            e = env(t0 + dly, 0.008, 0.55)
            add(np.sin(2 * np.pi * notes[k] * mult * t) * e * amp, pan=0.35 if k % 2 == 0 else -0.35)
        e = env(t0 + 0.62, 0.008, 0.5)
        add(np.sin(2 * np.pi * notes[k] * 1.5 * t) * e * 0.05, pan=-0.35 if k % 2 == 0 else 0.35)
    # intro swell
    pad_i = sum(np.sin(2 * np.pi * f * t) for f in (220, 261.63, 329.63, 493.88)) * 0.03
    add(pad_i * np.clip(t / 1.2, 0, 1) * np.clip((3.6 - t) / 1.2, 0, 1))
    # final riser, impact and outro chord
    r0, r1 = T_END + 0.3, 23.5
    p = np.clip((t - r0) / (r1 - r0), 0, 1)
    rf = 90 * (10 ** p)
    riser = np.sin(2 * np.pi * np.cumsum(rf) / SR) * p ** 2 * 0.12 * (t < r1)
    add(riser + band_noise(1500, 7000, 5) * p ** 3 * 0.1 * (t < r1))
    ti = 23.55
    bf = 38 + 50 * np.exp(-np.maximum(t - ti, 0) / 0.25)
    boom = np.sin(2 * np.pi * np.cumsum(bf) / SR) * env(ti, 0.005, 0.9) * 0.55
    add(boom + band_noise(300, 5000, 6) * env(ti, 0.004, 0.35) * 0.18)
    chord = sum(a * np.sin(2 * np.pi * f * t + i) for i, (f, a) in enumerate([(110, .5), (164.81, .4), (220, .4), (277.18, .32), (329.63, .3), (440, .16), (554.37, .1)]))
    add(chord * 0.075 * np.clip((t - 23.7) / 1.4, 0, 1) * (0.9 + 0.1 * np.sin(2 * np.pi * 0.4 * t)))
    for j, f in enumerate((659.25, 880.0, 1108.73)):
        add(np.sin(2 * np.pi * f * t) * env(24.4 + 0.22 * j, 0.01, 0.9) * 0.07, pan=(-0.4, 0.0, 0.4)[j])

    master = np.clip(t / 0.5, 0, 1) * np.clip((DUR - 0.15 - t) / 1.2, 0, 1)
    st = np.tanh(np.stack([L, R], 1) * master[:, None] * 1.5) * 0.9
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype('<i2').tobytes())
    print('audio', path, 'peak', float(np.abs(st).max()))

if MODE == 'audio':
    make_audio(sys.argv[2])
    sys.exit()

# ---------------------------------------------------------------- galaxy
GN, GS = 4000, 2.0                      # image size and world units per pixel
def make_galaxy():
    rng = np.random.default_rng(11)
    ax = (np.arange(GN, dtype=np.float32) - GN / 2) * GS
    x, y = np.meshgrid(ax, ax)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    def noise(m):
        a = Image.fromarray((rng.random((m, m)) * 255).astype(np.uint8)).resize((GN, GN), Image.BICUBIC)
        return np.asarray(a, np.float32) / 255
    n1, n2 = noise(90), noise(420)
    arm = (0.5 + 0.5 * np.cos(2 * (th - np.log(r / 100 + 1) * 1.9))) ** 3
    disk = np.exp(-r / 640)
    dens = disk * (0.22 + 1.7 * arm) * (0.5 + 1.0 * n1) * (0.65 + 0.7 * n2)
    core = np.exp(-(r / 230) ** 2)
    vign = np.clip(1 - r / 4200, 0, 1)
    img = np.empty((GN, GN, 3), np.float32)
    for c, (base, armc, knot, corec) in enumerate([(4, 62, 150, 255), (9, 104, 55, 222), (30, 235, 110, 175)]):
        img[..., c] = base * (0.6 + 0.9 * vign) + dens * armc * 1.75 + arm * disk * np.clip(n2 - 0.55, 0, 1) * knot * 2.2 + core * corec * 1.05 + np.exp(-(r / 95) ** 2) * 120
    img = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').filter(ImageFilter.GaussianBlur(5)), np.float32)
    # stars that belong to the disk
    m = 60000
    px = rng.integers(0, GN, m); py = rng.integers(0, GN, m)
    keep = rng.random(m) < np.clip(dens[py, px] * 3.2 + 0.03, 0, 1)
    b = rng.uniform(60, 190, m)[keep][:, None]
    img[py[keep], px[keep]] += b
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB')
GAL = make_galaxy()

# ---------------------------------------------------------------- sprites
rnd = random.Random(7)
LAYERS = []
for n_, f_, size_, bright_ in [(230, .05, 1, 200), (120, .12, 2, 210), (50, .25, 2, 255)]:
    LAYERS.append((f_, size_, [(rnd.uniform(0, W + 60), rnd.uniform(0, H + 60), rnd.uniform(.5, 1) * bright_, rnd.uniform(0, 6.28)) for _ in range(n_)]))

def glow(size, color, core=.09):
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    c = (size - 1) / 2
    r = np.hypot(x - c, y - c) / (size / 2)
    a = np.exp(-(r / .28) ** 2) * .55 + np.exp(-(r / core) ** 2)
    dx, dy = np.abs(x - c) / (size / 2), np.abs(y - c) / (size / 2)
    a += np.exp(-(dy / .012) ** 2) * np.exp(-(dx / .55) ** 2) * .7 + np.exp(-(dx / .012) ** 2) * np.exp(-(dy / .55) ** 2) * .7
    a = np.clip(a, 0, 1) * np.clip(1.2 - r, 0, 1)
    wh = np.clip(np.exp(-(r / (core * 1.4)) ** 2), 0, 1)[..., None]
    rgb = np.array(color, np.float32) * (1 - wh) + 255 * wh
    return Image.fromarray(np.dstack([rgb, np.clip(a, 0, 1)[..., None] * 255]).astype(np.uint8), 'RGBA')
GLOWS = [glow(300, t_[3]) for t_ in TARGETS]

GC = 1000                                # ship canvas, ship centre in the middle
def make_ship():
    S = 4
    im = Image.new('RGBA', (GC * S, GC * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = GC * S // 2
    def Pp(pts): return [(c + x * S, c + y * S) for x, y in pts]
    hull_dark, hull_mid, hull = (38, 50, 86), (120, 132, 160), (236, 240, 248)
    # delta wings
    d.polygon(Pp([(70, 0), (-58, -112), (-96, -112), (-70, -30), (-92, -26), (-92, 26), (-70, 30), (-96, 112), (-58, 112)]), fill=hull_dark)
    d.polygon(Pp([(52, -12), (-58, -104), (-80, -104), (-56, -30)]), fill=(58, 74, 120))
    d.polygon(Pp([(52, 12), (-58, 104), (-80, 104), (-56, 30)]), fill=(48, 62, 104))
    # red wing chevrons and tips
    d.polygon(Pp([(-20, -66), (-34, -78), (-70, -78), (-60, -66)]), fill=RED)
    d.polygon(Pp([(-20, 66), (-34, 78), (-70, 78), (-60, 66)]), fill=RED)
    d.polygon(Pp([(-58, -112), (-96, -112), (-92, -100), (-66, -100)]), fill=RED)
    d.polygon(Pp([(-58, 112), (-96, 112), (-92, 100), (-66, 100)]), fill=RED)
    # engine nacelles
    for sgn in (-1, 1):
        d.rounded_rectangle((c - 104 * S, c + (sgn * 52 - 13) * S, c - 22 * S, c + (sgn * 52 + 13) * S), 10 * S, fill=hull_mid)
        d.rounded_rectangle((c - 104 * S, c + (sgn * 52 - 13) * S, c - 22 * S, c + (sgn * 52 - 3) * S), 8 * S, fill=(168, 178, 200))
        d.ellipse((c - 112 * S, c + (sgn * 52 - 10) * S, c - 96 * S, c + (sgn * 52 + 10) * S), fill=(190, 240, 255))
    # fuselage
    d.polygon(Pp([(128, 0), (60, -17), (-60, -24), (-100, -16), (-100, 16), (-60, 24), (60, 17)]), fill=hull)
    d.polygon(Pp([(128, 0), (60, 17), (-60, 24), (-100, 16), (-100, 4), (60, 4)]), fill=(196, 204, 222))
    d.polygon(Pp([(-28, -23), (-12, -22), (-12, 22), (-28, 23)]), fill=BLUE)
    d.polygon(Pp([(-40, -23.5), (-34, -23), (-34, 23), (-40, 23.5)]), fill=RED)
    d.ellipse((c - 108 * S, c - 9 * S, c - 94 * S, c + 9 * S), fill=(190, 240, 255))
    # canopy
    d.polygon(Pp([(92, 0), (58, -10), (16, -11), (6, 0), (16, 11), (58, 10)]), fill=(18, 34, 78))
    d.polygon(Pp([(84, -1), (58, -8), (22, -9), (16, -2)]), fill=(96, 150, 235))
    d.line(Pp([(128, 0), (96, 0)]), fill=(150, 160, 185), width=S)
    return im.resize((GC, GC), Image.LANCZOS)
SHIP = make_ship()

def make_plume(k):
    r = random.Random(k)
    S = 2
    w, h = 460 * S, 180 * S
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = h // 2
    for off, wd, ln in ((-52, 11, 1.0), (52, 11, 1.0), (0, 8, 0.8)):
        L_ = r.uniform(300, 420) * ln
        y0 = cy + off * S
        d.polygon([(w, y0 - wd * S), (w - L_ * S, y0 + r.uniform(-3, 3) * S), (w, y0 + wd * S)], fill=(70, 150, 255, 210))
        d.polygon([(w, y0 - wd * .55 * S), (w - L_ * .6 * S, y0), (w, y0 + wd * .55 * S)], fill=(170, 230, 255, 240))
        d.polygon([(w, y0 - wd * .28 * S), (w - L_ * .3 * S, y0), (w, y0 + wd * .28 * S)], fill=(255, 255, 255, 255))
    return im.filter(ImageFilter.GaussianBlur(3 * S)).resize((460, 180), Image.LANCZOS)
PLUMES = [make_plume(k) for k in range(8)]

CW, CH = 800, 236
def make_card(i):
    name, line, tag, col = TARGETS[i]
    im = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, CW - 1, CH - 1), 18, fill=(5, 11, 32, 236), outline=(90, 120, 190, 255), width=2)
    d.rounded_rectangle((0, 0, 12, CH - 1), 6, fill=RED + (255,))
    d.text((44, 26), 'TARGET %d / 5' % (i + 1), font=font(MONO, 24), fill=RED + (255,))
    d.text((44, 60), name, font=font(BLACK, 58), fill=WHITE + (255,))
    d.text((44, 140), line, font=font(REG, 33), fill=(214, 222, 240, 255))
    d.text((44, 190), tag, font=font(MONO, 22), fill=(143, 176, 255, 255))
    return im
CARDS = [make_card(i) for i in range(5)]
CARD_POS = ((W - CW) // 2, 800)

def text_layer(items):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for text, fnt, fill, y, x in items:
        if x is None:
            d.text((W / 2, y), text, font=fnt, fill=fill, anchor='ma')
        else:
            d.text((x, y), text, font=fnt, fill=fill)
    return im
sc = np.zeros((H, W, 4), np.uint8)
sc[..., 3] = (np.clip((np.arange(H) - 600) / 300, 0, 1) ** 1.2 * 215)[:, None]
SCRIM = Image.fromarray(sc, 'RGBA')
INTRO = text_layer([
    ('NASA SPACE APPS 2026  ·  PLANET X AND SPHEREx', font(MONO, 30), RED + (255,), 810, None),
    ('Five targets. One infrared sky.', font(BLACK, 92), WHITE + (255,), 860, None),
])
HEADER = text_layer([('SPHEREx VOYAGE', font(MONO, 26), (190, 202, 228, 255), 64, 80)])
MESSAGE = text_layer([
    ('Real SPHEREx images.  True dates.', font(BLACK, 80), WHITE + (255,), 800, None),
    ('Doubts shown, not hidden.', font(BLACK, 80), RED + (255,), 900, None),
])
TITLE = text_layer([('SPHEREx VOYAGE', font(BLACK, 168), WHITE + (255,), 330, None)])
TAG = text_layer([('See how the sky really changed.', font(REG, 56), (226, 232, 246, 255), 590, None)])
CREDITS = text_layer([
    ('NASA SPACE APPS 2026  ·  PLANET X AND SPHEREx', font(MONO, 30), RED + (255,), 760, None),
    ('github.com/NasirAldeen/Planet-X-and-SPHEREx', font(MONO, 30), WHITE + (255,), 814, None),
    ('Built with SPHEREx data from the NASA/IPAC Infrared Science Archive. Not an official NASA product. Route and galaxy are artistic.', font(REG, 24), (170, 182, 210, 255), 960, None),
])
LABEL_FONT = font(MONO, 22)

def paste(frame, layer, alpha, pos=(0, 0)):
    if alpha <= 0.003: return
    if alpha < 0.997:
        layer = layer.copy()
        layer.putalpha(layer.getchannel('A').point(lambda v: int(v * alpha)))
    frame.paste(layer, pos, layer)

ROUTE = [P(i / 300) for i in range(301)]

def render(fi):
    t = fi / FPS
    cx, cy, z, ax, ay = camera(t)
    def S2(p): return ax + (p[0] - cx) * z, ay + (p[1] - cy) * z
    zo = clamp((1 - z) / 0.7)
    # galaxy backdrop
    l, tp = cx - ax / z, cy - ay / z
    box = ((l / GS) + GN / 2, (tp / GS) + GN / 2, ((l + W / z) / GS) + GN / 2, ((tp + H / z) / GS) + GN / 2)
    fr = GAL.resize((W, H), Image.BILINEAR, box=box)
    dim = smooth((t - 23.9) / 1.2) * 0.5
    if dim > 0:
        fr = fr.point(lambda p: int(p * (1 - dim)))
    d = ImageDraw.Draw(fr, 'RGBA')
    # foreground stars with speed streaks
    sp = speed_of(t)
    hd = heading_of(t)
    for f, size, stars in LAYERS:
        ln = sp * z * f * 0.16 if sp * z > 300 else 0
        ox, oy = cx * f, cy * f
        for x0, y0, b, ph in stars:
            x = (x0 - ox) % (W + 60) - 30
            y = (y0 - oy) % (H + 60) - 30
            c = int(b * (0.75 + 0.25 * math.sin(t * 3 + ph)))
            col = (c, c, min(255, c + 20), 255)
            if ln > 3:
                d.line((x, y, x - math.cos(hd) * ln, y - math.sin(hd) * ln), fill=col, width=size)
            elif size == 1:
                d.point((x, y), fill=col)
            else:
                d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=col)
    # route: dashed ahead, solid behind
    u = u_of(t)
    pts = [S2(p) for p in ROUTE]
    a_route = int(60 + 150 * zo)
    for i in range(0, 300, 2):
        if i / 300 >= u:
            d.line((pts[i], pts[i + 1]), fill=(143, 176, 255, a_route), width=2)
    done = [S2(P(i / 300)) for i in range(0, int(min(u, 1.3) * 300) + 1)] + [S2(P(min(u, 1.3)))]
    if len(done) > 1:
        d.line(done, fill=RED + (int((120 + 110 * zo) * (1 - 1.3 * dim)),), width=3 if z > 0.6 else 4)
    # target stars
    for k in range(5):
        sx, sy = S2(STARS[k])
        if -200 < sx < W + 200 and -200 < sy < H + 200:
            g = int(300 * max(z, 0.42) * (1 + 0.06 * math.sin(t * 5 + k)))
            gs = GLOWS[k].resize((g, g), Image.BILINEAR)
            fr.paste(gs, (int(sx - g / 2), int(sy - g / 2)), gs)
            la = clamp((zo - 0.3) / 0.3) * (1 - smooth((t - 22.8) / 0.8))
            if la > 0.02 and sy < 740:
                d = ImageDraw.Draw(fr, 'RGBA')
                d.text((sx + 26, sy - 34), TARGETS[k][0], font=LABEL_FONT, fill=(235, 240, 252, int(235 * la)))
    d = ImageDraw.Draw(fr, 'RGBA')
    # ship: trail, plume and hull
    shx, shy = S2(ship_world(t))
    scale = 0.5 + 0.5 * z
    if -600 < shx < W + 600 and -600 < shy < H + 600:
        for j in range(1, 30):
            px, py = S2(ship_world(t - j * 0.018))
            rr = max(1.0, (8 - j * 0.24) * scale)
            d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=(120, 200, 255, int(150 * (1 - j / 30))))
        boost = clamp(sp / 1300, 0, 1.6)
        pl = PLUMES[fi % len(PLUMES)]
        plw = int(460 * (0.38 + 0.62 * min(boost, 1.0)))
        pl = pl.resize((plw, 180), Image.BILINEAR)
        grp = Image.new('RGBA', (GC, GC), (0, 0, 0, 0))
        grp.paste(pl, (GC // 2 - 100 - plw, GC // 2 - 90), pl)
        grp.alpha_composite(SHIP)
        gsz = int(GC * scale)
        grp = grp.rotate(-math.degrees(hd), resample=Image.BICUBIC).resize((gsz, gsz), Image.BILINEAR)
        fr.paste(grp, (int(shx - gsz / 2), int(shy - gsz / 2)), grp)
    d = ImageDraw.Draw(fr, 'RGBA')
    # cards
    for k in range(5):
        a = fade(t, ARRIVE[k] - 0.05, ARRIVE[k] + 0.35, ARRIVE[k] + DWL - 0.25, ARRIVE[k] + DWL + 0.15)
        if a > 0.003:
            sx, sy = S2(STARS[k])
            ex = clamp(sx, CARD_POS[0] + 80, CARD_POS[0] + CW - 80)
            col = (143, 176, 255, int(230 * a))
            d.line((sx, sy + 34, sx, sy + 70, ex, CARD_POS[1] - 30, ex, CARD_POS[1]), fill=col, width=2)
            d.ellipse((sx - 5, sy + 29, sx + 5, sy + 39), outline=col, width=2)
            pop = 1 - 0.1 * (1 - smooth((t - ARRIVE[k] + 0.05) / 0.4))
            card = CARDS[k] if pop > 0.995 else CARDS[k].resize((int(CW * pop), int(CH * pop)), Image.BILINEAR)
            paste(fr, card, a, (CARD_POS[0] + (CW - card.width) // 2, CARD_POS[1] + (CH - card.height) // 2))
    # text
    ia = fade(t, 0.4, 1.0, 2.7, 3.3)
    ma = fade(t, T_END + 0.2, T_END + 0.7, 23.0, 23.6)
    paste(fr, SCRIM, max(ia, ma))
    paste(fr, INTRO, ia)
    paste(fr, HEADER, fade(t, 3.3, 3.9, T_END + 0.2, T_END + 0.8))
    paste(fr, MESSAGE, ma)
    ta = smooth((t - 24.2) / 0.9)
    if ta > 0:
        paste(fr, TITLE, ta)
        wl = int(520 * smooth((t - 24.8) / 0.8))
        if wl > 2:
            ImageDraw.Draw(fr).rectangle((W / 2 - wl, 548, W / 2 + wl, 554), fill=RED)
        paste(fr, TAG, smooth((t - 25.1) / 0.8))
        paste(fr, CREDITS, smooth((t - 25.8) / 0.8))
    k = min(smooth(t / 0.6), 1 - smooth((t - (DUR - 0.9)) / 0.8))
    if k < 0.997:
        fr = fr.point(lambda p: int(p * k))
    return fr

if MODE == 'preview':
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    for ts in sys.argv[3:]:
        render(int(float(ts) * FPS)).resize((960, 540), Image.LANCZOS).save(out / ('p_%05.1f.png' % float(ts)))
elif MODE == 'video':
    ff, wav, outp = sys.argv[2:5]
    cmd = [ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
           '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', outp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(NF):
        p.stdin.write(render(fi).tobytes())
        if fi % 150 == 0: print(fi, flush=True)
    p.stdin.close()
    print('ffmpeg exit', p.wait())
