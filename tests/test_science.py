import io
import unittest
from unittest.mock import patch

import numpy as np
from astropy.io import fits

from planetx.archive import align_hdul, common_grid, discover, validate_query


class AlignmentTests(unittest.TestCase):
    def make_image(self, flipped=False):
        wcs, world, n = common_grid(150, 30, 6)
        image = np.zeros((n, n))
        image[n//2+6, n//2-7] = 100
        if flipped:
            image = image[:, ::-1]
            wcs.wcs.cdelt[0] *= -1
        hdul = fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(image, wcs.to_header(), name="IMAGE"),
                             fits.ImageHDU(np.zeros_like(image, dtype=np.int32), name="FLAGS")])
        return hdul, world, wcs.pixel_to_world(n//2, n//2), n

    def test_different_orientations_align_the_same_source(self):
        first, world, center, n = self.make_image()
        second, _, _, _ = self.make_image(True)
        a, _ = align_hdul(first, world, center)
        b, _ = align_hdul(second, world, center)
        self.assertEqual(np.nanargmax(a), np.nanargmax(b))
        self.assertAlmostEqual(np.nanmax(a), 100, places=5)

    def test_flags_do_not_become_false_positive_sources(self):
        hdul, world, center, n = self.make_image()
        hdul["FLAGS"].data[n//2+6, n//2-7] = 1
        pixels, meta = align_hdul(hdul, world, center)
        self.assertTrue(np.isnan(pixels[n//2+6, n//2-7]))
        self.assertGreater(meta["masked_fraction"], 0)
        self.assertEqual(meta["flag_values"]["1"], 1)

    def test_north_up_east_left_grid(self):
        wcs, world, n = common_grid(150, 30, 6)
        self.assertLess(world.ra.deg[n//2, -1], world.ra.deg[n//2, 0])
        self.assertGreater(world.dec.deg[-1, n//2], world.dec.deg[0, n//2])

    def test_informational_source_flags_retain_astronomical_sources(self):
        hdul, world, center, n = self.make_image()
        hdul['FLAGS'].data[:] = (1 << 21) | (1 << 12)
        pixels, _ = align_hdul(hdul, world, center)
        self.assertAlmostEqual(np.nanmax(pixels),100,places=5)

    def test_invalid_coordinate_inputs_are_rejected(self):
        for args in [(360,0,6,"D3"),(0,91,6,"D3"),(0,0,100,"D3"),
                     (float('nan'),0,6,"D3"),(0,0,6,"D7"),(0,float('inf'),6,"D1")]:
            with self.assertRaises(ValueError): validate_query(*args)

    @patch("planetx.archive.request_bytes")
    def test_sia_column_names_take_precedence_over_ids(self, download):
        download.return_value = b'''<?xml version="1.0"?><VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3"><RESOURCE><TABLE>
        <FIELD name="energy_bandpassname" ID="col_0" datatype="char" arraysize="*"/>
        <FIELD name="access_url" ID="col_1" datatype="char" arraysize="*"/>
        <FIELD name="t_min" ID="col_2" datatype="double"/>
        <FIELD name="obs_id" ID="col_3" datatype="char" arraysize="*"/>
        <DATA><TABLEDATA><TR><TD>SPHEREx-D3</TD><TD>https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/a.fits</TD><TD>60000</TD><TD>test</TD></TR></TABLEDATA></DATA>
        </TABLE></RESOURCE></VOTABLE>'''
        rows, notices = discover(10, 20, "D3", collections=("spherex_dr1",))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["mjd"], 60000)
        self.assertEqual(notices, [])


if __name__ == "__main__": unittest.main()
