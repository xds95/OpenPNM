from scipy import pi as pi
import scipy as _sp


def generic_conductance(target, transport_type, pore_diffusivity,
                        throat_diffusivity, pore_area, throat_area,
                        conduit_lengths, conduit_shape_factors, **kwargs):
    r"""
    Calculate the generic conductance (could be mass, thermal, electrical,
    or hydraylic) of conduits in the network, where a conduit is
    ( 1/2 pore - full throat - 1/2 pore ).

    Parameters
    ----------
    target : OpenPNM Object
        The object which this model is associated with. This controls the
        length of the calculated array, and also provides access to other
        necessary properties.

    pore_diffusivity : string
        Dictionary key of the pore diffusivity values.

    throat_diffusivity : string
        Dictionary key of the throat diffusivity values.

    pore_area : string
        Dictionary key of the pore area values.

    throat_area : string
        Dictionary key of the throat area values.

    shape_factor : string
        Dictionary key of the conduit shape factor values.

    Returns
    -------
    g : ndarray
        Array containing conductance values for conduits in the geometry
        attached to the given physics object.

    Notes
    -----
    (1) This function requires that all the necessary phase properties already
    be calculated.

    (2) This function calculates the specified property for the *entire*
    network then extracts the values for the appropriate throats at the end.

    (3) This function assumes cylindrical throats with constant cross-section
    area. Corrections for different shapes and variable cross-section area can
    be imposed by passing the proper shape factor.

    (4) shape_factor depends on the physics of the problem, i.e. diffusion-like
    processes and fluid flow need different shape factors.

    """
    network = target.project.network
    throats = network.map_throats(throats=target.Ts, origin=target)
    phase = target.project.find_phase(target)
    cn = network['throat.conns'][throats]
    # Getting equivalent areas
    A1 = network[pore_area][cn[:, 0]]
    At = network[throat_area][throats]
    A2 = network[pore_area][cn[:, 1]]
    # Getting conduit lengths
    L1 = network[conduit_lengths + '.pore1'][throats]
    Lt = network[conduit_lengths + '.throat'][throats]
    L2 = network[conduit_lengths + '.pore2'][throats]
    # Preallocating g
    g1, g2, gt = _sp.zeros((3, len(Lt)))
    # Setting g to inf when Li = 0 (ex. boundary pores)
    # INFO: This is needed since area could also be zero, which confuses NumPy
    m1, m2, mt = [Li != 0 for Li in [L1, L2, Lt]]
    g1[~m1] = g2[~m2] = gt[~mt] = _sp.inf
    # If ionic conductance, compute conductance and return it
    if transport_type == 'ionic':
        g1[m1] = (A1)[m1] * L1[m1]
        g2[m2] = (A2)[m2] * L2[m2]
        gt[mt] = (At)[mt] * Lt[mt]
        return 1/((g1+g2+gt)/(L1+L2+Lt))
    # Getting shape factors
    try:
        SF1 = phase[conduit_shape_factors+'.pore1'][throats]
        SFt = phase[conduit_shape_factors+'.throat'][throats]
        SF2 = phase[conduit_shape_factors+'.pore2'][throats]
    except KeyError:
        SF1 = SF2 = SFt = 1.0
    # Interpolate pore phase property values to throats
    try:
        Dt = phase[throat_diffusivity][throats]
    except KeyError:
        Dt = phase.interpolate_data(propname=pore_diffusivity)[throats]
    try:
        D1 = phase[pore_diffusivity][cn[:, 0]]
        D2 = phase[pore_diffusivity][cn[:, 1]]
    except KeyError:
        D1 = phase.interpolate_data(propname=throat_diffusivity)[cn[:, 0]]
        D2 = phase.interpolate_data(propname=throat_diffusivity)[cn[:, 1]]
    # Find g for half of pore 1, throat, and half of pore 2
    if transport_type == 'flow':
        g1[m1] = A1[m1]**2 / (8*pi*D1*L1)[m1]
        g2[m2] = A2[m2]**2 / (8*pi*D2*L2)[m2]
        gt[mt] = At[mt]**2 / (8*pi*Dt*Lt)[mt]
    elif transport_type == 'flow_power_law':
        for k, v in kwargs.items():
            if k == 'pore_consistency':
                pore_consistency = v
            elif k == 'throat_consistency':
                throat_consistency = v
            elif k == 'pore_flow_index':
                pore_flow_index = v
            elif k == 'throat_flow_index':
                throat_flow_index = v
            elif k == 'pore_pressure':
                pore_pressure = v

        # Check if pressure field exists
        try:
            phase[pore_pressure]
        except KeyError:
            phase[pore_pressure] = 0
        P = phase[pore_pressure]

        # Interpolate pore phase property values to throats
        try:
            Ct = phase[throat_consistency][throats]
        except KeyError:
            Ct = phase.interpolate_data(propname=pore_consistency)[throats]
        try:
            nt = phase[throat_flow_index][throats]
        except KeyError:
            nt = phase.interpolate_data(propname=pore_flow_index)[throats]
        # Interpolate throat phase property values to pores
        try:
            C1 = phase[pore_consistency][cn[:, 0]]
            C2 = phase[pore_consistency][cn[:, 1]]
        except KeyError:
            C1 = phase.interpolate_data(propname=throat_consistency)[cn[:, 0]]
            C2 = phase.interpolate_data(propname=throat_consistency)[cn[:, 1]]
        try:
            n1 = phase[pore_flow_index][cn[:, 0]]
            n2 = phase[pore_flow_index][cn[:, 1]]
        except KeyError:
            n1 = phase.interpolate_data(propname=throat_flow_index)[cn[:, 0]]
            n2 = phase.interpolate_data(propname=throat_flow_index)[cn[:, 1]]
        # Interpolate pore pressure values to throats
        Pt = phase.interpolate_data(propname=pore_pressure)[throats]

        # Pressure differences dP
        dP1 = _sp.absolute(P[cn[:, 0]]-Pt)
        dP2 = _sp.absolute(P[cn[:, 1]]-Pt)
        dPt = _sp.absolute(_sp.diff(P[cn], axis=1).squeeze())

        # Apparent viscosities
        mu1 = (dP1**(1-1/n1)[m1] * C1**(1/n1)[m1] / ((4*n1/(3*n1+1)) *
               (2*L1/((A1/pi)**0.5))**(1-1/n1))[m1])

        mu2 = (dP2**(1-1/n2)[m2] * C2**(1/n2)[m2] / ((4*n2/(3*n2+1)) *
               (2*L2/((A2/pi)**0.5))**(1-1/n2))[m2])

        mut = (dPt**(1-1/nt)[mt] * Ct**(1/nt)[mt] / ((4*nt/(3*nt+1)) *
               (2*Lt/((At/pi)**0.5))**(1-1/nt))[mt])

        # Bound the apparent viscosity
        vis_min = 1e-08
        vis_max = 1e+04
        mu1[mu1 < vis_min] = vis_min
        mu1[mu1 > vis_max] = vis_max
        mu2[mu2 < vis_min] = vis_min
        mu2[mu2 > vis_max] = vis_max
        mut[mut < vis_min] = vis_min
        mut[mut > vis_max] = vis_max

        phase['throat.viscosity_eff'] = mut

        g1[m1] = A1[m1]**2 / ((8*pi*L1)[m1]*mu1)
        g2[m2] = A2[m2]**2 / ((8*pi*L2)[m2]*mu2)
        gt[mt] = At[mt]**2 / ((8*pi*Lt)[mt]*mut)

    elif transport_type == 'diffusion':
        g1[m1] = (D1*A1)[m1] / L1[m1]
        g2[m2] = (D2*A2)[m2] / L2[m2]
        gt[mt] = (Dt*At)[mt] / Lt[mt]
    elif transport_type == 'taylor_aris_diffusion':
        for k, v in kwargs.items():
            if k == 'pore_pressure':
                pore_pressure = v
            elif k == 'throat_hydraulic_conductance':
                throat_hydraulic_conductance = v
        P = phase[pore_pressure]
        gh = phase[throat_hydraulic_conductance]
        Qt = -gh*_sp.diff(P[cn], axis=1).squeeze()

        u1 = Qt[m1]/A1[m1]
        u2 = Qt[m2]/A2[m2]
        ut = Qt[mt]/At[mt]

        Pe1 = u1 * ((4*A1[m1]/_sp.pi)**0.5) / D1[m1]
        Pe2 = u2 * ((4*A2[m2]/_sp.pi)**0.5) / D2[m2]
        Pet = ut * ((4*At[mt]/_sp.pi)**0.5) / Dt[mt]

        g1[m1] = D1[m1]*(1+(Pe1**2)/192)*A1[m1] / L1[m1]
        g2[m2] = D2[m2]*(1+(Pe2**2)/192)*A2[m2] / L2[m2]
        gt[mt] = Dt[mt]*(1+(Pet**2)/192)*At[mt] / Lt[mt]
    elif transport_type == 'dispersion':
        for k, v in kwargs.items():
            if k == 'pore_pressure':
                pore_pressure = v
            elif k == 'throat_hydraulic_conductance':
                throat_hydraulic_conductance = v
            elif k == 'throat_diffusive_conductance':
                throat_diffusive_conductance = v
            elif k == 's_scheme':
                s_scheme = v

        P = phase[pore_pressure]
        gh = phase[throat_hydraulic_conductance]
        gd = phase[throat_diffusive_conductance]
        gd = _sp.tile(gd, 2)

        Qij = -gh*_sp.diff(P[cn], axis=1).squeeze()
        Qij = _sp.append(Qij, -Qij)

        Peij = Qij/gd
        Peij[(Peij < 1e-10) & (Peij >= 0)] = 1e-10
        Peij[(Peij > -1e-10) & (Peij <= 0)] = -1e-10
        Qij = Peij*gd

        if s_scheme == 'upwind':
            w = gd + _sp.maximum(0, -Qij)
        elif s_scheme == 'hybrid':
            w = _sp.maximum(0, _sp.maximum(-Qij, gd-Qij/2))
        elif s_scheme == 'powerlaw':
            w = gd * _sp.maximum(0, (1 - 0.1*_sp.absolute(Peij))**5) + \
                _sp.maximum(0, -Qij)
        elif s_scheme == 'exponential':
            w = -Qij / (1 - _sp.exp(Peij))
        else:
            raise Exception('Unrecognized discretization scheme: ' + s_scheme)
        w = _sp.reshape(w, (network.Nt, 2), order='F')
        return w
    elif transport_type == 'ad_dif_mig':
        for k, v in kwargs.items():
            if k == 'pore_pressure':
                pore_pressure = v
            if k == 'pore_potential':
                pore_potential = v
            elif k == 'throat_hydraulic_conductance':
                throat_hydraulic_conductance = v
            elif k == 'throat_diffusive_conductance':
                throat_diffusive_conductance = v
            elif k == 'throat_valence':
                throat_valence = v
            elif k == 'pore_temperature':
                pore_temperature = v
            elif k == 'throat_temperature':
                throat_temperature = v
            elif k == 's_scheme':
                s_scheme = v

        # Interpolate pore phase property values to throats
        try:
            T = phase[throat_temperature][throats]
        except KeyError:
            T = phase.interpolate_data(propname=pore_temperature)[throats]

        P = phase[pore_pressure]
        V = phase[pore_potential]
        gh = phase[throat_hydraulic_conductance]
        gd = phase[throat_diffusive_conductance]
        gd = _sp.tile(gd, 2)
        z = phase[throat_valence]
        D = Dt
        F = 96485.3329
        R = 8.3145

        S = (A1*L1+A2*L2+At*Lt)/(L1+L2+Lt)
        L = L1 + Lt + L2

        # Advection
        Qij = -gh*_sp.diff(P[cn], axis=1).squeeze()
        Qij = _sp.append(Qij, -Qij)

        # Migration
        grad_V = _sp.diff(V[cn], axis=1).squeeze() / L
        mig = ((z*F*D*S)/(R*T)) * grad_V
        mig = _sp.append(mig, -mig)

        # Advection-migration
        adv_mig = Qij-mig

        # Peclet number (includes advection and migration)
        Peij_adv_mig = adv_mig/gd
        Peij_adv_mig[(Peij_adv_mig < 1e-10) & (Peij_adv_mig >= 0)] = 1e-10
        Peij_adv_mig[(Peij_adv_mig > -1e-10) & (Peij_adv_mig <= 0)] = -1e-10

        # Corrected advection-migration
        adv_mig = Peij_adv_mig*gd

        if s_scheme == 'upwind':
            w = gd + _sp.maximum(0, -adv_mig)
        elif s_scheme == 'hybrid':
            w = _sp.maximum(0, _sp.maximum(-adv_mig, gd-adv_mig/2))
        elif s_scheme == 'powerlaw':
            w = (gd * _sp.maximum(0, (1 - 0.1*_sp.absolute(Peij_adv_mig))**5) +
                 _sp.maximum(0, -adv_mig))
        elif s_scheme == 'exponential':
            w = -adv_mig / (1 - _sp.exp(Peij_adv_mig))
        else:
            raise Exception('Unrecognized discretization scheme: ' + s_scheme)
        w = _sp.reshape(w, (network.Nt, 2), order='F')
        return w
    else:
        raise Exception('Unknown keyword for "transport_type", can only be' +
                        ' "flow", "diffusion", "taylor_aris_diffusion",' +
                        ' "dispersion", "ad_dif_mig" or "ionic"')
    # Apply shape factors and calculate the final conductance
    return (1/gt/SFt + 1/g1/SF1 + 1/g2/SF2)**(-1)