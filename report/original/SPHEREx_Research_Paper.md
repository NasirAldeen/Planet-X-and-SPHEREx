# A reproducible framework for exploring changes in SPHEREx sky images

Five astronomical benchmarks and a scientific specification for a public web tool

Planet X and SPHEREx project | Research and methods paper | 15 November 2026

## Abstract

Time-resolved infrared images can reveal stellar proper motion and changing source brightness, but apparent changes also arise from differences in wavelength, background, registration and detector quality. This paper develops a scientific basis for a public SPHEREx image-comparison tool using Barnard's Star, Epsilon Indi B, WISE 0855-0714, RW Aurigae and R Draconis. Published measurements are distinguished from calculations reproduced here and from proposed software capabilities. Historical proper motions imply half-year displacements of approximately 5.20, 2.35 and 4.05 arcsec for the three moving benchmarks, respectively, corresponding to less than one 6.15-arcsec SPHEREx spectral-image pixel. These scales motivate careful registration rather than a guarantee of detection. We reproduce historical WISE/Spitzer astrometry, derive magnitude changes from published RW Aur A flux ratios, and examine the sampling consequences of an approximately 246-day R Dra period. A reproducible display of two original SPHEREx DR1 cutouts provides an archive case study: the R Dra field center contains overflow, possible-error and bloom flags at both epochs, preventing an unqualified brightness measurement. The resulting specification prioritizes provenance, observation times, spectral compatibility, uncertainty and explicit invalid-data states. The contribution is a literature-grounded method and design study with an archive display demonstration; it does not establish a new astronomical discovery or a calibrated variability detection.

**Keywords:** SPHEREx; time-domain astronomy; proper motion; infrared photometry; citizen science; reproducibility.

## 1 Introduction

The Planet X and SPHEREx challenge asks for an accessible way to enter sky coordinates and inspect images of the same region over time. A useful implementation must make the comparison understandable while retaining enough information to evaluate whether a change is astronomical. The scientific question is therefore more specific than whether two pictures look different: did a source change position or flux when the observation times, wavelength responses and measurement conditions are accounted for?

The pre-launch IEEE mission overview describes SPHEREx's planned repeated all-sky spectral survey and the role of IPAC in data processing and archiving [R18]. Current archive documentation governs the products used here: spectral images and the 102-channel all-sky spectral cube serve different purposes [R07, R16]. An axis of spectral channels must never be presented as an axis of observation times.

The five requested targets span three related tests. Barnard's Star and the brown dwarfs test moving-source identification. RW Aur A tests wavelength-dependent dimming and blending. R Dra tests repeated brightness measurements, pulsation timing and data-quality handling. They are benchmarks for evaluating methods, not promises that each target will yield a valid measurement in every SPHEREx band. The paper connects these tests to a reproducible processing chain and an implementable website specification.

## 2 Evidence and study design

### 2.1 Source selection and provenance

The starting literature consists of the five papers supplied for this project [R01-R05]. Additional sources address an earlier Barnard planet interpretation, direct R Dra observations, astronomical time-series methods, image subtraction and archive interfaces [R06-R18]. IEEE Xplore was searched for SPHEREx in Brave; the visible abstract and metadata of its mission overview were reviewed, while full PDF access was unavailable. A Google Scholar search for "R Draconis" period identified an object-specific study by Osmer et al. [R17]. Original papers and official documentation supply the scientific evidence; search snippets are discovery aids. This is a targeted review rather than an exhaustive systematic survey.

Each reference has a separate record containing its citation, stable link, reading scope, evidence, limitations and saved source or clearly identified metadata note. Numerical inputs, figure data, FITS headers, scripts and checksums accompany the paper. Historical measurements retain their original dates and units. The archive demonstration uses two newly downloaded original FITS cutouts, not screenshots or precomputed website pixel values.

Three evidence classes are used throughout. **Published** results come from the cited studies. **Calculated** results are arithmetic or coordinate transformations performed here from identified inputs. **Proposed** operations describe future website behavior and validation. The FITS display is a fourth, narrowly defined activity: a reproducible rendering of archive observations without calibrated source photometry.

### 2.2 Benchmark identity and scope

| Target | Evidence used | Website test | Essential qualification |
| --- | --- | --- | --- |
| Barnard's Star | Stellar proper motion [R01] | Epoch-aware position and blink comparison | The old planet forecast is distinct from bulk stellar motion [R10] |
| Epsilon Indi B | Ba/Bb astrometry [R03] | Moving, unresolved brown-dwarf subsystem | Ba and Bb are not separately resolved by ordinary SPHEREx sampling |
| WISE 0855-0714 | Four historical positions [R04] | Motion, faintness and blended neighbors | Preserve observation epoch and upper limits |
| RW Aurigae A | Bright/dim spectra [R02] | Wavelength-dependent flux comparison | Component A can be mixed with B in coarse imaging |
| R Draconis | Visual timing and maser comparison [R05, R06, R17] | Light curves, cadence and quality rejection | Visual or radio variation is not an infrared amplitude prediction |

