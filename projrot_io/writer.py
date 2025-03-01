"""
Functions to write the ProjRot input file
"""

import os
import numpy as np
from mako.template import Template
from qcelemental import constants as qcc
from qcelemental import periodictable as ptab


# Conversion factors
BOHR2ANG = qcc.conversion_factor('bohr', 'angstrom')

# OBTAIN THE PATH TO THE DIRECTORY CONTAINING THE TEMPLATES #
SRC_PATH = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_PATH = os.path.join(SRC_PATH, 'templates')


def rpht_input(geoms, grads, hessians,
               saddle_idx=1,
               rotors_str='',
               coord_proj='cartesian',
               proj_rxn_coord=False):
    """ Write the ProjRot input file
    """

    # Format the molecule info
    if not isinstance(geoms, list):
        geoms = [geoms]
    if not isinstance(grads, list):
        grads = [grads]
    if not isinstance(hessians, list):
        hessians = [hessians]
    nsteps = len(geoms)
    natoms = len(geoms[0])
    data_str = _write_data_str(geoms, grads, hessians)
    nrotors = rotors_str.count('pivotA')

    # Check input into the function
    assert all(len(lst) == nsteps for lst in (geoms, grads, hessians))
    assert coord_proj in ('cartesian', 'internal')

    # Create a fill value dictionary
    rpht_keys = {
        'natoms': natoms,
        'nsteps': nsteps,
        'saddle_idx': saddle_idx,
        'coord_proj': coord_proj,
        'prod_rxn_coord': proj_rxn_coord,
        'nrotors': nrotors,
        'rotors_str': rotors_str,
        'data_str': data_str
    }

    # Set template name and path for an atom
    template_file_name = 'rpht_input.mako'
    template_file_path = os.path.join(TEMPLATE_PATH, template_file_name)

    # Build a ProjRot input string
    rpht_string = Template(filename=template_file_path).render(**rpht_keys)

    return rpht_string


def rpht_path_coord_en(coords, energy, bnd1=None, bnd2=None):
    """ Write the ProjRot file containing path data
    """
    nsteps = len(coords)

    # Build bnd1 and bnd2 lists with fake values if they have not been set
    bnd1 = bnd1 if bnd1 is not None else [1.00 for val in coords]
    bnd2 = bnd2 if bnd2 is not None else [1.00 for val in coords]

    # Check that all the lists are not empty and have the same length
    assert all(lst for lst in (coords, energy, bnd1, bnd2))
    assert all(len(lst) == nsteps for lst in (energy, bnd1, bnd2))

    path_str = 'Point Coordinate Energy Bond1 Bond2\n'
    for i, (crd, ene, bd1, bd2) in enumerate(zip(coords, energy, bnd1, bnd2)):
        path_str += '{0:>3d}{1:>9.5f}{2:>9.5f}{3:>8.5f}{4:>8.5f}'.format(
            i, crd, ene, bd1, bd2)
        if i != nsteps-1:
            path_str += '\n'

    return path_str


def rotors(axis, group, remdummy=None):
    """ Write the sections that defines the rotors section
    """

    # Set up the keywords
    pivota = axis[0]
    pivotb = axis[1]
    atomsintopa = len(group)
    if remdummy is not None:
        pivota = int(pivota - remdummy[pivota-1])
        pivotb = int(pivotb - remdummy[pivotb-1])
        topaatoms = '  '.join([str(int(val-remdummy[val-1])) for val in group])
    else:
        topaatoms = '  '.join([str(val) for val in group])

    # Build the rotors_str
    rotors_str = '\n{0:<32s}{1:<4d}\n'.format('pivotA', pivota)
    rotors_str += '{0:<32s}{1:<4d}\n'.format('pivotB', pivotb)
    rotors_str += '{0:<32s}{1:<4d}\n'.format('atomsintopA', atomsintopa)
    rotors_str += '{0:<32s}{1}'.format('topAatoms', topaatoms)

    return rotors_str


def _write_data_str(geoms, grads, hessians):
    """ Combine all of the data information into a string
    """
    nsteps = len(geoms) - 1
    data_str = ''
    for i, (geo, grad, hess) in enumerate(zip(geoms, grads, hessians)):
        data_str += 'Step    {0}\n'.format(str(i+1))
        data_str += 'geometry\n'
        data_str += _format_geom_str(geo)
        data_str += 'gradient\n'
        data_str += _format_grad_str(geo, grad)
        data_str += 'Hessian\n'
        data_str += _format_hessian_str(hess)
        if i != nsteps:
            data_str += '\n'

    return data_str


def _format_geom_str(geo):
    """ Write the geometry section of the input file
        geometry in Angstroms
    """

    # Format the strings for the xyz coordinates
    geom_str = ''
    for i, (sym, coords) in enumerate(geo):
        anum = int(ptab.to_Z(sym))
        coords = [coord * BOHR2ANG for coord in coords]
        coords_str = '{0:>14.8f}{1:>14.8f}{2:>14.8f}'.format(
            coords[0], coords[1], coords[2])
        geom_str += '{0:2d}{1:4d}{2:4d}{3}\n'.format(
            i+1, anum, 0, coords_str)

    return geom_str


def _format_grad_str(geom, grad):
    """ Write the gradient section of the input file
        grads in Hartrees/Bohr
    """

    atom_list = []
    for i, (sym, _) in enumerate(geom):
        atom_list.append(int(ptab.to_Z(sym)))

    # Format the strings for the xyz gradients
    full_grads_str = ''
    for i, grads in enumerate(grad):
        grads_str = '{0:>14.8f}{1:>14.8f}{2:>14.8f}'.format(
            grads[0], grads[1], grads[2])
        full_grads_str += '{0:2d}{1:4d}{2}\n'.format(
            i+1, atom_list[i], grads_str)

    return full_grads_str


def _format_hessian_str(hess):
    """ Write the Hessian section of the input file
    """

    # Format the Hessian
    hess = np.array(hess)
    nrows, ncols = hess.shape

    if nrows % 5 == 0:
        nchunks = nrows // 5
    else:
        nchunks = (nrows // 5) + 1

    hess_str = '   ' + '    '.join([str(val) for val in range(1, 6)]) + '\n'
    cnt = 0
    while cnt+1 <= nchunks:
        for i in range(nrows):
            col_tracker = 1
            if i >= 5*cnt:
                hess_str += '{0}'.format(str(i+1))
                for j in range(5*cnt, ncols):
                    if i >= j:
                        if col_tracker <= 5:
                            hess_str += '  {0:5.8f}'.format(hess[i][j])
                            col_tracker += 1
                            if col_tracker == 6:
                                hess_str += '\n'
                        else:
                            continue
                    elif i < j and col_tracker != 6:
                        hess_str += '\n'
                        break
                    else:
                        break
            if i+1 == nrows and cnt+1 < nchunks-1:
                val_str = '     '.join(
                    [str(val)
                     for val in range(5*(cnt+1) + 1, 5*(cnt+1) + 6)])
                hess_str += '    ' + val_str + '\n'
            if i+1 == nrows and cnt+1 == nchunks-1:
                val_str = '     '.join(
                    [str(val)
                     for val in range(5*(cnt+1) + 1, nrows+1)])
                hess_str += '    ' + val_str + '\n'
        cnt += 1

    return hess_str
