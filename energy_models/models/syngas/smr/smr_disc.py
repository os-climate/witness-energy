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


from energy_models.core.techno_type.disciplines.syngas_techno_disc import (
    SyngasTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.syngas.smr.smr import SMR


class SMRDiscipline(SyngasTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Syngas SMR Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-burn fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    DESC_IN = SyngasTechnoDiscipline.DESC_IN
    techno_name = GlossaryEnergy.SMR

    techno_infos_dict_default = {'reaction': 'H20 + CH4 = 3H2 + CO',
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 0.23,
                                 'elec_demand_unit': 'kWh/kg',
                                 'Opex_percentage': 0.05,
                                 'high_heat_production': (206 / (
                                             28.01 + 3 * 2.016)) * 1000 * 2.77778e-13 / 33.33 * 1e-9,
                                 # CH4 + H2O → CO + 3H2  ΔH°= 206 kJ/mol
                                 # Total power demand of 0.1 kWh/kg H2
                                 # hydrogen 33.33 * 1e-9 TWh/kg
                                 # https://www.sciencedirect.com/science/article/pii/S2666790822001574
                                 'high_heat_production_unit': 'TWh/TWh',
                                 # Diglio, G., Hanak, D.P., Bareschino, P., Mancusi, E., Pepe, F., Montagnaro, F. and Manovic, V., 2017.
                                 # Techno-economic analysis of sorption-enhanced steam methane reforming in a fixed bed reactor network integrated with fuel cell.
                                 # Journal of Power Sources, 364, pp.41-51.
                                 'Capex_init': 450,
                                 'Capex_init_unit': '$/kW',
                                 'efficiency': 0.8,
                                 'maturity': 5,
                                 'learning_rate': 0.0,  # 0.2,
                                 'euro_dollar': 1.114,
                                 'full_load_hours': 8000.0,
                                 'WACC': 0.0878,
                                     'techno_evo_eff': 'no',  # in kWh/kg
                                 }

    syngas_ratio = SMR.syngas_COH2_ratio

        # From Future of hydrogen : accounting for around three quarters of the
    # annual global dedicated hydrogen production of around 70 million tonnes.
    # 70 MT of hydrogen then 70*33.3 TWh of hydrogen we need approximately
    # 1.639 kWh of syngas to produce one of hydrogen (see WGS results)

    # syngas is also used for FT process :
    # 140000+34000 BPD in Qatar GtL
    # 12000 BPD in Malaysia GtL
    # BPD to TWh per year = 1700/1e9*365
    initial_production = 70.0 * 33.3 * 1.639 * 0.75 + \
                         (140000 + 34000 + 12000) * 1700 / 1e9 * 365
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
    }

    DESC_IN.update(SyngasTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this

    def init_execution(self):
        self.model = SMR(self.techno_name)