Table 1. The five benchmark roles. Object identity is part of the data model: Epsilon Indi Ba/Bb, a planet around the primary, and the primary star itself are different targets. R Dra must not be confused with AG Dra or R Dor.

## 3 SPHEREx data and comparison prerequisites

### 3.1 Data products and observation metadata

SPHEREx spectral images contain calibrated surface brightness, variance, flags and other extensions. Their nominal sampling is 6.15 arcsec per pixel. Six detector arrays span the survey wavelength range; the wavelength sampled at a particular position varies across a detector. A detector identifier alone therefore does not establish spectral equivalence between exposures. The all-sky cube has 102 spectral channels and a different pixel sampling of approximately 12.9 arcsec [R07].

DR1 was released in November 2026 and contains reprocessed spectral images intended to be compatible with QR3 images. Its spectral-image dataset has DOI 10.26131/IRSA678 [R16]. A client should discover available observations through IRSA's access interfaces and request cutouts for actual footprints [R08, R15]. The six-month survey description must not replace the individual observation timestamps.

| Quantity or extension | Meaning | Required treatment |
| --- | --- | --- |
| IMAGE | Surface brightness in MJy/sr | Preserve units; convert solid angle before quoting integrated flux |
| VARIANCE | Variance in (MJy/sr) squared | Retain uncertainty and account for processing covariance |
| FLAGS | Bit field describing pixel conditions | Decode named bits using the applicable release |
| ZODI | Zodiacal-light model for spectral images | Track whether subtraction has already occurred |
| Celestial WCS | Pixel to sky transformation | Include distortion; record frame and output grid |
| WCS-WAVE | Approximate local wavelength and width | Use for visualization; consult science calibration for precision work |
| MJD-AVG and TIMESYS | Exposure midpoint and time scale | Use observation time, not file creation time |

Table 2. Minimum interpretation needed for spectral-image ingestion [R07-R09]. Header content and release-specific documentation must be checked together; extension details can change between releases.

### 3.2 Spectral and spatial compatibility

Comparisons should select a common effective spectral response or explicitly disclose a mismatch. A change in a source's spectrum can produce a different image even if its physical brightness at a fixed wavelength is constant. Combining images within a detector is useful only when the wavelength coverage and weighting are specified. It produces a chosen composite response, not automatically a standard photometric filter.

The WCS-WAVE approximation is useful for display, but archive documentation distinguishes it from the calibration products needed for scientific wavelength and bandpass work [R07]. The alternate wavelength WCS must be evaluated in the raw detector coordinate convention; celestial distortion must not accidentally be applied a second time. The archive example below implements that distinction explicitly.

Spatial registration and point-spread function matching address different effects. Registration aligns sky coordinates. The point-spread function, or PSF, determines how a point source is distributed among pixels. A registered pair can still show subtraction residuals because the PSFs or backgrounds differ [R12]. The tool should expose these distinctions before offering quantitative difference images.

## 4 Astrometry and moving-source benchmarks

### 4.1 Coordinates and epochs

Right ascension in hours is converted to degrees by multiplying by 15. Declination retains its sign across degrees, arcminutes and arcseconds:

$$ (1) \alpha_{\rm deg}=15\left(h+\frac{m}{60}+\frac{s}{3600}\right),\qquad \delta_{\rm deg}=q\left(d+\frac{a}{60}+\frac{b}{3600}\right) $$

Here h, m and s are right-ascension hours, minutes and seconds; d, a and b are the nonnegative magnitudes of declination components; q is +1 or -1. This is a unit conversion, not a motion model. The supplied WISE coordinate becomes RA 133.79512917 deg and declination -7.24514722 deg. Its reference epoch is unspecified, so it is not silently treated as a current position. Coordinate frame, equinox when relevant, reference epoch and observation date are separate concepts.

A local first-order astrometric model separates secular motion from annual parallax:

$$ (2) x(t)=x_0+\mu_{\alpha *}(t-t_0)+\varpi P_\alpha(t),\qquad y(t)=y_0+\mu_\delta(t-t_0)+\varpi P_\delta(t) $$

The local east and north coordinates x and y, their fitted intercepts, and parallax varpi have angular units. Time is in years, proper motions in angle per year, and the parallax factors P are dimensionless functions of observer position and direction. The convention is mu_alpha_star = (d alpha/dt) cos(delta). The intercepts describe the model's reference position; they are not necessarily the apparent coordinates at t0 when parallax is nonzero. This model follows the usual position, proper-motion and parallax decomposition used in Chen et al. [R03]. Astropy can propagate space motion, but that operation alone is not a complete observer-dependent apparent-parallax calculation [R13]. Perspective acceleration, orbital motion and long extrapolations require a more complete model.

### 4.2 Calculated displacement scales

For a short interval and a proper-motion-only comparison, the angular displacement and pixel displacement are

