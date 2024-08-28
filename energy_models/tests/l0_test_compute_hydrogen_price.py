'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/23-2024/06/24 Copyright 2023 Capgemini

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

from energy_models.glossaryenergy import GlossaryEnergy


class HydrogenPriceTestCase(unittest.TestCase):
    """
    Hydrogen prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.electrolysis_techno_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years,
             GlossaryEnergy.ElectrolysisPEM: 90.,
             f'{GlossaryEnergy.ElectrolysisPEM}_wotaxes': 90.})

        self.smr_techno_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years,
                GlossaryEnergy.WaterGasShift: 63.,
             f"{GlossaryEnergy.WaterGasShift}_wotaxes": 60.
             })

        self.plasmacracking_techno_prices = pd.DataFrame({
            GlossaryEnergy.Years: years,
            GlossaryEnergy.PlasmaCracking:63.,
            'PlasmaCracking_wotaxes': 54.
        })

        self.smr_consumption = pd.DataFrame({GlossaryEnergy.Years: years,
                                             f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': 2896311508,
                                             f'{GlossaryEnergy.methane} ({GlossaryEnergy.energy_unit})': 13033401786.43378,
                                             'water (Mt)': 4115502095,
                                             })

        self.smr_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                            f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})":0.,
                                            f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': 14481557540,
                                            'CO2 (Mt)': 1452504570,})

        self.plasmacracking_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                                       f"{GlossaryEnergy.SolidCarbon} ({GlossaryEnergy.mass_unit})": 0.,
                                                       f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': 1097111725247,
                                                       'C (Mt)': 84232562661})

        self.plasmacracking_consumption = pd.DataFrame({GlossaryEnergy.Years: years,
                                                        f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': 231813581540,
                                                        f'{GlossaryEnergy.methane} ({GlossaryEnergy.energy_unit})': 1715281276020})

        self.electrolysis_consumption = pd.DataFrame({GlossaryEnergy.Years: years,
                                                      f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': 2896311508,
                                                      'water (Mt)': 4115502095})

        self.electrolysis_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                                     f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': 14481557540,
                                                     'O2 (Mt)': 1452504570})

        self.techno_capital = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.Capital: 0.0, GlossaryEnergy.NonUseCapital: 0.})

        self.electrolysis_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.ElectrolysisPEM: 0.0})

        self.plasma_cracking_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.PlasmaCracking: 0.013})
        self.smr_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.WaterGasShift: 0.1721})

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})

        self.land_use_required_WaterGasShift = pd.DataFrame(
            {GlossaryEnergy.Years: years, f'{GlossaryEnergy.WaterGasShift} ({GlossaryEnergy.surface_unit})': 0.0})
        self.land_use_required_Electrolysis = pd.DataFrame(
            {GlossaryEnergy.Years: years, f'{GlossaryEnergy.ElectrolysisPEM} (Gha)': 0.0})
        self.land_use_required_PlasmaCracking = pd.DataFrame(
            {GlossaryEnergy.Years: years, f'{GlossaryEnergy.PlasmaCracking} ({GlossaryEnergy.surface_unit})': 0.0})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

    def tearDown(self):
        pass

    def test_01_hydrogen_discipline(self):
        self.name = 'Test'
        self.model_name = f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_energy': f'{self.name}',
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.gaseous_hydrogen_disc.GaseousHydrogenDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': GlossaryEnergy.YearStartDefault,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.techno_list}': [GlossaryEnergy.WaterGasShift, GlossaryEnergy.ElectrolysisPEM,
                                                                     GlossaryEnergy.PlasmaCracking],
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoConsumptionValue}': self.smr_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.smr_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoProductionValue}': self.smr_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoPricesValue}': self.smr_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.CO2EmissionsValue}': self.smr_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_WaterGasShift,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoConsumptionValue}': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoProductionValue}': self.electrolysis_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoPricesValue}': self.electrolysis_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.CO2EmissionsValue}': self.electrolysis_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_Electrolysis,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoConsumptionValue}': self.plasmacracking_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoCapitalValue}': self.techno_capital,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoCapitalValue}': self.techno_capital,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoCapitalValue}': self.techno_capital,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.plasmacracking_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoProductionValue}': self.plasmacracking_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoPricesValue}': self.plasmacracking_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.CO2EmissionsValue}': self.plasma_cracking_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_PlasmaCracking}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()
