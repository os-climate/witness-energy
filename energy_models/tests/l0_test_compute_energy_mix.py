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
import os

import numpy as np
import pandas as pd
from sostrades_optimization_plugins.models.test_class import GenericDisciplinesTestClass

from energy_models.glossaryenergy import GlossaryEnergy


class EnergyMixTestCase(GenericDisciplinesTestClass):
    """
    ENergyMix test class
    """

    def setUp(self):
        self.name = 'Test'
        self.model_name = 'EnergyMix'
        self.ns_dict = {
            'ns_public': self.name,
            GlossaryEnergy.NS_CCS: self.name,
            'ns_energy_study': f'{self.name}',
            GlossaryEnergy.NS_WITNESS: f'{self.name}',
            GlossaryEnergy.NS_FUNCTIONS: f'{self.name}.{self.model_name}',
            GlossaryEnergy.NS_ENERGY_MIX: self.name
        }

        self.pickle_prefix = self.model_name
        self.jacobian_test = False
        self.show_graphs = False
        self.override_dump_jacobian = False
        self.pickle_directory = os.path.dirname(__file__)


        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefault
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.year_range = self.year_end - self.year_start + 1
        self.energy_list = [f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}', GlossaryEnergy.methane]
        self.energy_type_capital = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.Capital: 0.001, GlossaryEnergy.NonUseCapital: 0.})
        self.energy_consumption_hydro = pd.DataFrame(
            {f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': np.linspace(5., 7., len(self.years)),
             f'{GlossaryEnergy.methane} ({GlossaryEnergy.energy_unit})': np.linspace(13., 16., len(self.years))})

        self.resource_consumption_hydro = pd.DataFrame({'water (Mt)': np.linspace(8., 10., len(self.years))})

        self.production_hydro = pd.DataFrame({
            f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': np.linspace(28., 37., len(self.years))
        })

        self.prices_hydro = pd.DataFrame(
            {f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': np.linspace(76, 62, len(self.years)),
             f'{GlossaryEnergy.hydrogen}.gaseous_hydrogen_wotaxes': np.linspace(66, 52, len(self.years))})

        self.methane_energy_consumption = pd.DataFrame(
            {f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': np.linspace(7., 6000., len(self.years)),
             f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': np.linspace(12, 492, len(self.years)),
             f'{GlossaryEnergy.biogas} ({GlossaryEnergy.energy_unit})': np.linspace(142, 5910, len(self.years)),})

        self.methane_resource_consumption = pd.DataFrame(
            {'CO2 (Mt)': np.linspace(1.28, 1.14, len(self.years)),
             'MEA (Mt)': np.linspace(.7, 293., len(self.years)),
             'oil_resource (Mt)': np.linspace(.7, 293., len(self.years)), })

        self.methane_emissions = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.CO2: 0.,
            GlossaryEnergy.CH4: 10.,
            GlossaryEnergy.N2O: 0.
        })

        self.methane_emissions_intensity = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.CO2: 0.,
            GlossaryEnergy.CH4: 0.10,
            GlossaryEnergy.N2O: 0.
        })

        self.hydrogen_emissions = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.CO2: 10.,
            GlossaryEnergy.CH4: 3.,
            GlossaryEnergy.N2O: 1.
        })

        self.hydrogen_emissions_intensity = self.hydrogen_emissions / 10.

        self.production_methane = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f'{GlossaryEnergy.methane}': np.linspace(2.6, 2300, len(self.years))})

        self.cost_details = pd.DataFrame({GlossaryEnergy.methane:  np.linspace(193, 336, len(self.years)),
                                          'methane_wotaxes': np.linspace(193, 336, len(self.years)), })
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
            {GlossaryEnergy.Years: self.years, "Land use": 0.0})

        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)

        self.co2_taxes = pd.DataFrame({
            GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})

        self.stream_ccs_consumption = pd.DataFrame({GlossaryEnergy.Years: years,})

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

    def get_inputs_dict(self) -> dict:
        return {
            f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
            f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
            f'{self.name}.{GlossaryEnergy.energy_list}': [
                f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}', GlossaryEnergy.methane],
            f'{self.name}.{GlossaryEnergy.ccs_list}': [],
            f'{self.name}.is_dev': True,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.StreamPricesValue}': pd.DataFrame(
                {f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': self.prices_hydro[
                    f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'],
                 GlossaryEnergy.methane: self.cost_details[GlossaryEnergy.methane]}),
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamEnergyConsumptionValue}': self.energy_consumption_hydro,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamEnergyDemandValue}': self.energy_consumption_hydro,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamProductionValue}': self.production_hydro,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamPricesValue}': self.prices_hydro,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.EnergyTypeCapitalDfValue}': self.energy_type_capital,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.CO2PerUse}': pd.DataFrame(
                {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2PerUse: 0.0}),
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.CO2EmissionsValue}': pd.DataFrame(
                {GlossaryEnergy.Years: self.years,
                 f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0.0}),
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_mock,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamEnergyConsumptionValue}': self.methane_energy_consumption,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamEnergyDemandValue}': self.methane_energy_consumption,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamResourceConsumptionValue}': self.methane_resource_consumption,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamResourceDemandValue}': self.methane_resource_consumption,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamResourceDemandValue}': self.resource_consumption_hydro,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamResourceConsumptionValue}': self.resource_consumption_hydro,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamScope1GHGEmissionsValue}': self.hydrogen_emissions,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamScope1GHGIntensityValue}': self.hydrogen_emissions_intensity,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamCCSDemandValue}': self.stream_ccs_consumption,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.StreamCCSConsumptionValue}': self.stream_ccs_consumption,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamCCSDemandValue}': self.stream_ccs_consumption,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamCCSConsumptionValue}': self.stream_ccs_consumption,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamScope1GHGEmissionsValue}': self.methane_emissions,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamScope1GHGIntensityValue}': self.methane_emissions_intensity,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamProductionValue}': self.production_methane,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.StreamPricesValue}': self.cost_details,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.EnergyTypeCapitalDfValue}': self.energy_type_capital,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_mock,
            f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
            f'{self.name}.{self.model_name}.liquid_hydrogen_percentage': self.liquid_hydrogen_percentage,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.loss_percentage': 1.0,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.methane}.{GlossaryEnergy.loss_percentage}': 2.0,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.TargetEnergyProductionValue}': self.target_production
        }


    def test_01_energy_mix_discipline(self):
        """
        Test energy mix discipline

        Returns
        -------
        None.

        """

        self.mod_path = 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline'
