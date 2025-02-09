'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tools.post_processing.post_processing_factory import (
    PostProcessingFactory,
)

from energy_models.glossaryenergy import GlossaryEnergy


class EnergyMixTestCase(unittest.TestCase):
    """
    ENergyMix test class
    """

    def setUp(self):
        
        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefault
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.year_range = self.year_end - self.year_start + 1
        self.energy_list = [f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}', GlossaryEnergy.methane]
        self.energy_type_capital = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.Capital: 0.001, GlossaryEnergy.NonUseCapital: 0.})
        self.consumption_hydro = pd.DataFrame(
            {f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': np.linspace(5., 7., len(self.years)),
             f'{GlossaryEnergy.methane} ({GlossaryEnergy.energy_unit})': np.linspace(13., 16., len(self.years)),
             'water (Mt)': np.linspace(8., 10., len(self.years))})

        self.production_hydro = pd.DataFrame(
            {f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': np.linspace(28., 37., len(self.years)),
             f'{GlossaryEnergy.hydrogen} SMR (TWh)': np.linspace(14., 18., len(self.years)),
             'CO2 (Mt)': np.linspace(1.4, 1.8, len(self.years)),
             f'{GlossaryEnergy.hydrogen} Electrolysis (TWh)': np.linspace(14., 19., len(self.years)),
             'O2 (Mt)': np.linspace(1.4, 1.8, len(self.years))})

        self.prices_hydro = pd.DataFrame(
            {f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': np.linspace(76, 62, len(self.years)),
             f'{GlossaryEnergy.hydrogen}.gaseous_hydrogen_wotaxes': np.linspace(66, 52, len(self.years))})

        self.consumption = pd.DataFrame(
            {'CO2 (Mt)': np.linspace(1.28, 1.14, len(self.years)),
             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': np.linspace(7., 6000., len(self.years)),
             f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': np.linspace(12, 492, len(self.years)),
             f'{GlossaryEnergy.biogas} ({GlossaryEnergy.energy_unit})': np.linspace(142, 5910, len(self.years)),
             'MEA (Mt)': np.linspace(.7, 293., len(self.years)),
             'oil_resource (Mt)': np.linspace(.7, 293., len(self.years)),})

        self.production = pd.DataFrame(
            {GlossaryEnergy.methane: np.linspace(116, 6800., len(self.years)),
             f'{GlossaryEnergy.methane} Emethane (TWh)': np.linspace(2.6, 2300, len(self.years)),
             GlossaryEnergy.InvestValue:  np.linspace(8., 10., len(self.years)),
             'water (Mt)':  np.linspace(.8, 375, len(self.years)),
             f'{GlossaryEnergy.methane} UpgradingBiogas (TWh)':  np.linspace(114, 4500, len(self.years)),
             'CO2 (Mt)':  np.linspace(5, 222, len(self.years))})

        self.cost_details = pd.DataFrame({GlossaryEnergy.methane:  np.linspace(193, 336, len(self.years)),
                                          'methane_wotaxes': np.linspace(193, 336, len(self.years)),})
        # Biomass dry inputs coming from agriculture mix disc
        #
        energy_consumption_biomass = np.linspace(0, 4, self.year_range)
        self.energy_consumption_biomass = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'CO2_resource (Mt)': energy_consumption_biomass})

        energy_consumption_woratio_biomass = np.linspace(0, 4, self.year_range)
        self.energy_consumption_woratio_biomass = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'CO2_resource (Mt)': energy_consumption_woratio_biomass})

        energy_production_biomass = np.linspace(15, 16, self.year_range)
        self.energy_production_biomass = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.biomass_dry: energy_production_biomass})

        energy_prices_biomass = np.linspace(9, 9, self.year_range)
        energy_prices_wotaxes_biomass = np.linspace(9, 9, self.year_range)
        self.stream_prices_biomass = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.biomass_dry: energy_prices_biomass,
             'biomass_dry_wotaxes': energy_prices_wotaxes_biomass})

        CO2_per_use_biomass = np.linspace(0, 1, self.year_range)
        self.CO2_per_use_biomass = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2PerUse: CO2_per_use_biomass})

        CO2_emissions_biomass = np.linspace(0, -1, self.year_range)
        self.CO2_emissions_biomass = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.biomass_dry: CO2_emissions_biomass})

        self.land_use_required_mock = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'random techno (Gha)': 0.0})

        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})

        self.minimum_energy_production = 1e4
        self.production_threshold = 1e-3
        self.total_prod_minus_min_prod_constraint_ref = 1e4
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(GlossaryEnergy.unit_dicts.keys(), np.ones((len(self.years), len(self.years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.liquid_hydrogen_percentage = np.ones(len(self.years))
        self.target_production = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.TargetEnergyProductionValue: 280000
        })

    def test_01_energy_mix_discipline(self):
        """
        Test energy mix discipline

        Returns
        -------
        None.

        """

        name = 'Test'
        model_name = 'EnergyMix'
        agriculture_mix = 'AgricultureMix'
        ee = ExecutionEngine(name)
        ns_dict = {'ns_public': f'{name}',
                   'ns_hydrogen': f'{name}',
                   'ns_methane': f'{name}',
                   'ns_energy_study': f'{name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{name}.{model_name}',
                   GlossaryEnergy.NS_FUNCTIONS: f'{name}.{model_name}',
                   'ns_resource': f'{name}.{model_name}.resource',
                   GlossaryEnergy.NS_CCS: f'{name}.{model_name}',
                   'ns_energy': f'{name}.{model_name}',
                   GlossaryEnergy.NS_WITNESS: f'{name}'}
        ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline'
        builder = ee.factory.get_builder_from_module(model_name, mod_path)

        ee.factory.set_builders_to_coupling_builder(builder)

        ee.configure()
        ee.display_treeview_nodes()

        inputs_dict = {f'{name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{name}.{GlossaryEnergy.energy_list}': [f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}', GlossaryEnergy.methane],
                       f'{name}.{GlossaryEnergy.ccs_list}': [],
                       f'{name}.is_dev': True,
                       f'{name}.{model_name}.{GlossaryEnergy.EnergyPricesValue}': pd.DataFrame(
                           {f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': self.prices_hydro[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'],
                            GlossaryEnergy.methane: self.cost_details[GlossaryEnergy.methane]}),
                       f'{name}.{model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamEnergyConsumptionValue}': self.consumption_hydro,
                       f'{name}.{model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamConsumptionDemandsValue}': self.consumption_hydro,
                       f'{name}.{model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamProductionValue}': self.production_hydro,
                       f'{name}.{model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.EnergyPricesValue}': self.prices_hydro,
                       f'{name}.{model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.EnergyTypeCapitalDfValue}': self.energy_type_capital,
                       f'{name}.{model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.CO2PerUse}': pd.DataFrame(
                           {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2PerUse: 0.0}),
                       f'{name}.{model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.CO2EmissionsValue}': pd.DataFrame(
                           {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0.0}),
                       f'{name}.{model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_mock,
                       f'{name}.{agriculture_mix}.{GlossaryEnergy.StreamEnergyConsumptionValue}': self.energy_consumption_biomass,
                       f'{name}.{agriculture_mix}.{GlossaryEnergy.StreamConsumptionDemandsValue}': self.energy_consumption_biomass,
                       f'{name}.{agriculture_mix}.{GlossaryEnergy.StreamProductionValue}': self.energy_production_biomass,
                       f'{name}.{model_name}.{agriculture_mix}.{GlossaryEnergy.EnergyTypeCapitalDfValue}': self.energy_type_capital,
                       f'{name}.{agriculture_mix}.{GlossaryEnergy.EnergyPricesValue}': self.stream_prices_biomass,
                       f'{name}.{agriculture_mix}.{GlossaryEnergy.CO2PerUse}': self.CO2_per_use_biomass,
                       f'{name}.{agriculture_mix}.{GlossaryEnergy.CO2EmissionsValue}': self.CO2_emissions_biomass,
                       f'{name}.{agriculture_mix}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_mock,
                       f'{name}.{model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamEnergyConsumptionValue}': self.consumption,
                       f'{name}.{model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamConsumptionDemandsValue}': self.consumption,
                       f'{name}.{model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamProductionValue}': self.production,
                       f'{name}.{model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.EnergyPricesValue}': self.cost_details,
                       f'{name}.{model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.EnergyTypeCapitalDfValue}': self.energy_type_capital,
                       f'{name}.{model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.CO2PerUse}': pd.DataFrame(
                           {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2PerUse: 0.0}),
                       f'{name}.{model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.CO2EmissionsValue}': pd.DataFrame(
                           {GlossaryEnergy.Years: self.years, GlossaryEnergy.methane: 0.0}),
                       f'{name}.{model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_mock,
                       f'{name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{name}.{model_name}.liquid_hydrogen_percentage': self.liquid_hydrogen_percentage,
                       f'{name}.{model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.loss_percentage': 1.0,
                       f'{name}.{model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.loss_percentage}': 2.0,
                       f'{name}.{model_name}.{GlossaryEnergy.TargetEnergyProductionValue}': self.target_production
                       }

        ee.load_study_from_input_dict(inputs_dict)

        ee.execute()

        disc = ee.dm.get_disciplines_with_name(
            f'{name}.{model_name}')[0]
        ppf = PostProcessingFactory()
        filters = ppf.get_post_processing_filters_by_discipline(disc)
        graph_list = ppf.get_post_processing_by_discipline(
            disc, filters, as_json=False)

        for graph in graph_list:
            #graph.to_plotly().show()
            pass




if '__main__' == __name__:
    cls = EnergyMixTestCase()
    cls.setUp()
    cls.test_02_energy_mix_discipline()