$$ (3) \mu=\sqrt{\mu_{\alpha *}^2+\mu_\delta^2},\qquad \Delta\theta\simeq\mu\Delta t,\qquad \Delta p=\frac{\Delta\theta}{s_{\rm pix}} $$

The angular pixel scale s_pix must use the same angle unit as Delta theta. Equation 3 is vector geometry under constant motion. It is a planning calculation, not a detection threshold. Using the published stellar components for Barnard's Star [R01] and Epsilon Indi B [R03], and the reported total motion 8.1 +/- 0.1 arcsec/year for WISE 0855 [R04], yields Figure 1.

![Figure 1](figures/fig01_motion_scale.png)

Figure 1. Calculated displacement over 0.5 Julian year, ignoring parallax and orbital terms. Sources: R01 Table 1, R03 Table 4 and R04 Table 1/abstract. The WISE motion uncertainty alone contributes 0.05 arcsec to the half-year displacement. Error bars are omitted because they would be smaller than the plotted symbols or bars; the input uncertainties remain in the evidence file. A pixel is a sampling unit, not an astrometric precision limit.

The approximately 0.845, 0.383 and 0.659 pixel shifts for Barnard, Epsilon Indi B and WISE 0855 motivate subpixel registration and attention to signal-to-noise. They do not establish that SPHEREx can recover those shifts for every source. The 2019 Barnard paper's proposed planetary signature was conditional on an earlier candidate; later work interprets that 233-day signal as an activity alias [R10]. Neither that forecast nor its reassessment changes the distinction between bulk proper motion and a tiny orbital wobble.

### 4.3 Historical WISE imagery and astrometry

![Figure 2](sources/PIA18002.jpg)

Figure 2. An observed infrared sky image from NASA/JPL's WISE 0855 motion sequence, shown as the distributed May 2010 still frame. This is a false-color telescope image, not an artist's impression and not a SPHEREx observation. A single still does not establish motion. Credit: NASA/JPL-Caltech/Penn State University [R19]. The reference record links to the original animation and records the image-use policy [R20]. No measurement in this paper is extracted from this JPEG.

![Figure 3](figures/fig03_wise_positions.png)

Figure 3. Four published WISE/Spitzer positions from Luhman [R04, Table 2], plotted relative to the fixed numerical reference (133.795224 deg, -7.245138 deg). East offsets include cos(delta0). Bars show the tabulated positional uncertainty, 0.40 arcsec for WISE and 0.04 arcsec for Spitzer, as an approximate per-coordinate scale; no covariance was supplied. The first row defines the plotting origin numerically, rather than an error-free physical origin. No new motion/parallax fit or interpolation curve is introduced.

The plotted displacement demonstrates why a discovery-era coordinate must retain its observation date. Luhman's analysis also identifies stationary blended objects near the moving source [R04]. For website use, background catalogs should therefore remain separate from the moving-target position model. A cross-match within a fixed radius around an old coordinate can select the wrong object.

## 5 Photometry and variable-source benchmarks

### 5.1 Flux ratios and physical interpretation

For two measurements in the same calibrated photometric system, the magnitude difference is

$$ (4) \Delta m=m_2-m_1=-2.5\log_{10}\left(\frac{F_2}{F_1}\right) $$

F1 and F2 must represent positive fluxes with compatible bandpasses and zero points. The relation follows from the definition of astronomical magnitude. If a source dims, F2/F1 is below one and Delta m is positive. A nondetection remains an upper limit in flux; it should not be converted into a spurious measured magnitude.

Koutoulaki et al. compare RW Aur A spectra from a dim state on 19 March 2015 and a bright state on 30 September 2016. Reported bright-to-dim ratios are 11.8 in B and up to 2.1 in K [R02]. Equation 4 gives approximately 2.680 mag and up to 0.806 mag, respectively (Figure 4). The band difference warns against interpreting images at different wavelengths as a single light curve. The spectroscopy isolates A; coarse imaging can include the neighboring component B.

![Figure 4](figures/fig04_rw_aur_dimming.png)

Figure 4. Calculated magnitude equivalents of two historical RW Aur A flux ratios [R02, section 3.1]. The K value retains the source's "up to" qualification. These are two band summaries, not a spectrum, fitted extinction curve or SPHEREx light curve. No uncertainty bars are invented.

Under a pure absorbing-screen approximation, a transmission ratio can also be written

$$ (5) F_{\rm dim}=F_{\rm bright}e^{-\Delta\tau},\qquad \Delta\tau=\ln\left(\frac{F_{\rm bright}}{F_{\rm dim}}\right) $$

Optical-depth change Delta tau is dimensionless. Equation 5 assumes an unchanged intrinsic source and no added or scattered light along the comparison. RW Aur's near-infrared emission can include extra warm dust [R02]. Thus ln(2.1) = 0.742 is an effective attenuation example under those assumptions, not a unique measurement of dust optical depth. The website should expose the measured flux ratio first and reserve physical model interpretations for explicit analysis.

