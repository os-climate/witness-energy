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
import pickle
from os.path import dirname, join

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.biomass_fired.biomass_fired_disc import (
    BiomassFiredDiscipline,
)
from energy_models.models.electricity.coal_gen.coal_gen_disc import CoalGenDiscipline
from energy_models.models.electricity.gas.biogas_fired.biogas_fired_disc import (
    BiogasFiredDiscipline,
)
from energy_models.models.electricity.gas.combined_cycle_gas_turbine.combined_cycle_gas_turbine_disc import (
    CombinedCycleGasTurbineDiscipline,
)
from energy_models.models.electricity.gas.gas_turbine.gas_turbine_disc import (
    GasTurbineDiscipline,
)
from energy_models.models.electricity.geothermal.geothermal_disc import (
    GeothermalDiscipline,
)
from energy_models.models.electricity.hydropower.hydropower_disc import (
    HydropowerDiscipline,
)
from energy_models.models.electricity.nuclear.nuclear_disc import NuclearDiscipline
from energy_models.models.electricity.oil_gen.oil_gen_disc import OilGenDiscipline
from energy_models.models.electricity.solar_pv.solar_pv_disc import SolarPvDiscipline
from energy_models.models.electricity.solar_thermal.solar_thermal_disc import (
    SolarThermalDiscipline,
)
from energy_models.models.electricity.wind_offshore.wind_offshore_disc import (
    WindOffshoreDiscipline,
)
from energy_models.models.electricity.wind_onshore.wind_onshore_disc import (
    WindOnshoreDiscipline,
)


