#!/usr/bin/env python
"""
================================================================================
:mod:`importer` -- PENEPMA importer
================================================================================

.. module:: importer
   :synopsis: PENEPMA importer

.. inheritance-diagram:: pymontecarlo.program.penepma.output.importer

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2012 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import os
import re
import glob

# Third party modules.
import numpy as np

from pyxray.transition import Transition
from pyxray.subshell import Subshell

# Local modules.
from pymontecarlo.results.result import \
    (PhotonKey,
     PhotonIntensityResult,
     PhotonSpectrumResult,
     PhotonDepthResult,
     ElectronFractionResult,
     TimeResult,
     ShowersStatisticsResult,
     BackscatteredElectronEnergyResult,
     TransmittedElectronEnergyResult,
    )
from pymontecarlo.options.detector import \
    (
     _PhotonDelimitedDetector,
     BackscatteredElectronEnergyDetector,
     TransmittedElectronEnergyDetector,
     PhotonSpectrumDetector,
     PhotonIntensityDetector,
     PhotonDepthDetector,
     ElectronFractionDetector,
     TimeDetector,
     ShowersStatisticsDetector,
     )
from pymontecarlo.program.importer import Importer as _Importer, ImporterException
from pymontecarlo.program.penepma.options.detector import index_delimited_detectors

# Globals and constants variables.

def _load_dat_files(filepath):
    bins = []
    vals = []
    uncs = []

    with open(filepath, 'r') as fp:
        for line in fp:
            line = line.strip()
            if line.startswith('#'): continue
            if not line: continue
            values = line.split()

            bins.append(float(values[0]))
            vals.append(float(values[1]))
            uncs.append(float(values[2]))

    return bins, vals, uncs

class Importer(_Importer):

    def __init__(self):
        _Importer.__init__(self)

        self._importers[PhotonSpectrumDetector] = \
            self._import_photon_spectrum
        self._importers[PhotonIntensityDetector] = self._import_photon_intensity
        self._importers[ElectronFractionDetector] = \
            self._import_electron_fraction
        self._importers[TimeDetector] = self._import_time
        self._importers[ShowersStatisticsDetector] = \
            self._import_showers_statistics
        self._importers[BackscatteredElectronEnergyDetector] = \
            self._import_backscattered_electron_energy
        self._importers[TransmittedElectronEnergyDetector] = \
            self._import_transmitted_electron_energy
        self._importers[PhotonDepthDetector] = \
            self._import_photon_depth

    def _import(self, options, dirpath, *args, **kwargs):
        # Find index for each delimited detector
        # The same method (index_delimited_detectors) is called when exporting
        # the result. It ensures that the same index is used for all detectors
        dets = dict(options.detectors.iterclass(_PhotonDelimitedDetector))
        phdets_key_index, phdets_index_keys = index_delimited_detectors(dets)

        return self._run_importers(options, dirpath,
                                   phdets_key_index, phdets_index_keys,
                                   *args, **kwargs)

    def _import_photon_spectrum(self, options, key, detector, path,
                                  phdets_key_index, phdets_index_keys, *args):
        index = phdets_key_index[key] + 1

        # Find data files
        spect_filepath = os.path.join(path, 'pe-spect-%s.dat' % str(index).zfill(2))
        if not os.path.exists(spect_filepath):
            raise ImporterException("Data file %s cannot be found" % spect_filepath)

        # Load total spectrum
        energies, total_val, total_unc = _load_dat_files(spect_filepath)
        total = np.array([energies, total_val, total_unc]).T

        # Generate fake background
        background = np.zeros(total.shape)
        background[:, 0] = energies

        return PhotonSpectrumResult(total, background)

    def _import_photon_intensity(self, options, key, detector, path,
                                   phdets_key_index, phdets_index_keys, *args):
        def _read_intensities_line(line):
            values = line.split()

            try:
                z = int(values[0])
                src = Subshell(z, iupac=values[2].strip())
                dst = Subshell(z, iupac=values[1].strip())
                transition = Transition(z, src, dst)
            except ValueError: # transition not supported
                return None, 0.0, 0.0, 0.0, 0.0

            nf = float(values[4]), float(values[5])
            cf = float(values[6]), float(values[7])
            bf = float(values[8]), float(values[9])
            #tf = float(values[10]), float(values[11]) # skip not needed
            t = float(values[12]), float(values[13])

            return transition, cf, bf, nf, t

        index = phdets_key_index[key] + 1

        # Find data files
        emitted_filepath = os.path.join(path, 'pe-intens-%s.dat' % str(index).zfill(2))
        if not os.path.exists(emitted_filepath):
            raise ImporterException("Data file %s cannot be found" % emitted_filepath)

        generated_filepath = os.path.join(path, 'pe-gen-ph.dat')
        if not os.path.exists(generated_filepath):
            raise ImporterException("Data file %s cannot be found" % generated_filepath)

        # Load generated
        intensities = {}

        with open(generated_filepath, 'r') as fp:
            for line in fp:
                line = line.strip()
                if line.startswith('#'): continue

                transition, gcf, gbf, gnf, gt = _read_intensities_line(line)

                if transition is None:
                    continue

                intensities[PhotonKey(transition, False, PhotonKey.C)] = gcf
                intensities[PhotonKey(transition, False, PhotonKey.B)] = gbf
                intensities[PhotonKey(transition, False, PhotonKey.P)] = gnf
                intensities[PhotonKey(transition, False, PhotonKey.T)] = gt

        # Load emitted
        with open(emitted_filepath, 'r') as fp:
            for line in fp:
                line = line.strip()
                if line.startswith('#'): continue

                transition, ecf, ebf, enf, et = _read_intensities_line(line)

                if transition is None:
                    continue

                intensities[PhotonKey(transition, True, PhotonKey.C)] = ecf
                intensities[PhotonKey(transition, True, PhotonKey.B)] = ebf
                intensities[PhotonKey(transition, True, PhotonKey.P)] = enf
                intensities[PhotonKey(transition, True, PhotonKey.T)] = et

        return PhotonIntensityResult(intensities)

    def _import_photon_depth(self, options, key, detector, path,
                             phdets_key_index, phdets_index_keys, *args):
        distributions = {}

        for filepath in glob.glob(os.path.join(path, 'pe-map-*-depth.dat')):
            # Create photon key
            with open(filepath, 'r') as fp:
                next(fp) # Skip first line
                text = next(fp).split(':')[1].strip()
                match = re.match('Z = ([ \d]+),([ \w]+)-([ \w]+), detector = ([ \d]+)', text)
                z, dest, src, detector_index = match.groups()

                z = int(z)
                src = Subshell(z, iupac=src)
                dest = Subshell(z, iupac=dest)
                transition = Transition(z, src, dest)

                detector_index = int(detector_index)
                if detector_index == 0:
                    photonkey = PhotonKey(transition, False, PhotonKey.T)
                else:
                    assert detector_index == phdets_key_index[key] + 1
                    photonkey = PhotonKey(transition, True, PhotonKey.T)

            # Read values
            datum = np.genfromtxt(filepath, skip_header=6)
            datum *= 1e-2 # cm to m

            distributions[photonkey] = datum

        return PhotonDepthResult(distributions)

    def _read_log(self, path):
        """
        Returns the last line of the :file:`penepma.csv` log file as a
        :class:`dict` where the keys are the header of each column and the
        values are the values of the last line.

        :arg path: directory containing the simulation files
        """
        filepath = os.path.join(path, 'penepma-res.dat')
        if not os.path.exists(filepath):
            raise ImporterException("Data file %s cannot be found" % filepath)

        log = {}
        with open(filepath, 'r') as fp:
            for line in fp:
                line = line.strip()

                match = re.match(r'([^.]*) [\.]+  ([^ ]*)(?: \+\- )?([^ ]*)?', line)
                if not match:
                    continue

                name = match.group(1).strip()
                val = float(match.group(2))
                unc = float(match.group(3) or 0.0)
                log[name] = (val, unc)

        return log

    def _import_electron_fraction(self, options, key, detector, path, *args):
        log = self._read_log(path)

        absorbed = log['Absorption fraction']
        backscattered = log['Upbound fraction']
        transmitted = log['Downbound fraction']

        return ElectronFractionResult(absorbed, backscattered, transmitted)

    def _import_time(self, options, key, detector, path, *args):
        log = self._read_log(path)

        simulation_time_s = log['Simulation time'][0]
        simulation_speed_s = 1.0 / log['Simulation speed'][0], 0.0

        return TimeResult(simulation_time_s, simulation_speed_s)

    def _import_showers_statistics(self, options, key, detector, path, *args):
        log = self._read_log(path)

        showers = log['Simulated primary showers'][0]

        return ShowersStatisticsResult(showers)

    def _import_backscattered_electron_energy(self, options, key, detector, path, *args):
        filepath = os.path.join(path, 'pe-energy-el-up.dat')
        if not os.path.exists(filepath):
            raise ImporterException("Data file %s cannot be found" % filepath)

        # Load distributions
        bins, vals, uncs = _load_dat_files(filepath)
        data = np.array([bins, vals, uncs]).T

        return BackscatteredElectronEnergyResult(data)

    def _import_transmitted_electron_energy(self, options, key, detector, path, *args):
        filepath = os.path.join(path, 'pe-energy-el-down.dat')
        if not os.path.exists(filepath):
            raise ImporterException("Data file %s cannot be found" % filepath)

        # Load distributions
        bins, vals, uncs = _load_dat_files(filepath)
        data = np.array([bins, vals, uncs]).T

        return TransmittedElectronEnergyResult(data)