### 5.2 From surface brightness to aperture flux

An image in MJy/sr must be integrated over solid angle before it becomes a flux density. For a set A of full pixels with local background b,

$$ (6) F_\nu\,[{\rm Jy}]=10^6\sum_{i\in A}(I_i-b)\Omega_i $$

Ii and b are in MJy/sr, Omega_i is pixel solid angle in steradians, and the factor 10^6 converts MJy to Jy. Equation 6 is the discretized surface-brightness integral. A 6.15-arcsec square pixel has approximate solid angle (6.15/206265)^2 = 8.890 x 10^-10 sr, so 1 MJy/sr contributes about 0.889 mJy per pixel. Local geometry and distortion should replace this approximation in precision work. Aperture correction and contaminating neighbors remain separate concerns [R07, R14].

For independent pixel noise and an independent estimated common background with uncertainty sigma_b,

$$ (7) \sigma_F^2=10^{12}\left[\sum_{i\in A}\Omega_i^2 V_i+\left(\sum_{i\in A}\Omega_i\right)^2\sigma_b^2\right] $$

Vi is the pixel variance in (MJy/sr)^2. Equation 7 follows from linear propagation of independent errors: each intensity is multiplied by its solid angle, while the same estimated background affects every aperture pixel. Resampling introduces covariance, and background estimated from overlapping pixels is not independent. In those cases cross terms must be included, or the full measurement process must be calibrated empirically. Fractional pixel weights, correlated calibration errors and aperture-correction uncertainties are additional terms. Photutils supplies aperture operations, but software use does not remove these assumptions [R14].

### 5.3 R Draconis timing and wavelength dependence

The historical visual study by Isles and Saw reports a mean maximum-to-maximum interval of 245.32 days with 7.19-day cycle scatter over 96 intervals [R06]. The scatter is not an uncertainty of the mean. Marsakova gives a characteristic period of 246 days and a much longer O-C variation timescale of 12500 +/- 260 days [R05]. O-C denotes observed minus calculated times of maxima; its amplitude has time units, not magnitudes. These quantities describe different aspects of the variability and should occupy separate fields.

Osmer et al. provide a study specifically devoted to R Dra, comparing 22 GHz maser emission with visual photometry [R17]. The paper's phase-lag statements are internally inconsistent: its abstract and data section state about 0.2 cycle, the data section also gives about 58 days, and the conclusion states 0.1 cycle. We use it as evidence for wavelength-dependent timing and historical observations, without adopting a precise lag or transferring radio behavior to SPHEREx infrared measurements.

For a stated reference maximum t0 and period P, the phase and timing residual are

$$ (8) \phi(t)=\operatorname{frac}\left(\frac{t-t_0}{P}\right),\qquad (O-C)_E=t_{\max,E}-(t_0+EP) $$

E is an integer cycle number, frac returns the fractional part, and all times must share units and a time scale. This is the definition of phase folding and a constant-period ephemeris. It does not assert that R Dra follows a perfect clock. No contemporary t0 is inferred here.

![Figure 5](figures/fig05_r_dra_cadence.png)

Figure 5. Calculated sampling illustration using P = 246 days [R05] and hypothetical visits separated by 182.625 days. The phase origin is chosen only for the illustration. Points are not observations and no light-curve shape is assumed. A half-year step advances by 0.742 cycle; two steps advance by 0.485 cycle modulo one. Actual SPHEREx exposure times and coverage must replace this regular schedule.

With adequate valid observations, a weighted floating-mean sinusoidal model can support a period search:

$$ (9) f(t)=c+A\cos(2\pi\nu t)+B\sin(2\pi\nu t),\qquad \chi^2(\nu)=\sum_i\frac{[f_i-f(t_i)]^2}{\sigma_i^2} $$

The frequency nu has inverse-time units; c, A, B and fi have consistent flux units; sigma_i describes measurement uncertainty. Minimizing chi-squared at each frequency motivates the generalized Lomb-Scargle approach [R11]. Irregular sampling, aliases, changing pulse shape and correlated noise still matter. A periodogram peak from a few seasonal points must not be reported as a secure pulsation period. This paper does not fit a new R Dra period.

## 6 Image comparison methods

### 6.1 Registration and subtraction

Let I1 and I2 be spatially registered images at compatible spectral response. A useful explanatory subtraction model is

$$ (10) D=I_2-s(K*I_1)-B $$

K is a PSF-matching convolution kernel, s a photometric scale and B a residual-background model in image units. The asterisk denotes convolution. The model expresses the need to match image formation before interpreting residuals, following the image-subtraction framework of Alard and Lupton [R12]. The kernel convention must be stated: for example, sum K = 1 with total scaling carried by s. Saturated or invalid pixels must not become apparent variable detections.

Under independent original pixel noise and fixed fitted transformations, an illustrative variance propagation is

