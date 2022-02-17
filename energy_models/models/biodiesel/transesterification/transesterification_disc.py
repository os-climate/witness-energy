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
from energy_models.core.techno_type.disciplines.biodiesel_techno_disc import BioDieselTechnoDiscipline
from energy_models.models.biodiesel.transesterification.transesterification import Transesterification


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
    techno_name = 'Transesterification'
    energy_name = 'biodiesel'
    lifetime = 15
    construction_delay = 3  # years

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [0.0, 4.085787594423131, 11.083221775965836, 9.906291833479699,
                                                         11.264502455357881, 15.372601517593951, 10.940986166952394,
                                                         6.682284695273031, 3.1012940652355083, 7.711401160086531,
                                                         5.848393573822739, 2.2088353407762535, 3.162650601721087,
                                                         8.631749219311956]})  # to review

    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [4.0, 3.0, 2.0]})
    DESC_IN = {'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    DESC_IN.update(BioDieselTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = BioDieselTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Transesterification(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):
        '''
        Compute techno_infos_dict with updated data_fuel_dict
        '''
        BioDieselTechnoDiscipline.setup_sos_disciplines(self)
        dynamic_inputs = self.inst_desc_in
        if self._data_in is not None:
            if 'data_fuel_dict' in self._data_in:
                biodiesel_calorific_value = self.get_sosdisc_inputs('data_fuel_dict')[
                    'calorific_value']
                biodiesel_density = self.get_sosdisc_inputs('data_fuel_dict')[
                    'density']

                # Beer, T., Grant, T., Morgan, G., Lapszewicz, J., Anyon, P., Edwards, J., Nelson, P., Watson, H. and Williams, D., 2001.
                # Comparison of transport fuels. FINAL REPORT (EV45A/2/F3C) to the Australian Greenhouse Office on the stage, 2.
                # Pre-combustion CO2 emissions for soybean = 0.03 kgCO2/MJ * 3.6 MJ/kWh =
                # 0.11 kgCO2/kWh
                co2_from_production = (6.7 / 1000) * biodiesel_calorific_value
                techno_infos_dict_default = {'Opex_percentage': 0.04,
                                             'lifetime': self.lifetime,  # for now constant in time but should increase with time
                                             'lifetime_unit': 'years',
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

                                             'construction_delay': self.construction_delay
                                             }

                # IEA (2021), Renewables 2021, IEA, Paris https://www.iea.org/reports/renewables-2021
                # 43 billion liters from IEA in 2020
                initial_production = 37 * biodiesel_density / 1000 * biodiesel_calorific_value

                dynamic_inputs['techno_infos_dict'] = {
                    'type': 'dict', 'default': techno_infos_dict_default}
                dynamic_inputs['initial_production'] = {
                    'type': 'float', 'unit': 'TWh', 'default': initial_production}
        self.add_inputs(dynamic_inputs)

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        BioDieselTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()

        carbon_emissions = self.get_sosdisc_outputs('CO2_emissions')

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions)
