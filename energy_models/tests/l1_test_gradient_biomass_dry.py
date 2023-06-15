'''
Copyright 2022 Airbus SAS

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

import pandas as pd
import numpy as np
import scipy.interpolate as sc
from os.path import join, basename, dirname
import pickle

from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions,\
    get_static_prices
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.energy_mix.energy_mix import EnergyMix


class BiomassDryJacobianTestCase(AbstractJacobianUnittest):
    """
    Biomass Dry jacobian test class
    """
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_crop_energy_discipline_analytic_grad,
            self.test_02_managed_wood_discipline_analytic_grad,
            self.test_03_unmanaged_wood_discipline_analytic_grad,
            self.test_04_biomass_dry_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'biomass_dry'

        electricity_price = np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                      0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                      0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                      0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                      0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                      0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                      0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                      0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                      0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                      0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                      0.0928246539459331]) * 1.5 * 1000.0
        self.years = np.arange(2020, 2051)

        self.energy_prices = pd.DataFrame(
            {'years': self.years, 'electricity': electricity_price})

        self.energy_carbon_emissions = pd.DataFrame(
            {'years': self.years, 'electricity': 0.0})
        # invest: 1Mha of crop land each year

        self.invest_level_managed_wood = pd.DataFrame(
            {'years': self.years, 'invest': np.array([1135081003.0 * 0.28, 1135081003.0 * 0.28, 1135081003.0 * 0.28,
                                                      1135081003.0 * 0.28, 1135081003.0 * 0.28, 1135081003.0 * 0.28,
                                                      1135081003.0 * 0.28, 1135081003.0 * 0.28, 1135081003.0 * 0.28,
                                                      1135081003.0 * 0.28, 1135081003.0 * 0.28, 1135081003.0 * 0.28,
                                                      1135081003.0 * 0.28, 1135081003.0 * 0.28, 1135081003.0 * 0.28,
                                                      1135081003.0 * 0.28, 1135081003.0 * 0.28, 1135081003.0 * 0.28,
                                                      1135081003.0 * 0.28, 1135081003.0 * 0.28, 1135081003.0 * 0.28,
                                                      1135081003.0 * 0.28, 1135081003.0 * 0.28, 1135081003.0 * 0.28,
                                                      1135081003.0 * 0.28, 1135081003.0 * 0.28, 1135081003.0 * 0.28,
                                                      1135081003.0 * 0.28, 1135081003.0 * 0.28, 1135081003.0 * 0.28,
                                                      1135081003.0 * 0.28]) * 1.0e-9})

        self.invest_level = pd.DataFrame(
            {'years': self.years, 'invest': np.linspace(0, 10, len(self.years))})

        self.land_surface_for_food = pd.DataFrame({'years': self.years,
                                                   'Agriculture total (Gha)': np.ones(len(self.years)) * 4.8})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': self.years, 'CO2_tax': func(self.years)})
        self.margin = pd.DataFrame(
            {'years': self.years, 'margin': np.ones(len(self.years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {'years': self.years, 'transport': np.ones(len(self.years)) * 0.1})
        #---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(self.years))))
        demand_ratio_dict['years'] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(1.0, 1.0, len(self.years))))
        resource_ratio_dict['years'] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_crop_energy_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'crop_energy'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_biomass_dry': f'{self.name}',
                   'ns_witness': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.biomass_dry.crop_energy.crop_energy_disc.CropEnergyDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.land_surface_for_food_df': self.land_surface_for_food,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)


        self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl', local_data = disc_techno.local_data,
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level', f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.land_surface_for_food_df',
                                    f'{self.name}.CO2_taxes'
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     f'{self.name}.{self.model_name}.land_use_required',
                                     f'{self.name}.{self.model_name}.techno_capital',
                                     f'{self.name}.{self.model_name}.non_use_capital'],)

    def test_02_managed_wood_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'managed_wood'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_biomass_dry': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.biomass_dry.managed_wood.managed_wood_disc.ManagedWoodDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.invest_level', f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions', f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     f'{self.name}.{self.model_name}.land_use_required'],)

    def test_03_unmanaged_wood_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'unmanaged_wood'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_biomass_dry': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.biomass_dry.unmanaged_wood.unmanaged_wood_disc.UnmanagedWoodDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        np.set_printoptions(threshold=np.inf)

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data = disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions', f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     f'{self.name}.{self.model_name}.land_use_required'])

    def test_04_biomass_dry_discipline_jacobian(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_biomass_dry': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.biomass_dry_disc.BiomassDryDiscipline'
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
            if key in ['technologies_list', 'CO2_taxes', 'year_start', 'year_end',
                       'scaling_factor_energy_production', 'scaling_factor_energy_consumption',
                       'scaling_factor_techno_consumption', 'scaling_factor_techno_production']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.energy_name}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
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

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.energy_name}')[0].mdo_discipline_wrapp.mdo_discipline
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)


if '__main__' == __name__:
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = BiomassDryJacobianTestCase()
    cls.setUp()
    cls.test_01_crop_energy_discipline_analytic_grad()