$$ (11) V_D\simeq V_2+s^2(K^2*V_1)+V_B,\qquad S=\frac{D}{\sqrt{V_D}} $$

K^2 means elementwise squared kernel coefficients, not a second convolution. VB is uncertainty in an independently estimated background contribution. S is a dimensionless residual statistic. Registration covariance, shared reference data and uncertainty in K or s require extra terms; spatially correlated residuals are not independent trials. Therefore S alone is not a discovery probability or a calibrated false-alarm rate. The present FITS illustration does not apply this subtraction model or claim a validated SPHEREx subtraction pipeline.

### 6.2 Combining observations

For independent measurements of the same underlying quantity, inverse-variance weighting gives

$$ (12) \bar I=\frac{\sum_j w_j I_j}{\sum_j w_j},\qquad w_j=V_j^{-1},\qquad V_{\bar I}=\left(\sum_jw_j\right)^{-1} $$

This is the minimum-variance weighted mean under the stated independent-noise model. Only positive, valid variances are eligible. A stack of a moving source on a fixed sky grid can smear it; a long stack can erase variability. Measurements at dissimilar bandpasses are not automatically estimates of the same I. The website should disclose the input dates, spectral weighting and alignment convention for every composite, and preserve the original frames for comparison.

## 7 Archive case study in the R Draconis field

### 7.1 Original inputs and processing

Two DR1 detector-3 cutouts were retrieved from IRSA at the query center RA 248.1672330721 deg, declination +66.7550238262 deg. Selection began with exposure links in the local project cache, but the scientific inputs were downloaded anew and their FITS metadata inspected. The files contain IMAGE, FLAGS, VARIANCE, ZODI, EPSF and WCS-WAVE extensions. The starting cutouts are 88 by 88 pixels. Figure 6 displays them on a common 60 by 60 grid at 6.15 arcsec per pixel, covering approximately 6.15 arcmin on each side.

| Metadata | Epoch 1 | Epoch 2 |
| --- | --- | --- |
| Observation ID | 2025W20_2D_0243_1 | 2026W19_1A_0842_1 |
| Start time UTC | 2025-05-16 22:56:23.637 | 2026-05-06 06:04:36.596 |
| Midpoint MJD in UTC | 60811.956495321 | 61166.253867532 |
| Approximate central wavelength | 1.6553 micrometres | 1.6552 micrometres |
| Approximate local width | 0.03953 micrometres | 0.03953 micrometres |
| Nearest center pixel FLAGS | 69206022 | 69206022 |

Table 3. Values read from the original cutouts or computed from their alternate wavelength WCS. Wavelengths are display approximations, not a precision proof that response functions are identical [R07]. Original URLs, checksums and complete headers are preserved in the supplementary files. Dataset: SPHEREx DR1 spectral images [R16].

The processing subtracts the supplied ZODI model, applies a conservative mask, uses the celestial TAN/SIP WCS for bilinear projection onto a north-up east-left grid, and subtracts a per-epoch median in an annulus 50 to 150 arcsec from the query center. The same asinh display limits are used for both images. A projected pixel is shown only if all contributing interpolation weight comes from eligible input pixels. The mask allows SOURCE bit 21 and FULLSAMPLE bit 12 while rejecting other set bits in this example. This is a documented display policy, not a universal archive recommendation [R09]. The annulus can contain stellar wings, so its median is not a validated precision background estimate.

![Figure 6](figures/fig06_spherex_r_dra.png)

Figure 6. Original SPHEREx observations of the R Dra field, processed as described above. Blue pixels are masked or unavailable; they do not indicate zero flux. Orange circles mark the query center. Both panels share their stretch and surface-brightness scale. Credit: SPHEREx data products, NASA/JPL-Caltech/Caltech; data supplied by IRSA, DOI 10.26131/IRSA678 [R16]. This figure is a display and quality-control example, not a calibrated light curve or a detection of variability.

### 7.2 Result and interpretation

The exposure midpoints are separated by 354.297372211 days. At the nearest native pixel to the center, FLAGS = 69206022 decomposes into bits 1, 2, 21 and 26. The release documentation identifies these as OVERFLOW, SUR_ERROR, SOURCE and BLOOM, respectively [R09]. SOURCE is informational, while the other listed conditions require caution or exclusion under the chosen policy. Both center pixels are rejected. A global exposure-quality pass would not override these local conditions.

The result establishes successful access, metadata interpretation, coordinate registration and transparent masking for this pair. It does not establish a valid R Dra total flux, a flux ratio, or a detection limit. No PSF matching, aperture correction, precision background model or empirical uncertainty calibration was performed. The broad bright structure and masked core should not be interpreted as a resolved stellar disk. A future measurement would require unsaturated usable observations or a separately validated method that models usable wings and their calibration. Empty or invalid results must remain visible to the user.

## 8 Website specification grounded in the science

![Figure 7](figures/fig07_workflow.png)

