'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/24 Copyright 2023 Capgemini

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
from os.path import dirname, join

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy


class WindOnshoreTestCase(unittest.TestCase):
    """
    WindOnshore prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: np.linspace(22., 31., len(self.years))})

        
        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})

        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1),
             GlossaryEnergy.MarginValue: np.ones(
                 len(np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1))) * 110})

        transport_cost = 11
        # It is noteworthy that the cost of transmission has generally been held (and can
        # continue to be held)	within the £10-12/MWhr range despite transmission distances
        # increasing by almost an order of magnitude from an average of 20km for the
        # leftmost bar to 170km for the 2020 scenarios / OWPB 2016

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': transport_cost})

        self.resources_price = pd.DataFrame({GlossaryEnergy.Years: self.years})

        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == f'{GlossaryEnergy.electricity}.Wind_Onshore']
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(self.years), len(self.years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_03_wind_on_shore_discipline(self):
        self.name = 'Test'
        self.model_name = 'Wind_Electricity'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.wind_onshore.wind_onshore_disc.WindOnshoreDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: self.years}),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]

        production_detailed = disc.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedProductionValue)
        power_production = disc.get_sosdisc_outputs(GlossaryEnergy.InstalledCapacity)
        techno_infos_dict = disc.get_sosdisc_inputs('techno_infos_dict')

        drop_pickle = False
        if drop_pickle:
            import pickle
            with open('windtest.pkl','wb') as f:
                pickle.dump(self.ee.dm.get_data_dict_values(), f)
                pass
        import pickle
        with open('windtest.pkl' ,'rb') as f:
            pickle_dev = pickle.load(f)

        cur_dm = self.ee.dm.get_data_dict_values()

        commun_keys = set(cur_dm.keys()).intersection(set(pickle_dev.keys()))
        for key in commun_keys:
            curren_value = cur_dm[key]
            if isinstance(curren_value, pd.DataFrame):
                for col in curren_value.columns:
                    if col != GlossaryEnergy.Years:
                        curren_col = curren_value[col].values
                        if col in pickle_dev[key].columns:
                            before_col = pickle_dev[key][col].values
                            if curren_col.shape == before_col.shape:
                                try:
                                    mean_ratio  = (before_col / curren_col).mean()
                                    if abs(mean_ratio - 1) > 0.02:
                                        print(key, col, mean_ratio)
                                except Exception as e:
                                    #print(key, col , e)
                                    pass
                        else:
                            #print("missing col", key, col)
                            a = 1

        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        for graph in graph_list:
            #graph.to_plotly().show()
            pass
        self.assertLessEqual(list(production_detailed[f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})'].values),
                             list(power_production['total_installed_capacity'] * techno_infos_dict[
                                 'full_load_hours'] / 1000 * 1.001))
        self.assertGreaterEqual(list(production_detailed[f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})'].values),
                                list(power_production['total_installed_capacity'] * techno_infos_dict[
                                    'full_load_hours'] / 1000 * 0.999))
# if __name__ == "__main__":
#     unittest.main()
