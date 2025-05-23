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

import json
import unittest
from os.path import dirname, join

import numpy as np
import pandas as pd
from climateeconomics.core.core_resources.resource_mix.resource_mix import (
    ResourceMixModel,
)
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy


class NuclearTestCase(unittest.TestCase):
    """
    Nuclear prices test class
    """

    def setUp(self):
        
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)

        self.resources_price = pd.DataFrame(
            columns=[GlossaryEnergy.Years, GlossaryEnergy.WaterResource, GlossaryEnergy.UraniumResource])
        self.resources_price[GlossaryEnergy.Years] = years
        self.resources_price[GlossaryEnergy.WaterResource] = 2.0
        self.resources_price[GlossaryEnergy.UraniumResource] = 1390.0e3
        self.resources_price[GlossaryEnergy.CopperResource] = 10057.7 * 1000 * 1000  # in $/Mt

        self.invest_level = pd.DataFrame({GlossaryEnergy.Years: years})
        self.invest_level[GlossaryEnergy.InvestValue] = 10.

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})

        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1),
             GlossaryEnergy.MarginValue: np.ones(len(np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1))) * 200})

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.zeros(len(years))})

        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: years.tolist()})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == f'{GlossaryEnergy.electricity}.{GlossaryEnergy.Nuclear}']
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource', 'copper_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                0.5, 0.5, len(self.ratio_available_resource.index))

        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def test_01_nuclear_discipline(self):
        # TODO: test commented out bc needs to be updated with new database connector def
        self.name = 'Test'
        self.model_name = 'Nuclear_Europe'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   GlossaryEnergy.NS_WITNESS: f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   
                   'ns_electricity': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)
        ns_dict_bis = {'ns_electricity_nuc': f'{self.name}.{self.model_name}'}
        ns_id = self.ee.ns_manager.add_ns_def(ns_dict_bis, database_name='Europe')  # pylint: disable=E1123
        file_path = join(dirname(__file__), 'data_tests', 'data_nuclear_test.json')
        self.ee.ns_manager.set_ns_database_location(file_path)
        mod_path = 'energy_models.models.electricity.nuclear_modified.nuclear_disc.NuclearDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)
        builder.associate_namespaces(ns_id)
        model_name_US = 'Nuclear_US'
        builder_us = self.ee.factory.get_builder_from_module(
            model_name_US, mod_path)
        ns_id = self.ee.ns_manager.add_ns_def({'ns_electricity_nuc': f'{self.name}.{model_name_US}'},)  # pylint: disable=E1123
        builder_us.associate_namespaces(ns_id)
        self.ee.factory.set_builders_to_coupling_builder([builder, builder_us])

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsGHGEmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: self.years}),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{model_name_US}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,

                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{model_name_US}.{GlossaryEnergy.MarginValue}': self.margin}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_europe = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]

        disc_us = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{model_name_US}')[0]

        # we have associated only ns_electricity_nuc to the database. It means that only values of variables in this namespace will be loaded from the json file
        with open(file_path, "r") as f:
            json_data = f.read()

        data_dict_json = convert_from_editable_json(json_data)
        data_ref_europe = data_dict_json['Europe']
        data_ref_us = data_dict_json['US']

        # check techno_infos_dict maturity is equal to the json value
        self.assertEqual(data_ref_europe['techno_infos_dict']['maturity'],
                         disc_europe.get_sosdisc_inputs('techno_infos_dict')['maturity'])
        self.assertEqual(data_ref_us['techno_infos_dict']['maturity'],
                         disc_us.get_sosdisc_inputs('techno_infos_dict')['maturity'])

        # check that for a variable not in ns_electricity_nuc, the used value is the one given in the test not in the json. We test it on transport_margin variable
        self.assertNotEqual(data_ref_europe[GlossaryEnergy.TransportMarginValue][GlossaryEnergy.MarginValue].max(),
                            disc_europe.get_sosdisc_inputs(GlossaryEnergy.TransportMarginValue)[
                                GlossaryEnergy.MarginValue].max())
        self.assertNotEqual(data_ref_us[GlossaryEnergy.TransportMarginValue][GlossaryEnergy.MarginValue].max(),
                            disc_us.get_sosdisc_inputs(GlossaryEnergy.TransportMarginValue)[
                                GlossaryEnergy.MarginValue].max())


def convert_to_editable_json(data):
    def convert(obj):

        if isinstance(obj, pd.DataFrame):
            df = obj.apply(lambda x: x.astype(int) if x.dtype == np.int32 else x)
            df = df.where(pd.notnull(df), None)
            return [{col: df[col].values.tolist()} for col in df.columns]
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(elem) for elem in obj]
        elif isinstance(obj, float):
            return obj  # Round to 2 decimal places
        elif isinstance(obj, np.int32):
            return int(obj)
        else:
            return obj

    data = convert(data)
    return json.dumps(data, ensure_ascii=False)


def convert_from_editable_json(json_str):
    def convert(obj):
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            if len(obj) > 0 and isinstance(obj[0], dict):
                df = pd.DataFrame({k: v for d in obj for k, v in d.items()})
                # df = df.apply(lambda x: pd.to_numeric(x, errors='ignore') if x.dtype == np.object else x)
                return df
            else:
                return [convert(elem) for elem in obj]
        elif isinstance(obj, str):
            try:
                return int(obj)
            except ValueError:
                pass
            try:
                return float(obj)
            except ValueError:
                pass
            return obj
        else:
            return obj

    data = json.loads(json_str)
    return convert(data)


if __name__ == "__main__":
    cls = NuclearTestCase()
    cls.setUp()
    # cls.launch_data_pickle_generation()
    cls.test_01_nuclear_discipline()
