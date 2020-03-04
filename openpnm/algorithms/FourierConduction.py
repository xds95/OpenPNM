from openpnm.algorithms import ReactiveTransport
from openpnm.utils import logging
logger = logging.getLogger(__name__)


class FourierConduction(ReactiveTransport):
    r"""
    A subclass of GenericLinearTransport to simulate heat conduction.

    """
    def __init__(self,
                 settings={'quantity': 'pore.temperature',
                           'conductance': 'throat.thermal_conductance',
                           }, **kwargs):
        super().__init__(**kwargs)
        self.settings.update(settings)

    def setup(self, phase=None, quantity='', conductance='', **kwargs):
        r"""
        This method takes several arguments that are essential to running the
        algorithm and adds them to the settings.

        Parameters
        ----------
        phase : OpenPNM Phase object
            The phase on which the algorithm is to be run.  If no value is
            given, the existing value is kept.

        quantity : str (default = ``'pore.temperature'``)
            The name of the physical quantity to be calcualted.  If no value is
            given, the existing value is kept.

        conductance : str (default = ``'throat.thermal_conductance'``
            The name of the pore-scale transport conductance values.  These
            are typically calculate by a model attached to a *Physics* object
            associated with the given *Phase*.  If no value is given, the
            existing value is kept.

        Notes
        -----
        Any additional arguments are added to the ``settings`` dictionary of
        the object.

        """
        if phase:
            self.settings['phase'] = phase.name
        if quantity:
            self.settings['quantity'] = quantity
        if conductance:
            self.settings['conductance'] = conductance
        super().setup(**kwargs)

    def calc_effective_conductivity(self, inlets=None, outlets=None,
                                    domain_area=None, domain_length=None):
        r"""
        This calculates the effective thermal conductivity.

        Parameters
        ----------
        inlets : array_like
            The pores where the inlet temperature boundary conditions were
            applied.  If not given an attempt is made to infer them from the
            algorithm.

        outlets : array_like
            The pores where the outlet temperature boundary conditions were
            applied.  If not given an attempt is made to infer them from the
            algorithm.

        domain_area : scalar, optional
            The area of the inlet (and outlet) boundary faces.  If not given
            then an attempt is made to estimate it, but it is usually
            underestimated.

        domain_length : scalar, optional
            The length of the domain between the inlet and outlet boundary
            faces.  If not given then an attempt is made to estimate it, but it
            is usually underestimated.

        Notes
        -----
        The area and length of the domain are found using the bounding box
        around the inlet and outlet pores which do not necessarily lie on the
        edge of the domain, resulting in underestimation of sizes.
        """
        return self._calc_eff_prop(inlets=inlets, outlets=outlets,
                                   domain_area=domain_area,
                                   domain_length=domain_length)
