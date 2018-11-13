# -*- coding: utf-8 -*-
# Copyright 2017-2018 The pyXem developers
#
# This file is part of pyXem.
#
# pyXem is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyXem is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyXem.  If not, see <http://www.gnu.org/licenses/>.

"""Diffraction pattern library generator and associated tools.
"""

import numpy as np
import itertools
from tqdm import tqdm
from transforms3d.euler import euler2mat
import diffpy.structure

from pyxem.libraries.diffraction_library import DiffractionLibrary
from pyxem.libraries.vector_library import DiffractionVectorLibrary

from pyxem.utils.sim_utils import get_points_in_sphere
from pyxem.utils.vector_utils import get_angle_cartesian


class DiffractionLibraryGenerator(object):
    """Computes a library of electron diffraction patterns for specified atomic
    structures and orientations.
    """

    def __init__(self, electron_diffraction_calculator):
        """Initialises the generator with a diffraction calculator.

        Parameters
        ----------
        electron_diffraction_calculator : :class:`DiffractionGenerator`
            The calculator used to simulate diffraction patterns.
        """
        self.electron_diffraction_calculator = electron_diffraction_calculator

    def get_diffraction_library(self,
                                structure_library,
                                calibration,
                                reciprocal_radius,
                                half_shape,
                                with_direct_beam=True):
        """Calculates a dictionary of diffraction data for a library of crystal
        structures and orientations.

        Each structure in the structure library is rotated to each associated
        orientation and the diffraction pattern is calculated each time.

        Angles must be in the Euler representation (Z,X,Z) and in degrees

        Parameters
        ----------
        structure_library : pyxem:StructureLibrary Object
            Dictionary of structures and associated orientations for which
            electron diffraction is to be simulated.
        calibration : float
            The calibration of experimental data to be correlated with the
            library, in reciprocal Angstroms per pixel.
        reciprocal_radius : float
            The maximum g-vector magnitude to be included in the simulations.
        half_shape: tuple
            The half shape of the target patterns, for 144x144 use (72,72) etc

        Returns
        -------
        diffraction_library : :class:`DiffractionLibrary`
            Mapping of crystal structure and orientation to diffraction data
            objects.

        """
        # Define DiffractionLibrary object to contain results
        diffraction_library = DiffractionLibrary()
        # The electron diffraction calculator to do simulations
        diffractor = self.electron_diffraction_calculator
        structure_library = structure_library.struct_lib
        # Iterate through phases in library.
        for key in structure_library.keys():
            phase_diffraction_library = dict()
            structure = structure_library[key][0]
            a, b, c = structure.lattice.a, structure.lattice.b, structure.lattice.c
            alpha = structure.lattice.alpha
            beta = structure.lattice.beta
            gamma = structure.lattice.gamma
            orientations = structure_library[key][1]
            # Iterate through orientations of each phase.
            for orientation in tqdm(orientations, leave=False):
                _orientation = np.deg2rad(orientation)
                matrix = euler2mat(_orientation[0],
                                   _orientation[1],
                                   _orientation[2], 'rzxz')

                latt_rot = diffpy.structure.lattice.Lattice(a, b, c,
                                                            alpha, beta, gamma,
                                                            baserot=matrix)
                structure.placeInLattice(latt_rot)

                # Calculate electron diffraction for rotated structure
                data = diffractor.calculate_ed_data(structure,
                                                    reciprocal_radius,
                                                    with_direct_beam)
                # Calibrate simulation
                data.calibration = calibration
                pattern_intensities = data.intensities
                pixel_coordinates = np.rint(
                    data.calibrated_coordinates[:, :2] + half_shape).astype(int)
                # Construct diffraction simulation library, removing those that
                # contain no peaks
                if len(pattern_intensities) > 0:
                    phase_diffraction_library[tuple(orientation)] = \
                        {'Sim': data, 'intensities': pattern_intensities,
                         'pixel_coords': pixel_coordinates,
                         'pattern_norm': np.sqrt(np.dot(pattern_intensities,
                                                        pattern_intensities))}
                    diffraction_library[key] = phase_diffraction_library

        # Pass attributes to diffraction library from structure library.
        diffraction_library.identifiers = structure_library.indentifiers
        diffraction_library.structures = structure_library.structures

        return diffraction_library


class VectorLibraryGenerator(object):
    """Computes a library of diffraction vectors and pairwise inter-vector
    angles for a specified StructureLibrary.
    """

    def __init__(self, structure_library):
        """Initialises the library with a diffraction calculator.

        Parameters
        ----------
        structure_library : :class:`StructureLibrary`
            The StructureLibrary defining structures to be
        """
        self.structures = structure_library

    def get_vector_library(self,
                           reciprocal_radius):
        """Calculates a library of diffraction vectors and pairwise inter-vector
        angles for a library of crystal structures.

        Parameters
        ----------
        reciprocal_radius : float
            The maximum g-vector magnitude to be included in the library.

        Returns
        -------
        vector_library : :class:`DiffractionVectorLibrary`
            Mapping of phase identifier to a numpy array with entries in the
            form: [hkl1, hkl2, len1, len2, angle] ; lengths are in reciprocal
            Angstroms and angles are in radians.

        """
        # Define DiffractionVectorLibrary object to contain results
        vector_library = DiffractionVectorLibrary()
        # Get structures from structure library
        structure_library = self.structures.struct_lib
        # Iterate through phases in library.
        for key in structure_library.keys():
            # Get diffpy.structure object associated with phase
            structure = structure_library[key][0]
            # Get reciprocal lattice points within reciprocal_radius
            latt = structure.lattice
            recip_latt = latt.reciprocal()
            indices, coordinates, distances = get_points_in_sphere(
                recip_latt,
                reciprocal_radius)
            # Define an empty list to store phase vector pairs
            phase_vectors = []
            # iterate through all pairs calculating interplanar angle
            for comb in itertools.combinations(np.arange(len(indices)), 2):
                i, j = comb[0], comb[1]
                # specify hkls and lengths
                # TODO: This should be updated to reflect systematic absences
                # associated with the crystal structure.
                hkl1 = indices[i]
                hkl2 = indices[j]
                len1 = distances[i]
                len2 = distances[j]
                angle = get_angle_cartesian(coordinates[i], coordinates[j])
                phase_vectors.append(np.array([hkl1, hkl2, len1, len2, angle]))
            vector_library[key] = np.array(phase_vectors)

        # Pass attributes to diffraction library from structure library.
        vector_library.identifiers = structure_library.indentifiers
        vector_library.structures = structure_library.structures

        return vector_library
