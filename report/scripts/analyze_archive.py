"""Verify the PlanetX_Image_Set archive and derive display arrays and quality tables.

Usage: python -I analyze_archive.py <archive_dir> <out_dir>
Reads the original FITS files only. No photometry and no target identification.
Requires numpy and astropy.
"""
import sys, json, csv, hashlib, warnings
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

warnings.simplefilter('ignore')
A = Path(sys.argv[1])
O = Path(sys.argv[2])
O.mkdir(parents=True, exist_ok=True)
T = ['Barnards_Star', 'Epsilon_Indi_B', 'WISE_0855', 'RW_Aurigae', 'R_Draconis']
N = 147
ALLOWED = (1 << 12) | (1 << 21)  # FULLSAMPLE and SOURCE are informational


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def names(hdr):
    return {int(k[4:]): hdr[k] for k in hdr if k.startswith('MSKN')}


def bits(v):
    return [b for b in range(32) if int(v) & (1 << b)]


index = {(r['target'], r['visit']): r
         for r in csv.DictReader(open(A / 'Dated_Frame_Index.csv', encoding='utf-8-sig'))}
out = {'mosaics': [], 'frames': []}
arrays = {}
for t in T:
    p = A / (t + '_mosaic.fits.gz')
    meta = json.load(open(A / t / 'Metadata.json'))
    with fits.open(p) as hd:
        h = hd['IMAGE'].header
        im = hd['IMAGE'].data.astype(float)
        nh = hd['NHITS'].data
        fl = hd['FLAGS'].data.astype(np.int64)
        ch = hd['SPECTRAL_CHANNELS'].data
        wl = np.array(ch['WAVELENGTH'], float)
        bw = np.array(ch['BANDWIDTH'], float)
        det = np.array(ch['DETECTOR'], int)
        nm = names(hd['FLAGS'].header)
        cover = np.isfinite(im) & (nh > 0)
        bad = (fl & ((1 << 1) | (1 << 19))) != 0
        valid = cover & ~bad
        c = N // 2
        ctr_over = [int(((fl[k, c - 1:c + 2, c - 1:c + 2] & 2) != 0).sum()) for k in range(102)]
        ctr_fl = [int(fl[k, c, c]) for k in range(102)]
        rec = dict(
            target=t, file=p.name, sha256=sha(p), shape=list(im.shape),
            crval=[h['CRVAL1'], h['CRVAL2']], crpix=[h['CRPIX1'], h['CRPIX2']],
            cdelt_arcsec=abs(h['CDELT2']) * 3600, field_arcmin=N * abs(h['CDELT2']) * 60,
            bunit=h['BUNIT'], nchan=h['NCHAN'], wl_min=float(wl.min()), wl_max=float(wl.max()),
            detectors=sorted(set(det.tolist())),
            date_keywords=[k for k in h if 'DATE' in k or 'MJD-' in k],
            flag_names=nm,
            coverage_fraction_by_channel=cover.mean(axis=(1, 2)).round(4).tolist(),
            valid_fraction_by_channel=valid.mean(axis=(1, 2)).round(4).tolist(),
            nhits_median_by_channel=[float(np.median(nh[k])) for k in range(102)],
            center_pixel_flags_by_channel=ctr_fl,
            center3x3_overflow_count_by_channel=ctr_over,
            channels_center_pixel_overflow=int(sum((v & 2) != 0 for v in ctr_fl)),
            channels_center3x3_any_overflow=int(sum(v > 0 for v in ctr_over)),
            center_pixel_has_value_by_channel=[bool(np.isfinite(im[k, c, c]) and nh[k, c, c] > 0) for k in range(102)],
            channels_center_pixel_nan=int(sum(not np.isfinite(im[k, c, c]) for k in range(102))),
            wavelengths=wl.round(4).tolist(), bandwidths=bw.round(4).tolist(),
            detector_by_channel=det.tolist())
        rec['sha256_matches_metadata'] = rec['sha256'] == meta.get('sha256')
        out['mosaics'].append(rec)
        for want in (1.25, 2.2, 4.6):
            k = int(np.argmin(abs(wl - want)))
            arrays[t + '__mos_%d' % k] = np.where(cover[k], im[k], np.nan).astype(np.float32)
            arrays[t + '__mosbad_%d' % k] = bad[k]
    # Dated frames, placed on the mosaic grid by nearest-neighbour sampling.
    g = WCS(naxis=2)
    g.wcs.crpix = [h['CRPIX1'], h['CRPIX2']]
    g.wcs.cdelt = [h['CDELT1'], h['CDELT2']]
    g.wcs.crval = [h['CRVAL1'], h['CRVAL2']]
    g.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    yy, xx = np.mgrid[:N, :N]
    world = g.all_pix2world(xx, yy, 0)
    for f in sorted((A / t / 'Dated_Frames').glob('*.fits')):
        v = f.name[5]
        row = index[(t, v)]
        with fits.open(f) as hd:
            h2 = hd['IMAGE'].header
            w = WCS(h2, hd).celestial
            im = np.asarray(hd['IMAGE'].data, float)
            zo = np.asarray(hd['ZODI'].data, float)
            fl = np.asarray(hd['FLAGS'].data).astype(np.int64)
            var = np.asarray(hd['VARIANCE'].data, float)
            nm = names(hd['FLAGS'].header)
            px, py = w.all_world2pix(world[0], world[1], 0)
            ix = np.rint(px).astype(int)
            iy = np.rint(py).astype(int)
            inb = (ix >= 0) & (ix < im.shape[1]) & (iy >= 0) & (iy < im.shape[0])
            ixc = np.clip(ix, 0, im.shape[1] - 1)
            iyc = np.clip(iy, 0, im.shape[0] - 1)
            sub = (im - zo)[iyc, ixc]
            fproj = fl[iyc, ixc]
            finite = np.isfinite(sub)
            strict = (fproj & ~ALLOWED) != 0
            # 0 valid, 1 flagged, 2 outside the cutout
            state = np.where(~inb, 2, np.where(strict | ~finite, 1, 0)).astype(np.uint8)
            cx, cy = [float(q) for q in w.all_world2pix(h['CRVAL1'], h['CRVAL2'], 0)]
            jx, jy = int(round(cx)), int(round(cy))
            on = (0 <= jx < im.shape[1]) and (0 <= jy < im.shape[0])
            # The alternate WCS "W" maps raw detector pixels to wavelength, so the
            # celestial SIP distortion terms must not be applied to it.
            wh = h2.copy()
            for key in list(wh):
                if key.startswith(('A_', 'B_', 'AP_', 'BP_')):
                    del wh[key]
            wave = [float(q) for q in WCS(wh, hd, key='W').all_pix2world(cx, cy, 0)]
            cf = int(fl[jy, jx]) if on else None
            b3 = fl[max(jy - 1, 0):jy + 2, max(jx - 1, 0):jx + 2] if on else np.zeros((0, 0), np.int64)
            b5 = fl[max(jy - 2, 0):jy + 3, max(jx - 2, 0):jx + 3] if on else np.zeros((0, 0), np.int64)
            census = {}
            for b in range(32):
                m = ((fproj & (1 << b)) != 0) & inb
                if m.any():
                    census[nm.get(b, str(b))] = float(m.sum() / inb.sum())
            rec = dict(
                target=t, visit=int(v), file=f.name, sha256=sha(f),
                release='QR3' if '/qr3/' in row['url'] else 'DR1',
                obs_id=h2['OBSID'], detector=int(h2['DETECTOR']), date_obs=h2['DATE-OBS'],
                mjd_avg=float(h2['MJD-AVG']), timesys=h2['TIMESYS'],
                exposure_s=float(hd['FLAGS'].header.get('XPOSURE', float('nan'))),
                bunit=h2['BUNIT'], native_shape=list(im.shape), extensions=[x.name for x in hd],
                psf_fwhm_arcsec=h2.get('PSF_FWHM'), center_pixel=[cx, cy], center_on_cutout=bool(on),
                wavelength_um=wave[0], bandwidth_um=wave[1],
                index_wavelength_um=float(row['wavelength_at_field_center_um']),
                center_flags=cf,
                center_bits=bits(cf) if cf is not None else None,
                center_names=[nm.get(b, str(b)) for b in bits(cf)] if cf is not None else None,
                center_image=float(im[jy, jx]) if on else None,
                center_minus_zodi=float((im - zo)[jy, jx]) if on else None,
                center_variance=float(var[jy, jx]) if on else None,
                box3_rejected=int(((b3 & ~ALLOWED) != 0).sum()), box3_n=int(b3.size),
                box5_rejected=int(((b5 & ~ALLOWED) != 0).sum()), box5_n=int(b5.size),
                box5_overflow=int(((b5 & 2) != 0).sum()),
                box5_names=sorted({nm.get(b, str(b)) for q in np.unique(b5) for b in bits(q)}),
                grid_valid=float((state == 0).mean()), grid_flagged=float((state == 1).mean()),
                grid_nocoverage=float((state == 2).mean()), flag_census=census)
            rec['sha256_matches_index'] = rec['sha256'] == row['sha256']
            rec['date_matches_index'] = rec['date_obs'] == row['date_obs']
            out['frames'].append(rec)
            arrays[t + '__v' + v] = np.where(inb & finite, sub, np.nan).astype(np.float32)
            arrays[t + '__s' + v] = state
