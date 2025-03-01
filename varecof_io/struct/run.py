""" build structures and check symmetry
"""

import os
import subprocess
from qcelemental import constants as qcc
import automol
import intxyz
import varecof_io


RAD2DEG = qcc.conversion_factor('radian', 'degree')
BOHR2ANG = qcc.conversion_factor('bohr', 'angstrom')


ZMA = ((('C', (None, None, None), (None, None, None)),
        ('H', (0, None, None), ('R1', None, None)),
        ('H', (0, 1, None), ('R2', 'A2', None)),
        ('H', (0, 1, 2), ('R3', 'A3', 'D3')),
        ('H', (0, 1, 2), ('R4', 'A4', 'D4'))),
       {'R1': 2.09646,
        'R2': 2.09646, 'A2': 1.9106293854507126,
        'R3': 2.09646, 'A3': 1.9106293854507126, 'D3': 4.1887902047863905,
        'R4': 12.09646, 'A4': 1.9106293854507126, 'D4': 2.0943951023931953})
RXN_IDXS2 = [0, 4]
MAX_IDX = 4

MEP_GEO = """C       -0.2054901012      0.1186337111      0.0838793339                 
H        0.1076008786     -0.0621229284      1.2083245013                 
H        0.1076035596      1.1185015807     -0.4613403950                 
H       -0.9148413825     -0.6524365956     -0.4613401511                 
F        5.2265410000     -3.0175450000     -2.1337000000"""

# iso_geo1 = """C    0.000000   0.000000   0.000000
# H   -0.539500  -0.934400   0.000000
# H   -0.539500   0.934400   0.000000
# H    1.079000   0.000000   0.000000"""
iso_geo1 = """C       -0.2054901012      0.1186337111      0.0838793339                 
H        0.1076008786     -0.0621229284      1.2083245013                 
H        0.1076035596      1.1185015807     -0.4613403950                 
H       -0.9148413825     -0.6524365956     -0.4613401511"""

iso_geo2 = "H    0.000000   0.000000   0.000000"


