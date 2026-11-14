"""Record SIMBAD Sesame coordinates, proper motions, and raw provenance."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ("barnard", "Barnard’s Star", "Barnard's star", "Fast-moving nearby star", "D3",
     "Look for a small position shift against the background. Its bright core may be masked by quality flags."),
    ("epsilon-indi", "Epsilon Indi B", "eps Ind B", "Brown dwarf pair", "D3",
     "The brown dwarf pair is unresolved at SPHEREx resolution. Look for the system’s motion, not two separate points."),
    ("wise-0855", "WISE 0855", "WISE J085510.83-071442.5", "Cold, fast-moving brown dwarf", "D6",
     "A very faint target. The challenge’s supplied position is retained; low signal is not evidence of absence."),
    ("rw-aurigae", "RW Aurigae", "RW Aur", "Young variable star", "D3",
     "Compare brightness at similar wavelengths. Dust, image quality, and saturation can imitate variability."),
    ("r-draconis", "R Draconis", "R Dra", "Mira variable star", "D3",
     "Look for brightness changes at a stable position. Check wavelength and flags before interpreting the change."),
]


def main():
    out = ROOT / "public/data"
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for slug, name, query, kind, detector, hint in TARGETS:
        params = {"output.format": "VOTable", "Ident": query}
        # Sesame includes the reference-epoch coordinates and proper motions.
        url = "https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/SNV?" + requests.utils.quote(query)
        response = requests.get(url, timeout=35)
        response.raise_for_status()
        (out / (slug + "-resolver.xml")).write_text(response.text, encoding="utf-8")
        xml = ET.fromstring(response.content)
        resolver = xml.find(".//Resolver[jradeg]")
        if resolver is None:
            raise RuntimeError(f"No SIMBAD position for {name}")
        ra, dec = float(resolver.findtext("jradeg")), float(resolver.findtext("jdedeg"))
        reference_ra, reference_dec = ra, dec
        pmra = float(resolver.findtext("pm/pmRA", "0"))
        pmdec = float(resolver.findtext("pm/pmDE", "0"))
        if slug != "wise-0855":
            coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, pm_ra_cosdec=pmra*u.mas/u.yr,
                             pm_dec=pmdec*u.mas/u.yr, obstime=Time("J2000"))
            moved = coord.apply_space_motion(Time("J2026"))
            ra, dec = moved.ra.deg, moved.dec.deg
        else:
            ra, dec = (8+55/60+10.831/3600)*15, -(7+14/60+42.53/3600)
        record = dict(id=slug, name=name, kind=kind, detector=detector, hint=hint,
                      ra=ra, dec=dec, fov=6, reference_ra=reference_ra, reference_dec=reference_dec,
                      pm_ra_cosdec=pmra, pm_dec=pmdec, source_url=url,
                      coordinate_note="Challenge-supplied fixed position" if slug == "wise-0855" else
                      "SIMBAD J2000 position propagated linearly to J2026 using catalog proper motion; no parallax correction")
        records.append(record)
        print(json.dumps(record, ensure_ascii=True), flush=True)
    (out / "targets.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