class ElectricityJacobianTestCase(AbstractJacobianUnittest):
    """
    Electricity jacobian test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_combined_cycle_gas_turbine_discipline_analytic_grad,
            self.test_02_geothermal_discipline_analytic_grad,
            self.test_03_hydropower_discipline_analytic_grad,
            self.test_04_coal_gen_discipline_analytic_grad,
            self.test_05_gas_turbine_discipline_analytic_grad,
            self.test_06_wind_on_shore_discipline_analytic_grad,
            self.test_07_wind_off_shore_discipline_analytic_grad,
            self.test_08_solar_thermal_discipline_analytic_grad,
            self.test_09_solar_pv_discipline_analytic_grad,
            self.test_10_nuclear_discipline_analytic_grad,
            self.test_11_biogas_fired_discipline_analytic_grad,
            self.test_12_biomass_fired_discipline_analytic_grad,
            self.test_14_electricity_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = GlossaryEnergy.electricity
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
            {GlossaryEnergy.Years: self.years, 'transport': np.zeros(len(self.years))})

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
            zip(EnergyMix.RESOURCE_LIST, np.linspace(50.0, 50.0, len(self.years))))
        resource_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_combined_cycle_gas_turbine_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'cc_gas_turbine'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.gas.combined_cycle_gas_turbine.combined_cycle_gas_turbine_disc.CombinedCycleGasTurbineDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = CombinedCycleGasTurbineDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes_nul,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_ccgast,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict, }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(
            location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
            local_data=disc_techno.local_data,
            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                    ],
            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                     ], )

    def test_02_geothermal_discipline_analytic_grad(self):
        self.name = 'Test'
        self.model_name = 'geothermal_high_heat'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.geothermal.geothermal_disc.GeothermalDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = GeothermalDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_geothermal,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport_nul,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(
            location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}_zz.pkl',
            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
            local_data=disc_techno.local_data,
            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                    ],
            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                     ], )

    def test_03_hydropower_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'hydropower'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.hydropower.hydropower_disc.HydropowerDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = HydropowerDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_hydropower,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: self.years}),
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(
            location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
            local_data=disc_techno.local_data,
            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                    # f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                    # f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                    # f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                    # f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                    ],
            outputs=[  # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                # f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
            ], )

    def test_04_coal_gen_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'coal_gen'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}',
                   'ns_solid_fuel': f'{self.name}',
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.coal_gen.coal_gen_disc.CoalGenDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = CoalGenDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_coal,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport_nul,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(
            location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
            local_data=disc_techno.local_data,
            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                    ],
            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                     ], )

    def test_05_gas_turbine_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'gas_turbine'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.gas.gas_turbine.gas_turbine_disc.GasTurbineDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = GasTurbineDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes_nul,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_ccgast,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio[
                           [GlossaryEnergy.Years, GlossaryEnergy.methane]],
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-15, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     ], )

    def test_06_wind_on_shore_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'wind_on_shore'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.wind_onshore.wind_onshore_disc.WindOnshoreDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = WindOnshoreDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_windonshore,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: self.years}),
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                                    # f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    # f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[  # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                            ], )

    def test_07_wind_off_shore_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'wind_off_shore'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.wind_offshore.wind_offshore_disc.WindOffshoreDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = WindOffshoreDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       # same invest on and off shore
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_windonshore,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: self.years}),
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                                    # f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    # f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[  # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                            ], )

    def test_08_solar_thermal_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'solar_thermal'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.solar_thermal.solar_thermal_disc.SolarThermalDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = SolarThermalDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_solar_thermal,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: self.years}),
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                                    # f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    # f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[  # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',

                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.LandUseRequiredValue}'
                            ], )

    def test_09_solar_pv_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'solar_pv'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.solar_pv.solar_pv_disc.SolarPvDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = SolarPvDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_solar_pv,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: self.years}),
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(
            location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
            local_data=disc_techno.local_data,
            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                    # f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                    # f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                    # f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                    # f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                    ],
            outputs=[  # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                # f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',

                # f'{self.name}.{self.model_name}.{GlossaryEnergy.LandUseRequiredValue}'
            ])

    def test_10_nuclear_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'nuclear'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.nuclear.nuclear_disc.NuclearDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = NuclearDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_nuclear,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport_nul,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: self.years}),
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-15,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                                    # f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    # f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}'
                                    ],
                            outputs=[  # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                            ], )

    def test_11_biogas_fired_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'biogas_fired'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.gas.biogas_fired.biogas_fired_disc.BiogasFiredDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = BiogasFiredDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes_nul,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_ccgast,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                                    # f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    # f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[  # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                            ], )

    def test_12_biomass_fired_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'biomass_fired'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.biomass_fired.biomass_fired_disc.BiomassFiredDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = BiomassFiredDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
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
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                                    # f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    # f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[  # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                            ], )

    def test_13_oil_gen_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'oil_gen'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.oil_gen.oil_gen_disc.OilGenDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = OilGenDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes_nul,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_oil,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1], axis=1,
                           keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                                    # f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                                    # f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    # f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[  # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                # f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                            ], )

    def test_14_electricity_discipline_jacobian(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_electricity': f'{self.name}',
                   GlossaryEnergy.NS_REFERENCE: f'{self.name}',
                   GlossaryEnergy.NS_FUNCTIONS: f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.electricity_disc.ElectricityDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.energy_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.energy_name].keys():
            if key in [GlossaryEnergy.techno_list, GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.YearStart,
                       GlossaryEnergy.YearEnd,
                       'scaling_factor_energy_production', 'scaling_factor_energy_consumption',
                       'scaling_factor_techno_consumption', 'scaling_factor_techno_production', ]:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.energy_name}.{key}'] = mda_data_input_dict[self.energy_name][key][
                    'value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.energy_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.energy_name].keys():
            if mda_data_output_dict[self.energy_name][key]['is_coupling']:
                coupled_outputs += [f'{namespace}.{self.energy_name}.{key}']

        technos = inputs_dict[f"{self.name}.technologies_list"]
        techno_capital = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.Capital: 20000,
        })
        for techno in technos:
            inputs_dict[
                f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalValue}"] = techno_capital
            coupled_inputs.append(f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalValue}")

        coupled_outputs.append(f"{self.name}.{self.energy_name}.{GlossaryEnergy.EnergyTypeCapitalDfValue}")

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.energy_name}')[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs, )


if '__main__' == __name__:
    cls = ElectricityJacobianTestCase()
    cls.setUp()
    # cls.test_01_combined_cycle_gas_turbine_discipline_analytic_grad()
    # cls.test_02_geothermal_discipline_analytic_grad()
    # cls.test_03_hydropower_discipline_analytic_grad()
    # cls.test_04_coal_gen_discipline_analytic_grad()
    # cls.test_05_gas_turbine_discipline_analytic_grad()
    # cls.test_06_wind_on_shore_discipline_analytic_grad()
    # cls.test_07_wind_off_shore_discipline_analytic_grad()
    # cls.test_08_solar_thermal_discipline_analytic_grad()
    # cls.test_09_solar_pv_discipline_analytic_grad()
    # cls.test_10_nuclear_discipline_analytic_grad()
    # cls.test_11_biogas_fired_discipline_analytic_grad()
    # cls.test_12_biomass_fired_discipline_analytic_grad()
    # cls.test_13_oil_gen_discipline_analytic_grad()
    cls.test_14_electricity_discipline_jacobian()
