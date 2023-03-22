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

import numpy as np
import pandas as pd
import scipy.interpolate as sc

from sostrades_core.tools.post_processing.post_processing_factory import PostProcessingFactory
from sostrades_core.study_manager.study_manager import StudyManager
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary



class Study(StudyManager):
    def __init__(self, execution_engine=None):
        super().__init__(__file__, execution_engine=execution_engine)

    def setup_usecase(self):
        model_name_Europe = 'Nuclear_Europe'
        model_name_US = 'Nuclear_US'

        values_dict = {}

        years = np.arange(2020, 2051)

        resources_price = pd.DataFrame(
            columns=['years', ResourceGlossary.Water['name'], ResourceGlossary.Uranium['name']])
        resources_price['years'] = years
        resources_price[ResourceGlossary.Water['name']] = 2.0
        resources_price[ResourceGlossary.Uranium['name']] = 1390.0e3
        resources_price[ResourceGlossary.Copper['name']] = 10057.7 * 1000 * 1000 # in $/Mt

        invest_level = pd.DataFrame({'years': years})
        invest_level['invest'] = 10.

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')
        co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})

        margin = pd.DataFrame(
            {'years': np.arange(2020, 2051), 'margin': np.ones(len(np.arange(2020, 2051))) * 110})

        transport = pd.DataFrame(
            {'years': years, 'transport': np.zeros(len(years))})

        energy_prices = pd.DataFrame({'years': years})


        scaling_factor_techno_consumption = 1e3
        scaling_factor_techno_production = 1e3
        resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource', 'copper_resource']
        ratio_available_resource = pd.DataFrame(
            {'years': np.arange(2020, 2050 + 1)})
        for types in resource_list:
            ratio_available_resource[types] = np.linspace(
                0.5, 0.5, len(ratio_available_resource.index))

        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict['years'] = years
        all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        is_stream_demand = True
        is_apply_resource_ratio = True


        inputs_dict = {f'{self.study_name}.year_end': 2050,
                       f'{self.study_name}.energy_prices': energy_prices,
                       f'{self.study_name}.energy_CO2_emissions': pd.DataFrame(),
                       f'{self.study_name}.{model_name_Europe}.invest_level': invest_level,
                       f'{self.study_name}.{model_name_US}.invest_level': invest_level,
                       f'{self.study_name}.CO2_taxes': co2_taxes,
                       f'{self.study_name}.transport_margin': margin,
                       f'{self.study_name}.transport_cost': transport,
                       f'{self.study_name}.resources_price': resources_price,
                       f'{self.study_name}.{model_name_Europe}.margin':  margin,
                       f'{self.study_name}.{model_name_US}.margin':  margin}

        values_dict.update(inputs_dict)
        return [values_dict]


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()
    ppf = PostProcessingFactory()
    for disc in uc_cls.execution_engine.root_process.proxy_disciplines:
        filters = ppf.get_post_processing_filters_by_discipline(
            disc)
        graph_list = ppf.get_post_processing_by_discipline(
            disc, filters, as_json=False)
        if disc.sos_name == 'EnergyMix.electricity.OilGen': #Nuclear  OilGen
            for graph in graph_list:
                graph.to_plotly()#.show()