Figure 7. Proposed processing and interaction sequence. This is a software design diagram, not an implemented or benchmarked pipeline. The scientific dependencies are discussed in sections 3 to 7.

### 8.1 Query and data contract

The landing form should accept decimal or sexagesimal RA and declination, a coordinate frame, an optional reference epoch, field size, date range and a spectral selection. Validate ranges and distinguish RA degrees from RA hours. Five target presets should carry explicit identifiers and coordinate provenance; the user-supplied WISE coordinate must retain its unknown epoch until resolved. A query result should list actual available exposures rather than fabricate dates to fill an animation.

Every frame record should contain an observation identifier, release and processing version, source and cutout URL, checksum, time value and scale, detector, spatial WCS, local wavelength information, units, flags and variance availability. It should also record whether background or zodiacal light has been subtracted, the output grid, resampling method and display parameters. Preserve the immutable archive inputs separately from display products. A failed download, no coverage, missing extension and rejected measurement are distinct states.

### 8.2 Public interface and scientific controls

Blink, play, pause and manual stepping should share a fixed sky center, orientation and display stretch. The screen should show the current date, wavelength and quality state beside the image. A timeline should represent irregular gaps in observation times, even if playback uses a convenient frame rate. Users should be able to compare originals before viewing a subtraction or stack.

Flux measurements should be returned only when the aperture, background, mask, PSF treatment and uncertainty are documented. Missing or saturated samples should appear as rejected measurements or limits with reasons, never as zero-valued points. A color change caused by a detector selection should not masquerade as time variability. An on-demand spectrum should retain each sample's time and spectral response; assembling noncontemporaneous measurements of a variable object is not an instantaneous spectrum.

Catalog overlays need their own epochs, uncertainties and an association rule. Gaia or WISE positions require motion handling. Versioned permalinks should preserve coordinates, field size, dates, spectral selection, release and processing settings. A saved link must recover the original interpretation after archive updates. Exports should include the frame list and provenance alongside the image.

### 8.3 Validation before scientific claims

| Check | Evidence required to pass |
| --- | --- |
| Coordinate parsing | Known decimal/sexagesimal equivalence, including negative declination and RA wraparound |
| Time handling | Stored time scale and observation midpoint agree with the source headers |
| Spectral compatibility | Comparison selection documents the effective response and any mismatch |
| Registration | Independent stationary sources quantify residual offsets on the output grid |
| Photometry | Repeatable aperture/background method, uncertainty calibration and known-source recovery |
| Masks and invalid states | Saturated or rejected core cannot silently become a valid zero-flux datum |
| Subtraction | Constant sources and synthetic injections quantify residuals and false positives |
| Reproducibility | Exported manifest reproduces the frame selection and processing settings |

Table 4. Proposed validation gates. Thresholds should be derived from the measured data quality and the intended claim; arbitrary accuracy targets are not reported as achieved. Synthetic injections, if used later, must be labelled as simulations and kept distinct from observed sources.

Target-specific evaluation should test Barnard's predicted bulk motion with propagated coordinates, Epsilon Indi B as a blended subsystem, WISE 0855 with explicit nondetection and blending states, RW Aur with consistent spectral response and component handling, and R Dra with repeated quality-qualified flux measurements. Passing a user-interface test is different from validating an astronomical inference. No quantitative end-to-end benchmark on all five targets has been completed in this paper.

## 9 Discussion and limitations

Subpixel motion is plausible as a measurement objective, but sampling alone determines neither precision nor detectability. Accurate centroids depend on the PSF, signal-to-noise, saturation, neighbors and registration. Temporal separation can improve displacement while increasing the risk of an outdated query coordinate. The interface must therefore distinguish a target prediction from an observed source association.

Variability presents a parallel problem: two brightness values are comparable only if their measurement systems and uncertainties are understood. The RW Aur example demonstrates chromatic change, the R Dra literature demonstrates imperfect periodicity and wavelength-dependent behavior, and the archive cutouts demonstrate local data rejection. Together they motivate a tool that communicates evidence quality at the point of comparison.

The study is limited by targeted literature selection, historical catalog values and a two-exposure archive illustration. It does not measure SPHEREx fluxes for the five benchmarks, characterize completeness, resolve Epsilon Indi Ba/Bb, verify a new period, or identify a planet. The IEEE overview was used only at the level actually accessible. The internally inconsistent R Dra lag was not repaired by assumption. Future work should add calibrated per-band measurements, evaluated PSF matching, reference-source controls, coverage checks for every benchmark and user testing of how clearly uncertainty and invalid data are understood.

## 10 Conclusion

A scientifically useful SPHEREx comparison website needs to preserve the conditions under which images can be compared. The published benchmarks and reproduced calculations establish the relevant motion and variability scales, while the original R Dra cutouts show that quality flags can determine whether a measurement is meaningful. The proposed design makes coordinates and epochs, wavelength response, registration, masks, uncertainty and provenance part of the central workflow. This provides a defensible foundation for implementation and a concrete validation plan without claiming discoveries or precision that have not been demonstrated.

