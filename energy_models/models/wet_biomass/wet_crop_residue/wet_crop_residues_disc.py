'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/03/27 Copyright 2023 Capgemini

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
from energy_models.models.wet_biomass.wet_crop_residue.wet_crop_residues import (
    WetCropResidues,
)


class WetCropResiduesDiscipline(WetBiomassTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Wet Crop Residues Biomass Model',
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

    techno_name = GlossaryEnergy.WetCropResidues

    techno_infos_dict_default = {'maturity': 5,
                                 'crop_residues_moisture': 0.50,
                                 'crop_residue_colorific_value': 3.15,  # irena

                                 # computed 87.7euro/ha, counting harvest,
                                 # fertilizing, drying...from gov.mb.ca
                                 'Opex_percentage': 0.36,
                                 # 1 tonne of tree absorbs 1.8t of CO2 in one
                                 # year
                                 'CO2_from_production': -2.86,  # same as biomass_dry
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 0,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'WACC': 0.07,  # ?
                                 'learning_rate': 0.2,  # augmentation of forests ha per year?
                                 # capex from gov.mb.ca/agriculture/farm-management/production-economics/pubs/cop-crop-production.pdf
                                 # 25% of 237.95 euro/ha (717 $/acre)
                                 # 1USD = 0,82 euro in 2021
                                 'Capex_init': 59.48,
                                 'Capex_init_unit': 'euro/ha',
                                 'full_load_hours': 8760.0,
                                 'euro_dollar': 1.2195,
                                 # WBA World Bioenergy Association, 2021. Global bioenergy statistics.
                                 # available land in 2017:
                                 # (worldbioenergy.org), 93% is dry biomass
                                 'available_land': 4828000000 * 0.07,
                                 'available_land_unit': 'ha',

                                 # kg of residue for 1ha of crops, 25% of
                                 # residue (mdpi)
                                 'density_per_ha': 1522.4,  # average, worldbioenergy.org
                                 'density_per_ha_unit': 'kg/ha',
                                 'efficiency': 0.0,
                                 'techno_evo_eff': 'no',  # yes or no

                                 }
    # To be defined
        # 7% of available power is the amount of crop residue in 2017
    # (worldbioenergy.org)
    initial_production = 4.828 * 0.07 * 1522.4 * 3.36  # in Twh
    # Age distribution fake
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
                      
               }
    # -- add specific techno inputs to this
    DESC_IN.update(WetBiomassTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = WetBiomassTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = WetCropResidues(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
