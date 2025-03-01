"""
Test the rate plotting functionality for comparing two mechanisms
"""

import numpy as np
import chemkin_io

from data_thermo import THM_DCT
TEMPS = np.array([500.0, 1000.0, 1500.0])


def test__plot_thermo():
    """ test chemkin_io.mechparser.plot.thermo
    """
    chemkin_io.plotter.thermo.build(THM_DCT, TEMPS)


if __name__ == '__main__':
    test__plot_thermo()