np.savez_compressed(O / 'archive_display.npz', **arrays)
json.dump(out, open(O / 'archive_verification.json', 'w'), indent=1)
for m in out['mosaics']:
    print(m['target'], m['shape'], m['crval'], round(m['cdelt_arcsec'], 4), round(m['field_arcmin'], 2),
          m['wl_min'], m['wl_max'], m['detectors'], 'sha', m['sha256_matches_metadata'], 'dates', m['date_keywords'],
          'cov', min(m['coverage_fraction_by_channel']), 'valid', min(m['valid_fraction_by_channel']),
          max(m['valid_fraction_by_channel']), 'ctrOver', m['channels_center_pixel_overflow'],
          m['channels_center3x3_any_overflow'], 'nan', m['channels_center_pixel_nan'], 'nhits',
          min(m['nhits_median_by_channel']), max(m['nhits_median_by_channel']), m['flag_names'])
for r in out['frames']:
    print(r['target'], r['visit'], r['release'], r['date_obs'], r['native_shape'], 'D', r['detector'],
          round(r['wavelength_um'], 4), round(r['index_wavelength_um'], 4), round(r['bandwidth_um'], 4),
          'sha', r['sha256_matches_index'], r['date_matches_index'], 'ctr', r['center_names'],
          'b3', r['box3_rejected'], 'b5', r['box5_rejected'], r['box5_overflow'],
          'grid', round(r['grid_valid'], 3), round(r['grid_flagged'], 3), round(r['grid_nocoverage'], 3),
          'val', r['center_minus_zodi'], r['psf_fwhm_arcsec'])