# def fragment_geometries(ts_zma, rct_zmas, bdn_frm_idxs):
def fragment_geometries():
    """ get the fragment geometries
    """

    # Get the MEP geometries
    # mep_total_geo = automol.zmatrix.geometry(ZMA)
    mep_total_geo = automol.geom.from_string(MEP_GEO)
    # mep_fgeos = [mep_total_geo[:max_idx], mep_total_geo[max_idx:]]
    mep_fgeos = [mep_total_geo[:MAX_IDX], mep_total_geo[MAX_IDX:]]
    bnd_frm_idxs = RXN_IDXS2
    bnd_frm_idxs = [4, 0]
    # Get the geometries of the isolated fragments (the reactants)
    # iso_fgeos = [automol.zmatrix.geometry(zma) for zma in rct_zmas]
    iso_fgeos = [automol.geom.from_string(iso_geo1),
                 automol.geom.from_string(iso_geo2)]

    # Get the geometries for the structure.inp file
    vc_geos = []
    mol_data = zip(mep_fgeos, iso_fgeos, bnd_frm_idxs)
    for i, (mep_geo, iso_geo, idx) in enumerate(mol_data):

        if not automol.geom.is_atom(mep_geo):

            # Build MEPFragGeom+X coordinates using MEP geometry
            x_coord = mep_total_geo[idx][1]
            dummy_row = ('X', x_coord)
            if i == 0:
                mep_geo_wdummy = mep_geo + (dummy_row,)
                x_idx = len(mep_geo_wdummy) - 1
                a1_idx = 0
                # print(x_idx)
                # print(a1_idx)
                # for x in mep_geo_wdummy:
                #     print(x)
            else:
                mep_geo_wdummy = (dummy_row,) + mep_geo
                x_idx = 0
                a1_idx = 1

            # Calculate coords to define X position in IsoFragGeom structure
            xyz1 = iso_geo[a1_idx][1]
            xyz2 = iso_geo[a1_idx+1][1]
            xdistance = automol.geom.distance(
                mep_geo_wdummy, x_idx, a1_idx)
            print(x_idx, a1_idx, a1_idx+1)
            xangle = automol.geom.central_angle(
                mep_geo_wdummy, x_idx, a1_idx, a1_idx+1)
            print(xangle)
            print(xangle * 180.0/3.14)
            if len(mep_geo) > 2:
                xyz3 = iso_geo[a1_idx+2][1]
                xdihedral = automol.geom.dihedral_angle(
                    mep_geo_wdummy, x_idx, a1_idx, a1_idx+1, a1_idx+2)
            else:
                xyz3 = None
                xdihedral = None

            # Calculate the X Position for the IsoFrag structure
            # print('\ncoords')
            # print(x_idx)
            # print(np.array(xyz1) * BOHR2ANG)
            # print(np.array(xyz2) * BOHR2ANG)
            # print(np.array(xyz3) * BOHR2ANG)
            # print(xdistance * BOHR2ANG)
            # print(xangle * RAD2DEG)
            # print(xdihedral * RAD2DEG)
            xyzp = intxyz.find_xyzp(
                xyz1, xyz2, xyz3, xdistance, xangle, xdihedral)

            # Generate the IsoFragGeom+X coordinates for the structure.inp file
            if i == 0:
                iso_geo_wdummy = iso_geo + (('X', xyzp),)
            else:
                iso_geo_wdummy = (('X', xyzp),) + iso_geo

            # Append to final geoms
            vc_geos.append(iso_geo_wdummy)

        else:
            # If atom, set IsoFragGeom+X coords equal to mep_geo
            vc_geos.append(mep_geo)

    print('mep geo')
    for geo in mep_fgeos:
        print('\n')
        print(automol.geom.string(geo))
    print('\n')
    print('iso geo')
    for geo in iso_fgeos:
        print('\n')
        print(automol.geom.string(geo))
    print('\n')
    print('new geo')
    for geo in vc_geos:
        print('\n')
        print(automol.geom.string(geo).replace('X', 'F'))

    return vc_geos


def assess_face_symmetries():
    """ check the symmetry of the faces for each fragment
    """

    DEVNULL = open(os.devnull, 'w')
    subprocess.check_call(['./convert_struct', 'divsur.inp'],
        stdout=DEVNULL, stderr=DEVNULL)

    # Read fragment geoms from divsur.out with coordinates in the divsur frame
    with open('divsur.out', 'r') as divsur_file:
        divsur_string = divsur_file.read()
    fgeo1, fgeo2 = varecof_io.reader.divsur.frag_geoms_divsur_frame(
        divsur_string)
    fgeo1 = automol.geom.from_string(fgeo1)
    fgeo2 = automol.geom.from_string(fgeo2)

    # Reflect the dummy atom (pivot positio) about the xy plane
    f1_dummy_idx = len(fgeo1) - 1
    f2_dummy_idx = 0
    fgeo1_reflect = automol.geom.reflect_coordinates(
        fgeo1, [f1_dummy_idx], ['x', 'y'])
    fgeo2_reflect = automol.geom.reflect_coordinates(
        fgeo2, [f2_dummy_idx], ['x', 'y'])

    print(automol.geom.string(fgeo1)+'\n')
    print(automol.geom.string(fgeo1_reflect)+'\n')
    print(automol.geom.string(fgeo2)+'\n')
    print(automol.geom.string(fgeo2_reflect)+'\n')

    # # Assess the coloumb spectrum for each geom
    fgeo1_sym = automol.geom.almost_equal_coulomb_spectrum(
        fgeo1, fgeo1_reflect, rtol=1e-2)
    fgeo2_sym = automol.geom.almost_equal_coulomb_spectrum(
        fgeo2, fgeo2_reflect, rtol=1e-2)
    print(fgeo1_sym)
    print(fgeo2_sym)

    return fgeo1_sym, fgeo2_sym


if __name__ == '__main__':
    # fragment_geometries()
    assess_face_symmetries()
