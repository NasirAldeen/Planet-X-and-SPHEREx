# Scientific methodology and limits

## Processing

1. Validate fixed ICRS coordinates, field size and detector; query IRSA SIA2
   for DR1 and QR3 spectral images covering the field center.
2. Deduplicate observation ID and detector, preferring DR1 on overlap. Select
   up to 18 evenly spaced indices from the chronological exposure list.
3. Download FITS cutouts 1.5 times the display width to leave a rotation margin.
   TLS verification, retries and response-size limits are enabled.
4. Use Astropy celestial TAN/SIP WCS and bilinear sampling to align to a common
   grid. North increases with FITS row; canvas rows are flipped to show North
   up. East is left. Sampling is approximately 6.15 arcsec, not artificial
   super-resolution.
5. Retain informational `SOURCE` (21) and `FULLSAMPLE` (12) flags; mask all other
   set bits, nonfinite pixels and interpolation footprints containing bad pixels.
   Raw flag-value counts remain in each frame’s metadata.
6. Subtract ZODI when available and remove each frame’s usable-pixel median sky.
   This is display background correction, not a fitted precision sky model.
7. Evaluate `WCS-WAVE` at field center. Remove spatial SIP coefficients from the
   independent spectral transform, following IRSA’s convention of disabling SIP
   for spectral WCS. Preserve measured wavelength and bandwidth.
8. Save aligned intensities rounded to six significant digits, explicit `null`
   masks, timestamps, original FITS URLs, units, flags and processing versions.

## Comparison rules

Wavelength matching accepts center wavelengths within 5% of a reference. The
default reference maximizes matched baseline, then frame count. Missing wavelength
measurements never silently match. This tolerance is a quick-look heuristic:
bandpass response and wavelength vary spatially, so center matching does not
guarantee an equal bandpass everywhere in the image or along a moving object’s path.

Selected frames use one shared asinh stretch, avoiding independent per-frame
contrast normalization. Playback intervals are uniform; real elapsed times vary
and are shown by observation dates and the time baseline.

- **Blink:** individual chronological exposures.
- **Split:** reference left, current exposure right, adjustable divider.
- **Difference:** current minus reference background-subtracted surface brightness;
  positive is orange, negative blue. Invalid overlap is masked. The symmetric
  color stretch is not a significance or signal-to-noise map.
- **Stack:** arithmetic mean of valid selected pixels. Coverage varies per pixel.
  It is not inverse-variance weighted or aligned on a moving source, which can smear.

No PSF matching, fitted photometry, propagated astrometric uncertainties, automatic
classification, orbit fitting or source detection is implemented. Variance and
PSF products remain in the linked original FITS, but are not propagated through a
quantitative estimator. Differences in PSF, masks, calibration or backgrounds can
imitate motion and variability. The app presents visual evidence for investigation,
not confirmed discoveries or precision measurements.

## Target positions

CDS Sesame/SIMBAD supplies reference coordinates and proper motions; raw resolver
XML is bundled. Four target positions are propagated linearly from J2000 to
J2026 to center a fixed field. Barnard’s Star and Epsilon Indi B especially need
this correction. No epoch-by-epoch source tracking, parallax or perspective
correction is performed.

WISE 0855 retains the exact challenge position **08h55m10.831s, −07°14′42.53″**.
The crosshair marks field center, not a measured source centroid. Epsilon Indi B’s
components are unresolved at this sampling. Downloading images of a field does
not prove the named source is detectable in every exposure; faintness and
saturation are relevant limitations.

## References

- [IRSA spectral-image tutorial](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/)
- [IRSA cutout tutorial](https://github.com/Caltech-IPAC/irsa-tutorials/blob/main/tutorials/spherex/spherex_cutouts.md)
- [SPHEREx data access](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/)
- [IRSA flag definitions](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html)
- [SPHEREx explanatory supplement](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)