## Data availability and acknowledgements

The accompanying collection contains the reviewed references, bibliographic entries, numerical evidence, chart CSV files, original FITS cutouts, selected headers, image credits, processing scripts and checksum manifests. Figures 1, 3, 4 and 5 are reproducible calculations or re-plots; Figure 6 is a documented rendering of observations; Figure 7 is a proposed design. Figure 2 is an attributed NASA/JPL image [R19, R20]. No AI-generated astronomical imagery is used.

This work uses SPHEREx data products made available through IRSA. SPHEREx is jointly developed by the Jet Propulsion Laboratory and the California Institute of Technology with funding from the National Aeronautics and Space Administration. The DR1 spectral-image dataset is cited as DOI 10.26131/IRSA678 [R16]. Published astronomical measurements remain credited to their original authors.

<!-- PAGE -->
## Appendix A Equation justification and implementation boundaries

| Equations | Justification | Boundary for the website |
| --- | --- | --- |
| 1 | Angular unit conversion | Does not supply a missing epoch |
| 2 and 3 | Astrometric decomposition and vector geometry [R03, R13] | Propagation is not a complete apparent-position solution |
| 4 and 5 | Magnitude definition and exponential transmission | Compatible bandpasses; physical extinction needs extra assumptions |
| 6 and 7 | Surface-brightness integration and linear error propagation [R07, R14] | Pixel solid angle, background, covariance and aperture correction matter |
| 8 and 9 | Ephemeris definitions and weighted periodic model [R05, R06, R11] | A few visits do not establish a period |
| 10 and 11 | Matched-image subtraction and propagated variance [R12] | Fitted transformations and correlated noise need validation |
| 12 | Inverse-variance estimation of a common signal | Do not average incompatible bands or erase variability |

Table A1. The equations are established definitions or explicit statistical models. They are not newly proposed physical laws. Reference locators and assumptions are included so implementations can be checked against the quantities actually measured.

For context, the Epsilon Indi paper also illustrates why precise binary masses need resolved orbital data. In astronomical units and years, Newtonian two-body dynamics gives

$$ (13) a\,[{\rm AU}]=\frac{a_\theta}{\varpi},\qquad \frac{M_1+M_2}{M_\odot}\simeq\frac{a^3}{P^2} $$

The angular semimajor axis a_theta and parallax varpi must use identical angular units, and a is the relative orbit's semimajor axis. Using 661.58 mas, 274.99 mas and 11.0197 years from Chen et al. [R03, Table 4] gives a = 2.40583 AU and total mass approximately 0.11467 solar masses. This is a consistency calculation, not a new orbit fit. The reported component masses require the full astrometric analysis and covariance. The equation belongs to scientific background and is not a mass-estimation feature justified by a few blended SPHEREx frames.

## Appendix B Reading and implementation order

Read sections 1 and 2 for the question and evidence, then Figures 1 to 5 for the observational scales. Section 3 defines what must be preserved from the archive. Sections 4 to 6 explain why coordinate, flux and image operations need specific assumptions. Section 7 is the reproducible demonstration and its limitation. Section 8 and the companion WEBSITE_SCIENCE_SPEC.md translate the findings into development tasks and acceptance checks. Each reference ID opens a separate note in REFERENCE_INDEX.html; use the original tables or figures before reusing a numerical value.

<!-- REFERENCES -->

## References

