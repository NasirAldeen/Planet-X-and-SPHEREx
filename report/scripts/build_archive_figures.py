"""Draw the report's archive figures from data/archive_display.npz and
data/archive_verification.json (both written by analyze_archive.py).

Every pixel shown comes from an original IRSA FITS file. Flagged pixels and
pixels outside a cutout are drawn in their own colours and are never filled in.
Requires numpy and matplotlib.
"""
from pathlib import Path
import sys, json, csv
P = Path(__file__).resolve().parents[1]
for extra in (P.parent / 'Paper/.work/deps', P.parent / '.work/deps'):
    if extra.exists():
        sys.path.insert(0, str(extra))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, FancyArrowPatch, FancyBboxPatch

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9.5, 'savefig.dpi': 220,
                     'axes.titleweight': 'bold', 'axes.titlesize': 9.5})
F = P / 'figures'
D = P / 'data'
Z = np.load(D / 'archive_display.npz')
V = json.loads((D / 'archive_verification.json').read_text(encoding='utf-8'))
FR = {(f['target'], f['visit']): f for f in V['frames']}
MO = {m['target']: m for m in V['mosaics']}
NAME = {'Barnards_Star': "Barnard's Star", 'Epsilon_Indi_B': 'Epsilon Indi B', 'WISE_0855': 'WISE 0855',
        'RW_Aurigae': 'RW Aurigae', 'R_Draconis': 'R Draconis'}
N = 147
SCALE = 6.15
HALF = N * SCALE / 60 / 2            # half field in arcmin
EXT = [HALF, -HALF, -HALF, HALF]     # east to the left, north up
FLAG = '#7fb2d6'                     # flagged or rejected pixel
NOCOV = '#5b4a3a'                    # outside the cutout: no data
INK = '#1a1a1a'


def save(fig, name):
    fig.savefig(F / (name + '.png'), bbox_inches='tight', facecolor='white')
    plt.close(fig)


def stretch(x, lo, hi):
    soft = max((hi - lo) * 0.08, 1e-9)
    y = np.arcsinh((x - lo) / soft) / np.arcsinh((hi - lo) / soft)
    return np.clip(y, 0, 1)


def draw(ax, img, flagged, nocov, lo, hi, half=None):
    """Greyscale image with flagged pixels and no-data pixels in flat colours."""
    ax.imshow(stretch(img, lo, hi), origin='lower', cmap='gray', vmin=0, vmax=1, extent=EXT,
              interpolation='nearest')
    for mask, colour in ((flagged, FLAG), (nocov, NOCOV)):
        layer = np.ma.masked_where(~mask, np.ones(mask.shape))
        ax.imshow(layer, origin='lower', cmap=ListedColormap([colour]), extent=EXT, interpolation='nearest')
    lim = half or HALF
    ax.set_xlim(lim, -lim)
    ax.set_ylim(-lim, lim)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color('#888888')


def scalebar(ax, arcmin, half=None):
    lim = half or HALF
    x0 = -lim * 0.90
    y0 = -lim * 0.86
    ax.plot([x0 + arcmin, x0], [y0, y0], color='white', lw=2.2, solid_capstyle='butt')
    ax.text(x0 + arcmin / 2, y0 + lim * 0.05, '%g arcmin' % arcmin, color='white', ha='center', va='bottom',
            fontsize=8)


def centre_ticks(ax, half=None, colour='#ff8a3d'):
    lim = half or HALF
    a, b = lim * 0.07, lim * 0.2
    for (x1, x2, y1, y2) in ((a, b, 0, 0), (-a, -b, 0, 0), (0, 0, a, b), (0, 0, -a, -b)):
        ax.plot([x1, x2], [y1, y2], color=colour, lw=1.3)


def legend(fig, y, extra=(), flag='flagged pixel (not used)', nocov='outside this cutout (no data)'):
    handles = [Patch(color=FLAG, label=flag), Patch(color=NOCOV, label=nocov)] + list(extra)
    fig.legend(handles=handles, loc='lower center', ncol=len(handles), frameon=False, fontsize=8.5,
               bbox_to_anchor=(0.5, y))


