'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import unittest

import numpy as np
import pandas as pd
from numpy.linalg import norm

from energy_models.core.investments.base_invest import BaseInvest
from energy_models.glossaryenergy import GlossaryEnergy


class TestBaseInvest(unittest.TestCase):
    """
    SoSDiscipline test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.base_invest = BaseInvest('Test')
        self.y_s = GlossaryEnergy.YeartStartDefault
        self.y_e = 2050
        self.y_step = 1

    def test_01_set_invest_unit_failure(self):
        try:
            self.base_invest.set_invest_unit('€')
            passed = True
        except:
            passed = False
        self.assertFalse(passed)

    def test_02_set_invest_unit(self):
        POS_UNIT = BaseInvest.POS_UNIT
        for unit in POS_UNIT:
            self.base_invest.set_invest_unit(unit)
            self.assertEqual(unit, self.base_invest.invest_unit)

    def test_03_invest_dataframe(self):
        invest_ref = 1.e9  # $
        years = np.arange(self.y_s, self.y_e + 1, step=self.y_step)
        invest = np.zeros(len(years))
        invest[0] = invest_ref
        for i in range(1, len(years)):
            invest[i] = 1.02 * invest[i - 1]

        invest_df = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: invest})
        try:
            self.base_invest.set_invest_level(invest, '$')
            passed = True
        except:
            passed = False
        self.assertFalse(passed)  # -- assert crash if not a dataframe

        try:
            self.base_invest.set_invest_level(invest_df, '$')
            passed = True
        except:
            passed = False
        self.assertTrue(passed)  # -- assert dataframe setup works

    def test_04_change_invest_unit(self):
        invest_ref = 10.e12  # $
        years = np.arange(self.y_s, self.y_e + 1, step=self.y_step)
        invest = np.zeros(len(years))
        invest[0] = invest_ref
        for i in range(1, len(years)):
            invest[i] = 1.02 * invest[i - 1]

        invest_df = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: invest})
        self.base_invest.set_invest_level(invest_df, '$')
        # in $
        cinvest = self.base_invest.get_invest_level('$')
        self.assertAlmostEqual(norm(cinvest[GlossaryEnergy.InvestValue] - invest_df[GlossaryEnergy.InvestValue]), 0., 4)
        # in k$
        cinvest = self.base_invest.get_invest_level('k$')
        self.assertAlmostEqual(norm(cinvest[GlossaryEnergy.InvestValue] - invest_df[GlossaryEnergy.InvestValue] / 1e3),
                               0., 4)
        # in M$
        cinvest = self.base_invest.get_invest_level('M$')
        self.assertAlmostEqual(norm(cinvest[GlossaryEnergy.InvestValue] - invest_df[GlossaryEnergy.InvestValue] / 1e6),
                               0., 4)
        # in G$
        cinvest = self.base_invest.get_invest_level('G$')
        self.assertAlmostEqual(norm(cinvest[GlossaryEnergy.InvestValue] - invest_df[GlossaryEnergy.InvestValue] / 1e9),
                               0., 4)
        # in T$
        cinvest = self.base_invest.get_invest_level('T$')
        self.assertAlmostEqual(norm(cinvest[GlossaryEnergy.InvestValue] - invest_df[GlossaryEnergy.InvestValue] / 1e12),
                               0., 4)

        invest_ref = 3000.  # M$
        years = np.arange(self.y_s, self.y_e + 1, step=self.y_step)
        invest = np.zeros(len(years))
        invest[0] = invest_ref
        for i in range(1, len(years)):
            invest[i] = 1.02 * invest[i - 1]

        invest_df = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: invest})
        self.base_invest.set_invest_level(invest_df, 'M$')
        # in $
        cinvest = self.base_invest.get_invest_level('$')
        self.assertAlmostEqual(norm(cinvest[GlossaryEnergy.InvestValue] - invest_df[GlossaryEnergy.InvestValue] * 1e6),
                               0., 4)
        # in k$
        cinvest = self.base_invest.get_invest_level('k$')
        self.assertAlmostEqual(norm(cinvest[GlossaryEnergy.InvestValue] - invest_df[GlossaryEnergy.InvestValue] * 1e3),
                               0., 4)
        # in M$
        cinvest = self.base_invest.get_invest_level('M$')
        self.assertAlmostEqual(norm(cinvest[GlossaryEnergy.InvestValue] - invest_df[GlossaryEnergy.InvestValue]), 0., 4)
        # in G$
        cinvest = self.base_invest.get_invest_level('G$')
        self.assertAlmostEqual(norm(cinvest[GlossaryEnergy.InvestValue] - invest_df[GlossaryEnergy.InvestValue] / 1e3),
                               0., 4)
        # in T$
        cinvest = self.base_invest.get_invest_level('T$')
        self.assertAlmostEqual(norm(cinvest[GlossaryEnergy.InvestValue] - invest_df[GlossaryEnergy.InvestValue] / 1e6),
                               0., 4)
