#!/usr/bin/env python
""" """

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2012 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import unittest
import logging
import os
from math import radians

# Third party modules.

# Local modules.
from pymontecarlo.testcase import TestCase

from pymontecarlo.options.options import Options
from pymontecarlo.options.detector import \
    (PhotonSpectrumDetector,
     PhotonIntensityDetector,
     PhotonDepthDetector,
     ElectronFractionDetector,
     TimeDetector,
     ShowersStatisticsDetector,
     BackscatteredElectronEnergyDetector,
     TransmittedElectronEnergyDetector)
from pymontecarlo.program.penepma.importer import Importer

# Globals and constants variables.

class TestImporter(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        self.testdata = os.path.join(os.path.dirname(__file__),
                                     'testdata', 'test1')

        self.i = Importer()

    def tearDown(self):
        TestCase.tearDown(self)

    def testskeleton(self):
        self.assertTrue(True)

    def test_detector_photon_intensity(self):
        # Create
        ops = Options(name='test1')
        ops.beam.energy_eV = 20e3
        ops.detectors['xray1'] = \
            PhotonIntensityDetector((radians(35), radians(45)), (0, radians(360.0)))
        ops.detectors['xray2'] = \
            PhotonIntensityDetector((radians(-45), radians(-35)), (0, radians(360.0)))

        # Import
        resultscontainer = self.i.import_(ops, self.testdata)

        # Test
#        self.assertEqual(2, len(resultscontainer))

        result = resultscontainer['xray2']

        val, unc = result.intensity('W Ma1')
        self.assertAlmostEqual(6.07152e-05, val, 9)
        self.assertAlmostEqual(2.23e-06, unc, 9)

        val, unc = result.intensity('W Ma1', fluorescence=False)
        self.assertAlmostEqual(5.437632e-05, val, 9)
        self.assertAlmostEqual(2.12e-06, unc, 9)

        val, unc = result.intensity('W Ma1', absorption=False)
        self.assertAlmostEqual(5.521557e-4, val, 9)
        self.assertAlmostEqual(4.79e-06, unc, 9)

        val, unc = result.intensity('W Ma1', absorption=False, fluorescence=False)
        self.assertAlmostEqual(4.883132e-4, val, 9)
        self.assertAlmostEqual(4.45e-06, unc, 9)

    def test_detector_photon_spectrum(self):
        # Create
        ops = Options(name='test1')
        ops.beam.energy_eV = 20e3
        ops.detectors['spectrum'] = \
            PhotonSpectrumDetector((radians(35), radians(45)), (0, radians(360.0)),
                                   1000, (0, 20e3))

        # Import
        resultscontainer = self.i.import_(ops, self.testdata)

        # Test
        self.assertEqual(1, len(resultscontainer))

        result = resultscontainer['spectrum']

        total = result.get_total()
        self.assertEqual(1000, len(total))
        self.assertAlmostEqual(10.0, total[0, 0], 4)
        self.assertAlmostEqual(19990.0, total[-1, 0], 4)
        self.assertAlmostEqual(2.841637e-6, total[31, 1], 10)
        self.assertAlmostEqual(8.402574e-6, total[31, 2], 10)

        background = result.get_background()
        self.assertEqual(1000, len(background))
        self.assertAlmostEqual(10.0, background[0, 0], 4)
        self.assertAlmostEqual(19990.0, background[-1, 0], 4)
        self.assertAlmostEqual(0.0, background[31, 1], 10)
        self.assertAlmostEqual(0.0, background[31, 2], 10)

    def test_detector_photon_depth(self):
        # Create
        ops = Options(name='test1')
        ops.beam.energy_eV = 20e3
        ops.detectors['prz'] = \
            PhotonDepthDetector((radians(35), radians(45)), (0, radians(360.0)), 100)

        # Import
        resultscontainer = self.i.import_(ops, self.testdata)

        # Test
        self.assertEqual(1, len(resultscontainer))

        result = resultscontainer['prz']

        self.assertTrue(result.exists('Cu La1', absorption=True))
        self.assertTrue(result.exists('Cu La1', absorption=False))
        self.assertFalse(result.exists('Cu Ka1', absorption=True))

        dist = result.get('Cu La1', absorption=False)
        self.assertAlmostEqual(-5.750000e-7, dist[2, 0], 4)
        self.assertAlmostEqual(4.737908e-6, dist[2, 1], 4)
        self.assertAlmostEqual(1.005021e-5, dist[2, 2], 4)

        dist = result.get('Cu La1', absorption=True)
        self.assertAlmostEqual(-5.150000e-7, dist[8, 0], 4)
        self.assertAlmostEqual(4.228566e-5, dist[8, 1], 4)
        self.assertAlmostEqual(1.268544e-4, dist[8, 2], 4)

    def test_detector_electron_fraction(self):
        # Create
        ops = Options(name='test1')
        ops.beam.energy_eV = 20e3
        ops.detectors['fraction'] = ElectronFractionDetector()

        # Import
        resultscontainer = self.i.import_(ops, self.testdata)

        # Test
        self.assertEqual(1, len(resultscontainer))

        result = resultscontainer['fraction']

        self.assertAlmostEqual(0.5168187, result.backscattered[0], 4)
        self.assertAlmostEqual(7.5e-3, result.backscattered[1], 6)

        self.assertAlmostEqual(0.0, result.transmitted[0], 4)
        self.assertAlmostEqual(0.0, result.transmitted[1], 4)

        self.assertAlmostEqual(0.5113858, result.absorbed[0], 4)
        self.assertAlmostEqual(5.4e-3, result.absorbed[1], 6)

    def test_detector_time(self):
        # Create
        ops = Options(name='test1')
        ops.beam.energy_eV = 20e3
        ops.detectors['time'] = TimeDetector()

        # Import
        resultscontainer = self.i.import_(ops, self.testdata)

        # Test
        self.assertEqual(1, len(resultscontainer))

        result = resultscontainer['time']

        self.assertAlmostEqual(8.993401e1, result.simulation_time_s, 4)
        self.assertAlmostEqual(1.0 / 8.554940e2, result.simulation_speed_s[0], 4)

    def test_detector_showers_statistics(self):
        # Create
        ops = Options(name='test1')
        ops.beam.energy_eV = 20e3
        ops.detectors['showers'] = ShowersStatisticsDetector()

        # Import
        resultscontainer = self.i.import_(ops, self.testdata)

        # Test
        self.assertEqual(1, len(resultscontainer))

        result = resultscontainer['showers']

        self.assertEqual(76938, result.showers)

    def test_detector_backscattered_electron_energy(self):
        # Create
        ops = Options(name='test1')
        ops.beam.energy_eV = 20e3
        ops.detectors['bse'] = \
            BackscatteredElectronEnergyDetector(100, (0.0, 20e3))

        # Import
        resultscontainer = self.i.import_(ops, self.testdata)

        # Test
        self.assertEqual(1, len(resultscontainer))

        result = resultscontainer['bse']

        self.assertEqual(1000, len(result))

    def test_detector_transmitted_electron_energy(self):
        # Create
        ops = Options(name='test1')
        ops.beam.energy_eV = 20e3
        ops.detectors['transmitted'] = \
            TransmittedElectronEnergyDetector(100, (0.0, 20e3))

        # Import
        resultscontainer = self.i.import_(ops, self.testdata)

        # Test
        self.assertEqual(1, len(resultscontainer))

        result = resultscontainer['transmitted']

        self.assertEqual(1000, len(result))

if __name__ == '__main__': #pragma: no cover
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