def frames(t):
    out = []
    for v in (1, 2, 3):
        img = Z['%s__v%d' % (t, v)].astype(float)
        st = Z['%s__s%d' % (t, v)]
        ok = st == 0
        img = img - np.nanmedian(img[ok])       # per-frame median of accepted pixels
        out.append((img, st == 1, st == 2, ok, FR[(t, v)]))
    pooled = np.concatenate([i[o] for i, _, _, o, _ in out])
    lo, hi = np.percentile(pooled, [1, 99.5])
    return out, lo, hi


# ---- Figure 1: how the tool operates -----------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.2, 3.5))
ax.set_xlim(0, 100)
ax.set_ylim(0, 44)
ax.axis('off')


def box(x, y, w, h, title, body, face='white'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3', fc=face, ec='#4a4a4a', lw=1))
    ax.text(x + w / 2, y + h - 2.6, title, ha='center', va='top', fontweight='bold', fontsize=9, color=INK)
    ax.text(x + w / 2, y + h - 6.6, body, ha='center', va='top', fontsize=8.3, color=INK, linespacing=1.35)


def arrow(p, q):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='->', mutation_scale=13, color='#195377', lw=1.6))


box(0.5, 15, 20, 14, '1  Sky position', 'RA and Dec, or one\nof five targets')
box(25, 15, 20, 14, '2  Real exposures', 'IRSA files with their\nown dates and\nwavelengths')
box(49.5, 15, 20, 14, '3  Quality screen', 'flags and coverage\nchecked per pixel')
box(75, 26, 24.5, 15, '4a  Time view', 'one image per observing\ndate, same sky grid and\nbrightness scale', '#eef4f8')
box(75, 3, 24.5, 15, '4b  Wavelength view', '102 channels of one\ncombined mosaic,\nno observing date', '#f6f1ea')
arrow((21, 22), (24.5, 22))
arrow((45.5, 22), (49, 22))
arrow((70, 24.5), (74.5, 31.5))
arrow((70, 19.5), (74.5, 12.5))
ax.text(35, 10, 'every image keeps its source link and checksum;\nrejected pixels stay visible as rejected',
        ha='center', va='top', fontsize=8.3, style='italic', color='#333333')
save(fig, 'fig01_how_it_works')

# ---- Figure 2: wavelength view (mosaic channels of one field) -----------------------------------
t = 'Barnards_Star'
m = MO[t]
planes = sorted(int(k.split('_')[-1]) for k in Z.files if k.startswith(t + '__mos_'))
fig, axs = plt.subplots(1, 3, figsize=(8.2, 3.25))
fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.12, wspace=0.04)
for ax, k in zip(axs, planes):
    img = Z['%s__mos_%d' % (t, k)].astype(float)
    bad = Z['%s__mosbad_%d' % (t, k)]
    nocov = ~np.isfinite(img)
    ok = ~bad & ~nocov
    lo, hi = np.percentile(img[ok], [1, 99.5])
    draw(ax, np.nan_to_num(img), bad & ~nocov, nocov, lo, hi)
    scalebar(ax, 3)
    ax.set_title('channel %d of 102\n%.3f µm (width %.3f µm)' % (k + 1, m['wavelengths'][k], m['bandwidths'][k]))
legend(fig, -0.01, flag='OVERFLOW or OUTLIER flag set', nocov='no value stored in the mosaic')
save(fig, 'fig02_wavelength_view')

# ---- Figure 3: time view (three dates of one field, shared stretch) -----------------------------
t = 'WISE_0855'
fs, lo, hi = frames(t)
fig, axs = plt.subplots(1, 3, figsize=(8.2, 3.25))
fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.12, wspace=0.04)
for ax, (img, fl, nc, ok, r) in zip(axs, fs):
    draw(ax, np.nan_to_num(img), fl, nc, lo, hi)
    scalebar(ax, 3)
    centre_ticks(ax)
    ax.set_title('%s UTC\n%.3f µm at field centre' % (r['date_obs'][:10], r['wavelength_um']))
