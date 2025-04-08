'''
Copyright 2024 Capgemini
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
from energy_models.core.stream_type.energy_models.clean_energy import CleanEnergy
from energy_models.core.techno_type.techno_disc import TechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy


class CleanEnergyTechnoDiscipline(TechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Clean Energy Technologies Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-fan fa-fw',
        'version': '',
    }
    DESC_IN = {GlossaryEnergy.TransportCostValue: {'type': 'dataframe', 'unit': '$/MWh',
                                                   'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                   'namespace': 'ns_clean_energy',
                                                   'dataframe_descriptor': {GlossaryEnergy.Years: (
                                                   'int', [1900, GlossaryEnergy.YearEndDefaultCore], False),
                                                                            'transport': ('float', None, True)},
                                                   'dataframe_edition_locked': False},
               GlossaryEnergy.TransportMarginValue: {'type': 'dataframe', 'unit': '%',
                                                     'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                     'namespace': 'ns_clean_energy',
                                                     'dataframe_descriptor': {GlossaryEnergy.Years: (
                                                     'int', [1900, GlossaryEnergy.YearEndDefaultCore], False),
                                                                              GlossaryEnergy.MarginValue: (
                                                                              'float', None, True)},
                                                     'dataframe_edition_locked': False},
               'data_fuel_dict': {'type': 'dict',
                                  'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_clean_energy',
                                  'default': CleanEnergy.data_energy_dict,
                                  'unit': 'defined in dict'},
               }
    DESC_IN.update(TechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    energy_name = CleanEnergy.name

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        TechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_stream_price()

        carbon_emissions = self.get_sosdisc_outputs(GlossaryEnergy.CO2EmissionsValue)

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions)
