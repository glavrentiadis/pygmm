#!/usr/bin/env python
# encoding: utf-8
"""Model for the Idriss (2014) ground motion model."""

from __future__ import division

import numpy as np

from . import model

__author__ = 'Albert Kottke'


class Idriss2014(model.Model):
    """Idriss (2014, :cite:`idriss14`) model.

    This model was developed for active tectonic regions as part of the
    NGA-West2 effort.
    """

    NAME = 'Idriss (2014)'
    ABBREV = 'I14'

    # Reference velocity (m/s)
    V_REF = 1200.

    # Load the coefficients for the model
    COEFF = dict(
        small=model.load_data_file('idriss_2014-small.csv', 2),
        large=model.load_data_file('idriss_2014-large.csv', 2), )
    PERIODS = COEFF['small']['period']

    INDEX_PGA = 0
    INDICES_PSA = np.arange(22)

    PARAMS = [
        model.NumericParameter('dist_rup', True, None, 150),
        model.NumericParameter('mag', True, 5, None),
        model.NumericParameter('v_s30', True, 450, 1200),
        model.CategoricalParameter('mechanism', True, ['SS', 'RS'], 'SS'),
    ]

    def __init__(self, **kwds):
        """Initialize the model.

        Keyword Args:
            dist_rup (float): Closest distance to the rupture plane
                (:math:`R_\\text{rup}`, km)

            mag (float): moment magnitude of the event (:math:`M_w`)

            mechanism (str): fault mechanism. Valid options: "SS", "NS", "RS".
                *SS* and *NS* mechanism are treated the same with :math:`F=0`
                in the model.

            v_s30 (float): time-averaged shear-wave velocity over the top 30 m
                of the site (:math:`V_{s30}`, m/s).
        """
        super(Idriss2014, self).__init__(**kwds)
        self._ln_resp = self._calc_ln_resp()
        self._ln_std = self._calc_ln_std()

    def _calc_ln_resp(self):
        """Calculate the natural logarithm of the response.

        Returns:
            :class:`np.array`: Natural log of the response.
        """
        p = self.params
        c = self.COEFF['small'] if p['mag'] <= 6.75 else self.COEFF['large']

        if p['mechanism'] == 'RS':
            flag_mech = 1
        else:
            # SS/RS/U
            flag_mech = 0

        f_mag = (c.alpha_1 + c.alpha_2 * p['mag'] + c.alpha_3 *
                 (8.5 - p['mag']) ** 2)
        f_dst = (-(c.beta_1 + c.beta_2 * p['mag']) * np.log(p['dist_rup'] + 10)
                 + c.gamma * p['dist_rup'])
        f_ste = c.epsilon * np.log(p['v_s30'])
        f_mec = c.phi * flag_mech

        ln_resp = f_mag + f_dst + f_ste + f_mec

        return ln_resp

    def _calc_ln_std(self):
        """Calculate the logarithmic standard deviation.

        Returns:
            :class:`np.array`: Logarithmic standard deviation.
        """
        p = self.params
        ln_std = (1.18 + 0.035 * np.log(np.clip(self.PERIODS, 0.05, 3.0)) -
                  0.06 * np.clip(p['mag'], 5.0, 7.5))
        return ln_std