[R01] Tal-Or, L.; Zucker, S.; Ribas, I.; Anglada-Escudé, G.; Reiners, A. (2019). Prospects for detecting the astrometric signature of Barnard’s Star b. Astronomy & Astrophysics 623, A10. [https://doi.org/10.1051/0004-6361/201834643](https://doi.org/10.1051/0004-6361/201834643)

[R02] Koutoulaki, M.; Facchini, S.; Manara, C. F.; Natta, A.; Garcia Lopez, R.; Fedriani, R.; Caratti o Garatti, A.; Coffey, D.; Ray, T. P. (2019). Exploring the dimming event of RW Aurigae A through multi-epoch VLT/X-shooter spectroscopy. Astronomy & Astrophysics 625, A49. [https://doi.org/10.1051/0004-6361/201834713](https://doi.org/10.1051/0004-6361/201834713)

[R03] Chen, M.; Li, Y.; Brandt, T. D.; Dupuy, T. J.; Cardoso, C. V.; McCaughrean, M. J. (2022). Precise Dynamical Masses of Epsilon Indi Ba and Bb: Evidence of Slowed Cooling at the L/T Transition. The Astronomical Journal; author preprint arXiv:2205.08077v1. [https://doi.org/10.3847/1538-3881/ac66d2](https://doi.org/10.3847/1538-3881/ac66d2)

[R04] Luhman, K. L. (2014). Discovery of a ~250 K Brown Dwarf at 2 pc from the Sun. The Astrophysical Journal Letters 786, L18. [https://doi.org/10.1088/2041-8205/786/2/L18](https://doi.org/10.1088/2041-8205/786/2/L18)

[R05] Marsakova, V. I. (2014). Characteristics of the period changes in Mira-type variables. Odessa Astronomical Publications 27(2), 128–130. [https://dspace.onu.edu.ua/bitstreams/1ddaa620-96ac-405b-b23a-c28e25482b04/download](https://dspace.onu.edu.ua/bitstreams/1ddaa620-96ac-405b-b23a-c28e25482b04/download)

[R06] Isles, J. E.; Saw, D. R. B. (1989). Mira Stars III: R Dra, R Gem, S Her, T Her, U Her and R Leo. Journal of the British Astronomical Association 99(4), 165–171. [https://articles.adsabs.harvard.edu/pdf/1989JBAA...99..165I](https://articles.adsabs.harvard.edu/pdf/1989JBAA...99..165I)

[R07] Caltech/IPAC-IRSA (2026). SPHEREx Data Products. SPHEREx Archive User Guide, live documentation snapshot. [https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/)

[R08] NASA/IPAC Infrared Science Archive (2026). SPHEREx Cutout Capabilities. SPHEREx Cutout Tool documentation snapshot. [https://irsa.ipac.caltech.edu/data/SPHEREx/docs/cutout_tool.html](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/cutout_tool.html)

[R09] NASA/IPAC Infrared Science Archive (2026). SPHEREx Data Explorer Help on Spectra and Flags. Online help snapshot. [https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html)

[R10] Lubin, J.; Robertson, P.; Stefansson, G.; et al. (2021). Stellar Activity Manifesting at a One-year Alias Explains Barnard b as a False Positive. The Astronomical Journal 162, 61. [https://doi.org/10.3847/1538-3881/ac0057](https://doi.org/10.3847/1538-3881/ac0057)

[R11] VanderPlas, J. T. (2018). Understanding the Lomb–Scargle Periodogram. The Astrophysical Journal Supplement Series; arXiv:1703.09824v1 (2017 preprint). [https://doi.org/10.3847/1538-4365/aab766](https://doi.org/10.3847/1538-4365/aab766)

[R12] Alard, C.; Lupton, R. H. (1998). A Method for Optimal Image Subtraction. The Astrophysical Journal 503, 325–331. [https://doi.org/10.1086/305984](https://doi.org/10.1086/305984)

[R13] The Astropy Developers (2026). Accounting for Space Motion. Astropy stable documentation snapshot. [https://docs.astropy.org/en/stable/coordinates/apply_space_motion.html](https://docs.astropy.org/en/stable/coordinates/apply_space_motion.html)

[R14] The Photutils Developers (2026). Aperture Photometry. Photutils stable documentation snapshot. [https://photutils.readthedocs.io/en/stable/user_guide/aperture.html](https://photutils.readthedocs.io/en/stable/user_guide/aperture.html)

[R15] Caltech/IPAC-IRSA (2026). SPHEREx Data Access. SPHEREx Archive User Guide, live documentation snapshot. [https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/)

[R16] NASA/IPAC Infrared Science Archive (2026). SPHEREx Data Release 1 Overview. Official release overview, accessed 2026-11-15 local time. [https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_dr1.html](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_dr1.html)

[R17] Osmer, S. J.; Benson, P. J.; Little-Marenin, I. R. (1991). Water Maser Emission and the Visual Light Curve of R Draconis. Journal of the American Association of Variable Star Observers 20, 203-207. [https://articles.adsabs.harvard.edu/pdf/1991JAVSO..20..203O](https://articles.adsabs.harvard.edu/pdf/1991JAVSO..20..203O)

[R18] Alibay, F.; Sindiy, O. V.; Jansma, P. A. T.; Reynerson, C. M.; Rice, E. B.; Rocca, J.; Susca, S.; Unwin, S. C.; Akeson, R. L.; Mihaly, S. E.; Werner, M. S. (2023). SPHEREx Preliminary Mission Overview. 2023 IEEE Aerospace Conference, Big Sky, Montana, 4-11 March 2023. Abstract and metadata reviewed; full text not accessed. [https://doi.org/10.1109/AERO55745.2023.10115793](https://doi.org/10.1109/AERO55745.2023.10115793)

[R19] NASA Jet Propulsion Laboratory (2014). Cold and Quick a Fast Moving Brown Dwarf. Photojournal image PIA18002, 25 April 2014. [https://www.jpl.nasa.gov/images/pia18002-cold-and-quick-a-fast-moving-brown-dwarf/](https://www.jpl.nasa.gov/images/pia18002-cold-and-quick-a-fast-moving-brown-dwarf/)

[R20] NASA Jet Propulsion Laboratory (n.d.). JPL Image Use Policy. Official image reuse guidance, reviewed 15 November 2026. [https://www.jpl.nasa.gov/jpl-image-use-policy/](https://www.jpl.nasa.gov/jpl-image-use-policy/)
