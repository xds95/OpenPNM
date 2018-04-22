from openpnm.core import logging as _logging
from openpnm.models import misc as _misc
import numpy as _np
_logger = _logging.getLogger(__name__)


def weibull(target, shape, scale, loc, seeds='pore.seed'):
    return _misc.weibull(target=target, shape=shape, scale=scale, loc=loc,
                         seeds=seeds)


weibull.__doc__ = _misc.weibull.__doc__


def normal(target, scale, loc, seeds='pore.seed'):
    return _misc.normal(target=target, scale=scale, loc=loc,
                        seeds=seeds)


normal.__doc__ = _misc.normal.__doc__


def generic(target, func, seeds='pore.seed'):
    return _misc.generic(target=target, func=func, seeds=seeds)


generic.__doc__ = _misc.generic.__doc__


def largest_sphere(target, iters=10):
    r"""
    Finds the maximum diameter pore that can be places in each location without
    doverlapping any neighbors.

    Parameters
    ----------
    target : OpenPNM Object
        The object which this model is associated with. This controls the
        length of the calculated array, and also provides access to other
        necessary properties.

    iters : integer
        The number of iterations to perform when searching for maximum
        diameter.  This function iteratively grows pores until they touch
        their nearest neighbor, which is also growing, so this parameter limits
        the maximum number of iterations.  The default is 10, but 5 is usally
        enough.

    Notes
    -----
    This model looks into all pores in the network when finding the diameter.
    This means that when multiple Geometry objects are defined, it will
    consider the diameter of pores on adjacent Geometries. If no diameters
    have been assigned to these neighboring pores it will assume 0.  If
    diameter value are assigned to the neighboring pores AFTER this model is
    run, the pores will overlap.  This can be remedied by running this model
    again.

    """
    network = target.project.network
    D = _np.zeros([network.Np, ], dtype=float)
    Ps = network.pores(target.name)
    C1 = network['pore.coords'][network['throat.conns'][:, 0]]
    C2 = network['pore.coords'][network['throat.conns'][:, 1]]
    L = _np.sqrt(_np.sum((C1 - C2)**2, axis=1))
    while iters >= 0:
        iters -= 1
        Lt = L - _np.sum(D[network['throat.conns']], axis=1)/2
        am = network.create_adjacency_matrix(weights=Lt, fmt='lil')
        D[Ps] = D[Ps] + _np.array([_np.amin(row) for row in am.data])[Ps]*0.95
    if _np.any(D < 0):
        _logger.warning('Negative pore diameters found!  Neighboring pores' +
                        ' must be larger than the pore spacing.')
    return D[network.pores(target.name)]


def equivalent_diameter(target, pore_volume='pore.volume',
                        pore_shape='sphere'):
    r"""
    Calculate pore diameter as the diameter of a sphere with an equivalent
    volume.

    Parameters
    ----------
    target : OpenPNM Geometry Object
        The Geometry object which this model is associated with. This controls
        the length of the calculated array, and also provides access to other
        necessary geometric properties.

    pore_volume : string
        The dictionary key containing the pore volume values

    shape : string
        The shape of the pore body to assume when back-calculating from
        volume.  Options are 'sphere' (default) or 'cube'.

    """
    from scipy.special import cbrt
    pore_vols = target[pore_volume]
    if pore_shape.startswith('sph'):
        value = cbrt(6*pore_vols/_np.pi)
    elif pore_shape.startswith('cub'):
        value = cbrt(pore_vols)
    return value
