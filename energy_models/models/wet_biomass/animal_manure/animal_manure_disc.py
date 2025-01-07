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


from energy_models.core.techno_type.disciplines.wet_biomass_techno_disc import (
    WetBiomassTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.wet_biomass.animal_manure.animal_manure import AnimalManure


class AnimalManureDiscipline(WetBiomassTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Animal Manure Biomass Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': '',
        'version': '',
    }

    # wood residues comes from forestry residues
    # prices come from harvest, transport, chipping, drying (depending from
    # where it comes)

    techno_name = GlossaryEnergy.AnimalManure

    techno_infos_dict_default = {'maturity': 5,
                                 'moisture': 0.85,

                                 # To be defined, but is nearly 0
                                 'Opex_percentage': 0.36,
                                 # 1 tonne of tree absorbs 1.8t of CO2 in one
                                 # year
                                 'CO2_from_production': -2.86,  # same as biomass_dry
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 0,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'WACC': 0.07,  # ?
                                 'learning_rate': 0.2,  # augmentation of forests ha per year?
                                 # To be defined, should be nearly 0
                                 'Capex_init': 59.48,
                                 'Capex_init_unit': 'euro/ha',
                                 'full_load_hours': 8760.0,
                                 'euro_dollar': 1.2195,  # in 2021, date of the paper
                                 # WBA-World Bioenergy Association, 2021. Global bioenergy statistics.
                                 # To be defined
                                 'available_power': 0,  # average, worldbioenergy.org
                                 'available_power_unit': 'kg',
                                 'efficiency': 0.0,
                                 'techno_evo_eff': 'no',  # yes or no

                                 }
    # invest: 7% of ha are planted each year at 13047.328euro/ha
        # To be defined
    initial_production = 1e-12  # in Twh
    # to be defined
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},

               }
    # -- add specific techno inputs to this
    DESC_IN.update(WetBiomassTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = WetBiomassTechnoDiscipline.DESC_OUT

    def init_execution(self):
        self.techno_model = AnimalManure(self.techno_name)
