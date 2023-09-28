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

from energy_models.core.stream_type.energy_disc import EnergyDiscipline
from energy_models.core.stream_type.energy_models.wet_biomass import WetBiomass
from climateeconomics.glossarycore import GlossaryCore


class BiomassWetDiscipline(EnergyDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Wet Biomass Model',
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

    DESC_IN = {'technologies_list': {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': ['WetCropResidues', 'AnimalManure'],
                                     'namespace': 'ns_wet_biomass',
                                     'structuring': True,
                                     'unit': '-'},
               'data_fuel_dict': {'type': 'dict',
                                  'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_wet_biomass',
                                  'default': WetBiomass.data_energy_dict,
                                  'unit': 'defined in dict'},
               }
    DESC_IN.update(EnergyDiscipline.DESC_IN)

    energy_name = WetBiomass.name

    DESC_OUT = EnergyDiscipline.DESC_OUT  # -- add specific techno outputs to this

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = WetBiomass(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def run(self):
        EnergyDiscipline.run(self)

        # -- get inputs
        inputs_dict = self.get_sosdisc_inputs()
        # -- instantiate specific class

        # -- compute informations
        cost_details, production, consumption, techno_mix = self.energy_model.compute()

        outputs_dict = {'energy_prices': cost_details,
                        'energy_consumption': consumption / inputs_dict['scaling_factor_energy_consumption'],
                        GlossaryCore.EnergyProductionValue: production / inputs_dict[
                            'scaling_factor_energy_production'],
                        'techno_mix': techno_mix}
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)
