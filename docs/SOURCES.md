# Sources, attribution and licenses

| Source | Use |
| --- | --- |
| [Space Apps challenge](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/) | Requirements supplied by the project owner; five required test targets. |
| [NASA/IPAC IRSA SPHEREx](https://irsa.ipac.caltech.edu/Missions/spherex.html) | Real calibrated FITS images and archive metadata; individual URLs are recorded per frame. |
| [IRSA data-access guide](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/) | SIA2 collections and cutout conventions. |
| [IRSA tutorials](https://github.com/Caltech-IPAC/irsa-tutorials) | Spatial and spectral WCS guidance; implementation is original project code. |
| [IRSA flags](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html) | Flag interpretation. |
| [CDS Sesame](https://cds.unistra.fr/cgi-bin/Sesame) / [SIMBAD](https://simbad.cds.unistra.fr/simbad/) | Reference positions and proper motions; raw XML responses are included. |

Credit: This research has made use of the NASA/IPAC Infrared Science Archive,
which is funded by the National Aeronautics and Space Administration and operated
by the California Institute of Technology. It also uses the SIMBAD database,
operated at CDS, Strasbourg, France.

The MIT license covers original code, not a relicensing of IRSA or SIMBAD data.
Review [IRSA acknowledgments](https://irsa.ipac.caltech.edu/ack.html) and release
documentation for publication-specific citations. No NASA logo is used. The
orbital icon is an original SVG.

## Direct software dependencies

Versions are pinned in `requirements.txt`. Upstream licenses and dependency
notices ship with installed packages and are not replaced by this project’s license.

| Software | Upstream | License family |
| --- | --- | --- |
| Python | https://www.python.org/ | PSF |
| Astropy | https://www.astropy.org/ | BSD 3-Clause |
| NumPy | https://numpy.org/ | BSD 3-Clause |
| SciPy | https://scipy.org/ | BSD 3-Clause |
| Requests | https://requests.readthedocs.io/ | Apache 2.0 |
| Flask | https://flask.palletsprojects.com/ | BSD 3-Clause |
| Waitress | https://docs.pylonsproject.org/projects/waitress/ | ZPL 2.1 |
| Node.js (test tooling) | https://nodejs.org/ | MIT and bundled notices |

No third-party frontend JavaScript, external fonts, analytics, tracking pixels
or generated astronomical assets are used.
