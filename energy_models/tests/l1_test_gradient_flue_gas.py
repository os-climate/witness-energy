'''
Copyright 2022 Airbus SAS
Modifications on 2023/08/23-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_optimization_plugins.models.test_class import GenericDisciplinesTestClass

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
)
from energy_models.glossaryenergy import GlossaryEnergy


class GradientFlueGasTestCase(GenericDisciplinesTestClass):
    """Flue gas gradients test class"""

    def setUp(self):
        self.jacobian_test = True
        self.show_graphs = False
        self.override_dump_jacobian = False
        self.pickle_directory = dirname(__file__)

        self.name = "Test"
        self.pickle_directory = dirname(__file__)
        self.ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   GlossaryEnergy.NS_WITNESS: self.name,
                   GlossaryEnergy.NS_CCS: self.name,
                   'ns_energy_study': f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   
                   'ns_flue_gas': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_carbon_capture': self.name,
                   'ns_resource': f'{self.name}'}

        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)

        self.stream_name = 'flue_gas'

        self.flue_gas_mean = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.FlueGasMean: 0.3})

        self.flue_gas_mean_swing = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.FlueGasMean: 0.1})

        self.flue_gas_mean_piperazine = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.FlueGasMean: 0.2})

        self.stream_prices = pd.DataFrame(
            {GlossaryEnergy.Years: self.years,
             GlossaryEnergy.electricity: 80.0,
             GlossaryEnergy.methane: 80.0})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: np.linspace(22., 31., len(self.years))})

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})

        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years,
             GlossaryEnergy.MarginValue: 100})

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 0.0, GlossaryEnergy.methane: 0.2})
        self.carbon_storage_availability_ratio = pd.DataFrame({
            GlossaryEnergy.Years: self.years, GlossaryEnergy.carbon_captured: 100.,
            GlossaryEnergy.carbon_storage: 100.})

        transport_cost = 0

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': transport_cost})

        self.resources_price = pd.DataFrame({GlossaryEnergy.Years: self.years})
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(self.years))))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.resource_list, np.linspace(1.0, 1.0, len(self.years))))
        resource_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def get_inputs_dict(self):
        return {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(self.years),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.FlueGasMean}': self.flue_gas_mean_swing,
                       f'{self.name}.{GlossaryEnergy.CO2}_intensity_by_energy': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.CH4}_intensity_by_energy': self.stream_co2_emissions * 0.1,
                       f'{self.name}.{GlossaryEnergy.N2O}_intensity_by_energy': self.stream_co2_emissions * 0.01,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                f'{self.name}.{GlossaryEnergy.CCUSAvailabilityRatiosValue}': self.carbon_storage_availability_ratio,}
    def test_01_calcium_looping_discipline_analytic_grad(self):
        self.model_name = 'CalciumLooping'
        self.mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.calcium_looping.calcium_looping_disc.CalciumLoopingDiscipline'



    def test_02_pressure_swing_adsorption_analytic_grad(self):
        self.model_name = 'pressure_swing_adsorption'
        self.mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.pressure_swing_adsorption.pressure_swing_adsorption_disc.PressureSwingAdsorptionDiscipline'


    def test_03_piperazine_process_analytic_grad(self):
        self.model_name = 'piperazine_process'
        self.mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.piperazine_process.piperazine_process_disc.PiperazineProcessDiscipline'


    def test_04_monoethanolamine_analytic_grad(self):
        self.model_name = 'mono_ethanol_amine'
        self.mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.mono_ethanol_amine.mono_ethanol_amine_disc.MonoEthanolAmineDiscipline'



    def test_05_co2_membranes_analytic_grad(self):
        self.model_name = 'CO2_membranes'
        self.mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.co2_membranes.co2_membranes_disc.CO2MembranesDiscipline'


    def test_06_chilled_ammonia_process_discipline_analytic_grad(self):
        self.model_name = 'chilled_ammonia_process'
        self.mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.chilled_ammonia_process.chilled_ammonia_process_disc.ChilledAmmoniaProcessDiscipline'

