'''
Copyright 2023 Capgemini

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

from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.glossaryenergy import GlossaryEnergy


class TestEnergyInvest(AbstractJacobianUnittest):
    """
    Energy Invest test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_02_redistribution_invest_disc_gradient,
            self.test_02_redistribution_invest_disc_gradient_wih_biomass_dry
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefault
        self.y_step = 1
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_list = [GlossaryEnergy.fossil, GlossaryEnergy.renewable]
        self.ccs_list = [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]
        self.economics_df = pd.DataFrame(columns=[GlossaryEnergy.Years, GlossaryEnergy.GrossOutput,
                                                  GlossaryEnergy.OutputNetOfDamage, GlossaryEnergy.PerCapitaConsumption])
        self.economics_df[GlossaryEnergy.Years] = self.years
        self.economics_df[GlossaryEnergy.GrossOutput] = np.linspace(140., 200., len(self.years))
        self.economics_df[GlossaryEnergy.OutputNetOfDamage] = np.linspace(130., 190., len(self.years))
        self.economics_df[GlossaryEnergy.PerCapitaConsumption] = 0.
        self.techno_list_fossil = ['FossilSimpleTechno']
        self.techno_list_renewable = ['RenewableSimpleTechno']
        self.techno_list_carbon_capture = [f'{GlossaryEnergy.direct_air_capture}.DirectAirCaptureTechno',
                                           f'{GlossaryEnergy.flue_gas_capture}.FlueGasTechno']
        self.techno_list_carbon_storage = ['CarbonStorageTechno']

        data_invest = {
            GlossaryEnergy.Years: self.years
        }
        all_techno_list = [self.techno_list_fossil, self.techno_list_renewable, self.techno_list_carbon_capture,
                           self.techno_list_carbon_storage]
        data_invest.update({techno: 100. / 5 for sublist in all_techno_list for techno in sublist})

        self.invest_percentage_per_techno = pd.DataFrame(data=data_invest)
        self.invest_percentage_gdp = pd.DataFrame(data={GlossaryEnergy.Years: self.years,
                                                        GlossaryEnergy.EnergyInvestPercentageGDPName: np.linspace(10.,
                                                                                                                  20.,
                                                                                                                  len(self.years))})
        forest_invest = np.linspace(5, 8, len(self.years))
        self.forest_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.ForestInvestmentValue: forest_invest})
        managed_wood_invest = np.linspace(0.5, 2, len(self.years))
        self.managed_wood_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": managed_wood_invest})
        deforestation_invest = np.linspace(1.0, 0.1, len(self.years))
        self.deforestation_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": deforestation_invest})
        crop_invest = np.linspace(0.5, 0.25, len(self.years))
        self.crop_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": crop_invest})

    def test_01_redistribution_invest_disc(self):
        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: self.name,
                   GlossaryEnergy.NS_REFERENCE: self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   GlossaryEnergy.NS_CCS: f'{self.name}.CCUS',
                   'ns_energy': self.name,
                   GlossaryEnergy.NS_FUNCTIONS: self.name,
                   'ns_invest': f'{self.name}.{self.model_name}'
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.investments_redistribution_disc.InvestmentsRedistributionDisicpline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.energy_list}': self.energy_list,
                       f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.name}.{GlossaryEnergy.fossil}.{GlossaryEnergy.TechnoListName}': self.techno_list_fossil,
                       f'{self.name}.{GlossaryEnergy.renewable}.{GlossaryEnergy.TechnoListName}': self.techno_list_renewable,
                       f'{self.name}.{GlossaryEnergy.CCUS}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.TechnoListName}': self.techno_list_carbon_capture,
                       f'{self.name}.{GlossaryEnergy.CCUS}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.TechnoListName}': self.techno_list_carbon_storage,
                       f'{self.name}.{GlossaryEnergy.EconomicsDfValue}': self.economics_df,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoInvestPercentageName}': self.invest_percentage_per_techno,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyInvestPercentageGDPName}': self.invest_percentage_gdp,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ForestInvestmentValue}': self.forest_invest_df
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        # assert that for fossil techno and direct air capture, investment is 10% * 130 * 20% at 2020 and 20% * 190 * 20%
        fossil_invest_level = \
            self.ee.dm.get_value(
                f'{self.name}.{GlossaryEnergy.fossil}.FossilSimpleTechno.{GlossaryEnergy.InvestLevelValue}')[
                GlossaryEnergy.InvestValue].values
        fossil_invest_2020 = fossil_invest_level[0]
        fossil_invest_2050 = fossil_invest_level[-1]
        error_message = 'Error in investment, it is not equal to expected'
        self.assertAlmostEqual(fossil_invest_2020, 0.1 * 130 * 1e3 * 0.2, msg=error_message)
        self.assertAlmostEqual(fossil_invest_2050, 0.2 * 190 * 1e3 * 0.2, msg=error_message)

        dac_invest_level = \
            self.ee.dm.get_value(f'{self.name}.{GlossaryEnergy.CCUS}.{GlossaryEnergy.carbon_capture}.direct_air_capture'
                                 f'.DirectAirCaptureTechno.{GlossaryEnergy.InvestLevelValue}')[
                GlossaryEnergy.InvestValue].values
        dac_invest_2020 = dac_invest_level[0]
        dac_invest_2050 = dac_invest_level[-1]
        self.assertAlmostEqual(dac_invest_2020, 0.1 * 130 * 1e3 * 0.2,
                               msg=error_message)
        self.assertAlmostEqual(dac_invest_2050, 0.2 * 190 * 1e3 * 0.2,
                               msg=error_message)

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

        for graph in graph_list:
            pass
            # graph.to_plotly().show()

    def test_02_redistribution_invest_disc_gradient(self):
        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: self.name,
                   GlossaryEnergy.NS_REFERENCE: self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   GlossaryEnergy.NS_CCS: f'{self.name}',
                   'ns_energy': self.name,
                   GlossaryEnergy.NS_FUNCTIONS: self.name,
                   'ns_invest': f'{self.name}.{self.model_name}'
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.investments_redistribution_disc.InvestmentsRedistributionDisicpline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.energy_list}': self.energy_list,
                       f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.name}.{GlossaryEnergy.fossil}.{GlossaryEnergy.TechnoListName}': self.techno_list_fossil,
                       f'{self.name}.{GlossaryEnergy.renewable}.{GlossaryEnergy.TechnoListName}': self.techno_list_renewable,
                       f'{self.name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.TechnoListName}': self.techno_list_carbon_capture,
                       f'{self.name}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.TechnoListName}': self.techno_list_carbon_storage,
                       f'{self.name}.{GlossaryEnergy.EconomicsDfValue}': self.economics_df,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoInvestPercentageName}': self.invest_percentage_per_techno,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyInvestPercentageGDPName}': self.invest_percentage_gdp,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ForestInvestmentValue}': self.forest_invest_df
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()
        disc = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        all_technos_list = [
            f'{energy}.{techno}' for energy in self.energy_list + self.ccs_list for techno in
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.techno_list}']]

        self.check_jacobian(location=dirname(__file__), filename='jacobian_redistribution_invest_disc_wo_biomass.pkl',
                            discipline=disc, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=[f'{self.name}.{GlossaryEnergy.EconomicsDfValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.ForestInvestmentValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyInvestPercentageGDPName}'
                                    ],
                            outputs=[f'{self.name}.{techno}.{GlossaryEnergy.InvestLevelValue}' for techno in
                                     all_technos_list] + [
                                        f'{self.name}.{GlossaryEnergy.EnergyInvestmentsWoTaxValue}'], )

    def test_02_redistribution_invest_disc_gradient_wih_biomass_dry(self):
        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: self.name,
                   GlossaryEnergy.NS_REFERENCE: self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   GlossaryEnergy.NS_CCS: f'{self.name}',
                   'ns_energy': self.name,
                   GlossaryEnergy.NS_FUNCTIONS: self.name,
                   'ns_invest': f'{self.name}.{self.model_name}',
                   'ns_forest': self.name,
                   'ns_crop': self.name
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.investments_redistribution_disc.InvestmentsRedistributionDisicpline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.energy_list}': self.energy_list + [GlossaryEnergy.biomass_dry],
                       f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.name}.{GlossaryEnergy.fossil}.{GlossaryEnergy.TechnoListName}': self.techno_list_fossil,
                       f'{self.name}.{GlossaryEnergy.renewable}.{GlossaryEnergy.TechnoListName}': self.techno_list_renewable,
                       f'{self.name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.TechnoListName}': self.techno_list_carbon_capture,
                       f'{self.name}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.TechnoListName}': self.techno_list_carbon_storage,
                       f'{self.name}.{GlossaryEnergy.biomass_dry}.{GlossaryEnergy.TechnoListName}': [],
                       f'{self.name}.{GlossaryEnergy.EconomicsDfValue}': self.economics_df,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoInvestPercentageName}': self.invest_percentage_per_techno,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyInvestPercentageGDPName}': self.invest_percentage_gdp,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ForestInvestmentValue}': self.forest_invest_df,
                       f'{self.name}.managed_wood_investment': self.managed_wood_invest_df,
                       f'{self.name}.deforestation_investment': self.deforestation_invest_df,
                       f'{self.name}.crop_investment': self.crop_invest_df
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()
        disc = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        all_technos_list = [
            f'{energy}.{techno}' for energy in self.energy_list + self.ccs_list for techno in
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.techno_list}']]

        self.check_jacobian(location=dirname(__file__), filename='jacobian_redistribution_invest_disc_w_biomass.pkl',
                            discipline=disc, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=[f'{self.name}.{GlossaryEnergy.EconomicsDfValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.ForestInvestmentValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyInvestPercentageGDPName}',
                                    f'{self.name}.managed_wood_investment',
                                    f'{self.name}.deforestation_investment',
                                    f'{self.name}.crop_investment'],
                            outputs=[f'{self.name}.{techno}.{GlossaryEnergy.InvestLevelValue}' for techno in
                                     all_technos_list] + [
                                        f'{self.name}.{GlossaryEnergy.EnergyInvestmentsWoTaxValue}'], )
