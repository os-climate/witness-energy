'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/06/24 Copyright 2023 Capgemini

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
import logging

import numpy as np
import pandas as pd
from climateeconomics.core.core_witness.climateeco_discipline import (
    ClimateEcoDiscipline,
)
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_optimization_plugins.models.autodifferentiated_discipline import (
    AutodifferentiedDisc,
)

from energy_models.core.ccus.ccus import CCUS
from energy_models.glossaryenergy import GlossaryEnergy


class CCUS_Discipline(AutodifferentiedDisc):
    # ontology information
    _ontology_data = {
        'label': 'Carbon Capture and Storage Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fa-solid fa-people-carry-box fa-fw',
        'version': '',
    }

    ccs_list = [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]

    DESC_IN = {GlossaryEnergy.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'}, "default": ccs_list, 'structuring': True},
               GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
               GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
               'net_energy_production_details': {'type': 'dataframe', 'unit': 'TWh', 'description': 'net energy production for each energy', AutodifferentiedDisc.GRADIENTS: True},
           }

    DESC_OUT = {
        GlossaryEnergy.CCUS_CO2EmissionsDfValue: GlossaryEnergy.CCUS_CO2EmissionsDf,
        GlossaryEnergy.CCUS_CarbonStorageCapacityValue: GlossaryEnergy.CCUS_CarbonStorageCapacity,
        GlossaryEnergy.CCUSPriceValue: GlossaryEnergy.CCUSPrice
    }

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.model = None

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.model = CCUS(GlossaryEnergy.ccus_type)
        self.model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        for ccs_name in self.ccs_list:
            dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.StreamEnergyConsumptionValue}'] = {
                'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                'namespace': GlossaryEnergy.NS_CCS,
                "dynamic_dataframe_columns": True}
            dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.StreamEnergyDemandValue}'] = {
                'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                'namespace': GlossaryEnergy.NS_CCS,
                "dynamic_dataframe_columns": True}
            dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.StreamProductionValue}'] = {
                'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                'namespace': GlossaryEnergy.NS_CCS,
                'dynamic_dataframe_columns': True}
            dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyPricesValue}'] = {
                'type': 'dataframe', 'unit': '$/MWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                'namespace': GlossaryEnergy.NS_CCS,
                'dynamic_dataframe_columns': True}
            dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.LandUseRequiredValue}'] = {
                'type': 'dataframe', 'unit': 'Gha', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                'namespace': GlossaryEnergy.NS_CCS,
                "dynamic_dataframe_columns": True}

        self.update_default_values()
        self.add_inputs(dynamic_inputs),
        self.add_outputs(dynamic_outputs)

    def update_default_values(self):
        """
        Update all default dataframes with years
        """
        if self.get_data_in() is not None:
            if GlossaryEnergy.YearEnd in self.get_data_in() and GlossaryEnergy.YearStart in self.get_data_in() and 'co2_for_food' in self.get_data_in():
                year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
                if year_start is not None and year_end is not None:
                    default_co2_for_food = pd.DataFrame({
                        GlossaryEnergy.Years: np.arange(year_start, year_end + 1),
                        f'{GlossaryEnergy.carbon_capture} for food (Mt)': 0.0})
                    self.update_default_value('co2_for_food', 'in', default_co2_for_food)

    def run(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.model.configure_parameters(inputs_dict)
        self.model.compute()
        self.store_sos_outputs_values(self.model.outputs_dict)

