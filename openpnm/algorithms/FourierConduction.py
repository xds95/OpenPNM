from openpnm.algorithms import ReactiveTransport
from openpnm.utils import logging, Docorator, GenericSettings
logger = logging.getLogger(__name__)
docstr = Docorator()

@docstr.get_sectionsf('FourierConductionSettings',
                      sections=['Parameters'])
@docstr.dedent
class FourierConductionSettings(GenericSettings):
    r"""

    Parameters
    ----------
    %(GenericTransportSettings.parameters)s

    quantity : (str)
        The name of the physical quantity to be calculated
    conductance : (str)
        The name of the pore-scale transport conductance values. These are
        typically calculated by a model attached to a *Physics* object
        associated with the given *Phase*.

    Other Parameters
    ----------------

    **The following parameters pertain to the ReactiveTransport class**

    %(ReactiveTransportSettings.other_parameters)s

    ----

    **The following parameters pertain to the GenericTransport class**

    %(GenericTransportSettings.other_parameters)s

    """
    quantity = 'pore.voltage'
    conductance = 'throat.electrical_conductance'


class FourierConduction(ReactiveTransport):
    r"""
    A subclass of GenericLinearTransport to simulate heat conduction.

    """

    def __init__(self, settings={}, **kwargs):
        super().__init__(**kwargs)
        self.settings.update(settings)
        self.settings._update_settings_and_docs(FourierConductionSettings())

    def setup(self, phase=None, quantity='', conductance='', **kwargs):
        r"""
        This method takes several arguments that are essential to running the
        algorithm and adds them to the settings.

        Parameters
        ----------
        %(FourierConductionSettings.parameters)s

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
