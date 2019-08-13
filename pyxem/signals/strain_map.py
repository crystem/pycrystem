# -*- coding: utf-8 -*-
# Copyright 2017-2019 The pyXem developers
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

from hyperspy.signals import Signal2D
import numpy as np



class StrainMap(Signal2D):
    _signal_type = "strain_map"

    def __init__(self, *args, **kwargs):
        Signal2D.__init__(self, *args, **kwargs)
        self.current_basis_x = [1,0]
        self.current_basis_y = [0,1]

    def change_strain_basis(x_new):
        # following
        #https://www.continuummechanics.org/stressxforms.html
        # retrived August 2019

        def _get_rotation_matrix(x_new):
            # just do an inverse job
            x_old = self.current_basis_x
            pass
        
        pass
