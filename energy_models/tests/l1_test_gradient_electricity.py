'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/21-2024/06/24 Copyright 2023 Capgemini

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
from os.path import dirname, join

import numpy as np
import pandas as pd
from sostrades_optimization_plugins.models.test_class import GenericDisciplinesTestClass

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.glossaryenergy import GlossaryEnergy


class ElectricityJacobianTestCase(GenericDisciplinesTestClass):
    """Electricity jacobian test class"""

    def setUp(self):

        self.name = "Test"
        self.override_dump_jacobian = False
        self.show_graph = False
        self.jacobian_test = True
        self.pickle_directory = dirname(__file__)
        self.stream_name = GlossaryEnergy.electricity
        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest

        self.years = np.arange(self.year_start, self.year_end + 1)

        # --- energy prices ---
        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                           GlossaryEnergy.electricity: 90,
                                           GlossaryEnergy.solid_fuel: 5.7,
                                           f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}': 91,
                                           GlossaryEnergy.methane: 27.07,
                                           GlossaryEnergy.biogas: 5.0,
                                           GlossaryEnergy.biomass_dry: 11.0,
                                           GlossaryEnergy.mediumtemperatureheat_energyname: 4.5
             })
        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.methane: 0.123 / 15.4, GlossaryEnergy.biogas: 0.123 / 15.4,
             GlossaryEnergy.solid_fuel: 0.64 / 4.86, f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}': 0.64 / 4.86, GlossaryEnergy.biomass_dry: - 0.64 / 4.86,
             GlossaryEnergy.electricity: 0.0, GlossaryEnergy.mediumtemperatureheat_energyname: 6.2})

        # --- invest level ---
        self.invest_level_ccgast = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 21.0})

        self.invest_level_biomass_fired = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 21.0})

        self.invest_level_geothermal = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.invest_level_geothermal[GlossaryEnergy.InvestValue] = 5.0 * \
                                                                   1.10 ** (self.invest_level_geothermal[
                                                                                GlossaryEnergy.Years] - GlossaryEnergy.YearStartDefault)

        self.invest_level_solar_pv = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 130.0})

        self.invest_level_solar_thermal = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 15.0})

        self.invest_level_coal = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 50.0})

        self.invest_level_oil = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 10.0})

        self.invest_level_nuclear = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.invest_level_nuclear[GlossaryEnergy.InvestValue] = 33.0 * \
                                                                1.10 ** (self.invest_level_nuclear[
                                                                             GlossaryEnergy.Years] - GlossaryEnergy.YearStartDefault)

        self.invest_level_hydropower = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                     GlossaryEnergy.InvestValue: np.linspace(4435750000.0, 5093000000.0, len(self.years)) * 1.0e-9})
        self.invest_level_windonshore = pd.DataFrame(
            {GlossaryEnergy.Years: self.years,
             GlossaryEnergy.InvestValue: np.linspace(22., 31., len(self.years))})
        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14.86, 50.29, len(self.years))})
        self.co2_taxes_nul = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: 0})

        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 110.0})

        # --- Transport ---
        transport_cost = 11.0
        # It is noteworthy that the cost of transmission has generally been held (and can
        # continue to be held)    within the 10-12/MWhr range despite transmission distances
        # increasing by almost an order of magnitude from an average of 20km for the
        # leftmost bar to 170km for the 2020 scenarios / OWPB 2016

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': transport_cost})

        self.transport_nul = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': 0.})

        # --- resources ---
        self.resources_price = pd.DataFrame(
            columns=[GlossaryEnergy.Years, 'water'])
        self.resources_price[GlossaryEnergy.Years] = self.years
        self.resources_price['water'] = Water.data_energy_dict['cost_now']
        self.resources_price['uranium fuel'] = 1390.0e3

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == f'{GlossaryEnergy.electricity}.{GlossaryEnergy.CombinedCycleGasTurbine}']
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(50.0, 50.0, len(self.years))))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.resource_list, np.linspace(50.0, 50.0, len(self.years))))
        resource_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

        self.ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                        'ns_energy_study': f'{self.name}',
                   GlossaryEnergy.NS_WITNESS: f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   
                        'ns_electricity': self.name,
                        'ns_resource': f'{self.name}'}

    def get_inputs_dict(self):
        return {
            f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
            f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
            f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
               self.years),
            f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
            f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
            f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes_nul,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_biomass_fired,
            f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
            f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
               [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
               keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
            f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
            f'{self.name}.{GlossaryEnergy.CO2}_intensity_by_energy': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.CH4}_intensity_by_energy': self.stream_co2_emissions * 0.1,
                       f'{self.name}.{GlossaryEnergy.N2O}_intensity_by_energy': self.stream_co2_emissions * 0.01,
            f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
            f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
        }

    def test_01_combined_cycle_gas_turbine_discipline_analytic_grad(self):
        self.model_name = 'cc_gas_turbine'
        self.mod_path = 'energy_models.models.electricity.gas.combined_cycle_gas_turbine.combined_cycle_gas_turbine_disc.CombinedCycleGasTurbineDiscipline'


    def test_02_geothermal_discipline_analytic_grad(self):
        self.model_name = 'geothermal_high_heat'
        self.mod_path = 'energy_models.models.electricity.geothermal.geothermal_disc.GeothermalDiscipline'


    def test_03_hydropower_discipline_analytic_grad(self):
        self.model_name = 'hydropower'
        self.mod_path = 'energy_models.models.electricity.hydropower.hydropower_disc.HydropowerDiscipline'

    def test_04_coal_gen_discipline_analytic_grad(self):
        self.model_name = 'coal_gen'
        self.mod_path = 'energy_models.models.electricity.coal_gen.coal_gen_disc.CoalGenDiscipline'

    def test_05_gas_turbine_discipline_analytic_grad(self):
        self.model_name = 'gas_turbine'
        self.mod_path = 'energy_models.models.electricity.gas.gas_turbine.gas_turbine_disc.GasTurbineDiscipline'

    def test_06_wind_on_shore_discipline_analytic_grad(self):
        self.model_name = 'wind_on_shore'
        self.mod_path = 'energy_models.models.electricity.wind_onshore.wind_onshore_disc.WindOnshoreDiscipline'

    def test_07_wind_off_shore_discipline_analytic_grad(self):
        self.model_name = 'wind_off_shore'
        self.mod_path = 'energy_models.models.electricity.wind_offshore.wind_offshore_disc.WindOffshoreDiscipline'

    def test_08_solar_thermal_discipline_analytic_grad(self):
        self.model_name = 'solar_thermal'
        self.mod_path = 'energy_models.models.electricity.solar_thermal.solar_thermal_disc.SolarThermalDiscipline'

    def test_09_solar_pv_discipline_analytic_grad(self):
        self.model_name = 'solar_pv'
        self.mod_path = 'energy_models.models.electricity.solar_pv.solar_pv_disc.SolarPvDiscipline'

    def test_10_nuclear_discipline_analytic_grad(self):
        self.model_name = 'nuclear'
        self.mod_path = 'energy_models.models.electricity.nuclear.nuclear_disc.NuclearDiscipline'

    def test_11_biogas_fired_discipline_analytic_grad(self):
        self.model_name = 'biogas_fired'
        self.mod_path = 'energy_models.models.electricity.gas.biogas_fired.biogas_fired_disc.BiogasFiredDiscipline'

    def test_12_biomass_fired_discipline_analytic_grad(self):
        self.model_name = 'biomass_fired'
        self.mod_path = 'energy_models.models.electricity.biomass_fired.biomass_fired_disc.BiomassFiredDiscipline'

    def test_13_oil_gen_discipline_analytic_grad(self):
        self.model_name = 'oil_gen'
        self.mod_path = 'energy_models.models.electricity.oil_gen.oil_gen_disc.OilGenDiscipline'
