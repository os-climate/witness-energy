'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.techno_type.disciplines.biodiesel_techno_disc import (
    BioDieselTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.biodiesel.transesterification.transesterification import (
    Transesterification,
)


class TransesterificationDiscipline(BioDieselTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Transesterification Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-gas-pump fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    techno_name = GlossaryEnergy.Transesterification
    energy_name = BioDiesel.name

    # use biodiesel calorific value to compute co2 from production

    # Beer, T., Grant, T., Morgan, G., Lapszewicz, J., Anyon, P., Edwards, J., Nelson, P., Watson, H. and Williams, D., 2001.
    # Comparison of transport fuels. FINAL REPORT (EV45A/2/F3C) to the Australian Greenhouse Office on the stage, 2.
    # Pre-combustion CO2 emissions for soybean = 0.03 kgCO2/MJ * 3.6 MJ/kWh =
    # 0.11 kgCO2/kWh
    co2_from_production = (6.7 / 1000) * BioDiesel.data_energy_dict['calorific_value']
    techno_infos_dict_default = {'Opex_percentage': 0.04,
                                 'Capex_init': 22359405 / 40798942,  # Capex initial at year 2020
                                 'Capex_init_unit': '$/kg',
                                 'efficiency': 0.99,
                                 'CO2_from_production': co2_from_production,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'maturity': 5,
                                 'learning_rate': 0.1,
                                 'full_load_hours': 7920.0,
                                 'WACC': 0.0878,
                                     'techno_evo_eff': 'no',
                                 }
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               }
    DESC_IN.update(BioDieselTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = BioDieselTechnoDiscipline.DESC_OUT

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.dprices_demissions = None
        self.grad_total = None

    def init_execution(self):
        self.model = Transesterification(self.techno_name)

    def setup_sos_disciplines(self):
        '''
        Compute techno_infos_dict with updated data_fuel_dict
        '''
        super().setup_sos_disciplines()
        dynamic_inputs = self.get_inst_desc_in()
        if self.get_data_in() is not None:
            if 'data_fuel_dict' in self.get_data_in():
                biodiesel_calorific_value = self.get_sosdisc_inputs('data_fuel_dict')[
                    'calorific_value']
                biodiesel_density = self.get_sosdisc_inputs('data_fuel_dict')[
                    'density']

                # Source for initial production: IEA 2022, Renewables 2021, https://www.iea.org/reports/renewables-2021, License: CC BY 4.0.
                # 43 billion liters from IEA in 2020
                initial_production = 37 * biodiesel_density / 1000 * biodiesel_calorific_value

                dynamic_inputs['techno_infos_dict'] = {
                    'type': 'dict', 'default': self.techno_infos_dict_default, 'unit': 'defined in dict'}
                dynamic_inputs['initial_production'] = {
                    'type': 'float', 'unit': 'TWh', 'default': initial_production}
        self.add_inputs(dynamic_inputs)