legend(fig, -0.01, [plt.Line2D([], [], color='#ff8a3d', marker='+', ls='', ms=9, mew=1.4,
                               label='requested coordinate (not a detection)')])
save(fig, 'fig03_time_view')
stretch_log = {'WISE_0855_time_view': [float(lo), float(hi)]}

# ---- Figure 4: quality screen (centres of RW Aurigae and R Draconis, three dates each) ---------
ZOOM = 2.6
fig, axs = plt.subplots(2, 3, figsize=(7.4, 5.35))
fig.subplots_adjust(left=0.07, right=0.99, top=0.92, bottom=0.085, wspace=0.04, hspace=0.2)
for row, t in enumerate(('RW_Aurigae', 'R_Draconis')):
    fs, lo, hi = frames(t)
    stretch_log[t + '_quality'] = [float(lo), float(hi)]
    for ax, (img, fl, nc, ok, r) in zip(axs[row], fs):
        draw(ax, np.nan_to_num(img), fl, nc, lo, hi, half=ZOOM)
        scalebar(ax, 1, half=ZOOM)
        centre_ticks(ax, half=ZOOM)
        ax.set_title('%s UTC, %.3f µm' % (r['date_obs'][:10], r['wavelength_um']))
    axs[row][0].set_ylabel(NAME[t] + ' field', fontsize=10, fontweight='bold')
legend(fig, -0.005, [plt.Line2D([], [], color='#ff8a3d', marker='+', ls='', ms=9, mew=1.4,
                                label='requested coordinate')])
save(fig, 'fig04_quality_screen')

# ---- Figure 5: centre pixel of each mosaic, channel by channel ---------------------------------
order = ['Barnards_Star', 'Epsilon_Indi_B', 'WISE_0855', 'RW_Aurigae', 'R_Draconis']
grid = np.zeros((5, 102), int)
for i, t in enumerate(order):
    m = MO[t]
    for k in range(102):
        if not m['center_pixel_has_value_by_channel'][k]:
            grid[i, k] = 2          # no value stored
        elif m['center_pixel_flags_by_channel'][k] & 2:
            grid[i, k] = 1          # OVERFLOW flag set
fig, ax = plt.subplots(figsize=(8.2, 2.5))
fig.subplots_adjust(left=0.17, right=0.99, top=0.9, bottom=0.36)
cmap = ListedColormap(['#2f7d5b', '#d9822b', '#c9c9c9'])
ax.imshow(grid, aspect='auto', cmap=cmap, vmin=0, vmax=2, interpolation='nearest', extent=[0.5, 102.5, 5, 0])
for y in range(1, 5):
    ax.axhline(y, color='white', lw=2)
ax.set_yticks(np.arange(5) + 0.5, [NAME[t] for t in order])
wl = MO[order[0]]['wavelengths']
ticks = [1, 18, 35, 52, 69, 86, 102]
ax.set_xticks(ticks, ['%d\n%.2f µm' % (k, wl[k - 1]) for k in ticks])
ax.set_xlabel('mosaic channel and its wavelength')
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
counts = [(int((grid[i] == 0).sum()), int((grid[i] == 1).sum()), int((grid[i] == 2).sum())) for i in range(5)]
fig.legend(handles=[Patch(color='#2f7d5b', label='value present, no overflow flag'),
                    Patch(color='#d9822b', label='value present but OVERFLOW flag set'),
                    Patch(color='#c9c9c9', label='no value stored')],
           loc='lower center', ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.55, -0.02))
save(fig, 'fig05_mosaic_centre')
with (D / 'mosaic_centre_counts.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['target', 'channels_usable', 'channels_overflow_flag', 'channels_no_value'])
    for t, c in zip(order, counts):
        w.writerow([t, *c])
(D / 'display_limits.json').write_text(json.dumps(stretch_log, indent=1), encoding='utf-8')
print(counts)
